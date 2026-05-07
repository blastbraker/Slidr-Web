"""Slider-Web - AI Presentation Maker - Streamlit Web App"""

import streamlit as st
import json
import os
from io import BytesIO
from openai import OpenAI

st.set_page_config(
    page_title="Slider-Web",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


SLIDE_TYPES = {
    "title": "Title Slide - Big title with subtitle",
    "content": "Content - Title and bullet points",
    "bullets_image": "Bullets + Image - Left bullets, right image",
    "two_column": "Two Column - Two content columns",
    "divider": "Divider - Section transition",
    "quote": "Quote - Big quote with author citation",
    "statistic": "Statistic - Large number with label",
    "comparison": "Comparison - Pros vs cons",
    "timeline": "Timeline - Chronological events",
    "full_image": "Full Image - Hero image with caption",
}


def get_ai_client():
    """Get Groq AI client"""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except:
            api_key = ""
    
    if not api_key:
        st.error("Please set GROQ_API_KEY in Streamlit Cloud secrets")
        return None
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )


def generate_slides(topic: str, num_slides: int = 6) -> list:
    """Generate slides using Groq AI"""
    client = get_ai_client()
    if not client:
        return None
    
    prompt = f"""Create a professional presentation about: {topic}

Generate exactly {num_slides} slides in JSON format. Choose the BEST slide type for each content:

Available slide types:
- title: Main presentation title slide (big title + subtitle)
- content: Standard content (title + subtitle + bullets)
- bullets_image: Content with image on right side
- two_column: Two columns of content
- divider: Section transition (big centered title)
- quote: Quote or testimonial with author
- statistic: Big number with label (e.g., "85%", "$1B", "3x")
- comparison: Two-column comparison (pros/cons, before/after)
- timeline: Chronological events with dates
- full_image: Full-bleed image with caption overlay

AI should auto-select the best layout based on content. For example:
- First slide = title
- Data/metrics slides = statistic  
- Comparisons = comparison
- History/timeline = timeline
- Quotes from sources = quote
- Image-heavy slides = bullets_image or full_image
- Section breaks = divider

For each slide, include appropriate fields:
- type: auto-selected layout
- title: The slide title
- subtitle: Brief description
- bullets: 2-5 key points (use for content, bullets_image, two_column)
- quote: The quote text (for quote layout)
- author: Quote author (for quote layout)
- big_number: Large number like "85%" or "$1B" (for statistic)
- stat_label: Label for the number (for statistic)  
- left_title: Title for left column (for comparison)
- left_items: Items for left column (for comparison)
- right_title: Title for right column (for comparison)
- right_items: Items for right column (for comparison)
- events: Array of {{"date": "2020", "title": "Event"}} (for timeline)
- image_url: Direct image URL (for full_image, bullets_image)
- caption: Image caption (for full_image)
- image_keywords: Keywords for relevant image

Return ONLY valid JSON array (no code blocks):
[
  {{"type": "title", "title": "Main Title", "subtitle": "Subtitle", "bullets": [], "image_keywords": ""}},
  {{"type": "statistic", "title": "", "subtitle": "", "big_number": "85%", "stat_label": "Growth", "image_keywords": ""}},
  ...
]

Return only the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        
        content = response.choices[0].message.content
        slides = parse_slides_json(content)
        return slides
    except Exception as e:
        st.error(f"Error generating slides: {e}")
        return None


def parse_slides_json(content: str) -> list:
    """Parse JSON response from AI"""
    try:
        content = content.strip()
        start = content.find("[")
        end = content.rfind("]")
        
        if start >= 0 and end > start:
            content = content[start:end+1]
        elif "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        slides = json.loads(content.strip())
        
        if isinstance(slides, list):
            for slide in slides:
                slide.setdefault("type", "content")
                slide.setdefault("title", "")
                slide.setdefault("subtitle", "")
                slide.setdefault("bullets", [])
                slide.setdefault("quote", "")
                slide.setdefault("author", "")
                slide.setdefault("big_number", "")
                slide.setdefault("stat_label", "")
                slide.setdefault("left_title", "")
                slide.setdefault("left_items", [])
                slide.setdefault("right_title", "")
                slide.setdefault("right_items", [])
                slide.setdefault("events", [])
                slide.setdefault("image_keywords", "")
                slide.setdefault("image_url", "")
                slide.setdefault("caption", "")
            return slides
        return []
    except Exception as e:
        st.error(f"Error parsing slides: {e}")
        return []


def build_slide_markdown(slide: dict) -> str:
    """Build reveal.js markdown for a slide"""
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    bullets = slide.get("bullets", [])
    quote = slide.get("quote", "")
    author = slide.get("author", "")
    big_number = slide.get("big_number", "")
    stat_label = slide.get("stat_label", "")
    left_title = slide.get("left_title", "Pros")
    right_title = slide.get("right_title", "Cons")
    left_items = slide.get("left_items", bullets[:3])
    right_items = slide.get("right_items", bullets[3:])
    events = slide.get("events", [])
    
    if slide_type == "title":
        return f"## {title}\n### {subtitle}"
    
    elif slide_type == "divider":
        return f"# {title}\n### {subtitle}"
    
    elif slide_type == "quote":
        return f"> {quote}\n\n> — *{author}*"
    
    elif slide_type == "statistic":
        return f"# {big_number}\n## {stat_label}\n### {subtitle}"
    
    elif slide_type == "comparison":
        left = "\n".join([f"- {i}" for i in left_items])
        right = "\n".join([f"- {i}" for i in right_items])
        return f"## {title}\n\n### {left_title}\n{left}\n\n### {right_title}\n{right}"
    
    elif slide_type == "timeline":
        timeline = "\n".join([f"**{e.get('date', '')}** - {e.get('title', '')}" for e in events])
        return f"## {title}\n\n{timeline}"
    
    elif slide_type == "bullets_image":
        bullet_list = "\n".join([f"- {b}" for b in bullets])
        return f"## {title}\n\n{bullet_list}"
    
    elif slide_type == "two_column":
        left = "\n".join([f"- {b}" for b in bullets[:3]])
        right = "\n".join([f"- {b}" for b in bullets[3:]])
        return f"## {title}\n\n### Column 1\n{left}\n\n### Column 2\n{right}"
    
    else:
        bullet_list = "\n".join([f"- {b}" for b in bullets])
        return f"## {title}\n### {subtitle}\n\n{bullet_list}"


def build_presentation_markdown(slides: list) -> str:
    """Build complete reveal.js presentation markdown"""
    md = "---\n"
    md += "title: Presentation\n"
    md += "author: Slider-Web\n"
    md += "---\n\n"
    
    for i, slide in enumerate(slides):
        md += f"## Slide {i+1}\n"
        md += build_slide_markdown(slide)
        md += "\n\n"
    
    return md


def export_pptx(slides: list, title: str) -> bytes:
    """Export slides to PPTX"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    accent_color = RGBColor(74, 144, 217)
    primary_color = RGBColor(30, 30, 46)
    
    for slide_data in slides:
        slide_type = slide_data.get("type", "content")
        content_slide = prs.slides.add_slide(prs.slide_layouts[6])
        s = content_slide.shapes
        
        bg = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = primary_color
        bg.line.fill.background()
        
        hdr = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.9))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = accent_color
        hdr.line.fill.background()
        
        title_text = slide_data.get("title", "Slide")
        tb = s.add_textbox(Inches(0.5), Inches(0.2), Inches(12), Inches(0.7))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        
        if slide_type == "statistic":
            big_num = slide_data.get("big_number", "")
            stat_label = slide_data.get("stat_label", "")
            nb = s.add_textbox(Inches(1), Inches(2), Inches(11.333), Inches(2.5))
            tf = nb.text_frame
            p = tf.paragraphs[0]
            p.text = big_num if big_num else "85%"
            p.font.size = Pt(72)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = RGBColor(255, 255, 255)
            
            if stat_label:
                sb = s.add_textbox(Inches(1), Inches(4.5), Inches(11.333), Inches(1))
                tf = sb.text_frame
                p = tf.paragraphs[0]
                p.text = stat_label
                p.font.size = Pt(28)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = accent_color
        
        elif slide_type == "quote":
            quote_text = slide_data.get("quote", "")
            author_text = slide_data.get("author", "")
            qb = s.add_textbox(Inches(1.5), Inches(1.5), Inches(10), Inches(3.5))
            tf = qb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f'"{quote_text}"' if quote_text else '"Quote"'
            p.font.size = Pt(36)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = RGBColor(255, 255, 255)
            
            if author_text:
                ab = s.add_textbox(Inches(1.5), Inches(5.2), Inches(10), Inches(0.8))
                tf = ab.text_frame
                p = tf.paragraphs[0]
                p.text = f"— {author_text}"
                p.font.size = Pt(20)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = accent_color
        
        else:
            bullet_list = slide_data.get("bullets", [])
            y = 1.3
            bb = s.add_textbox(Inches(0.5), Inches(y), Inches(12), Inches(5))
            tf = bb.text_frame
            tf.word_wrap = True
            
            for j, b in enumerate(bullet_list):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.text = b
                p.font.size = Pt(20)
                p.space_before = Pt(10)
                p.font.color.rgb = RGBColor(230, 230, 230)
    
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def main():
    st.title("📊 Slider-Web")
    st.caption("AI Presentation Maker - Free, No Downloads")
    
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'selected_slide' not in st.session_state:
        st.session_state.selected_slide = 0
    
    with st.sidebar:
        st.header("🎛️ Controls")
        
        topic = st.text_input("Topic", placeholder="e.g., History of AI")
        
        num_slides = st.selectbox("Slides", list(range(4, 13)), index=2)
        
        if st.button("🚀 Generate", type="primary", use_container_width=True):
            if topic:
                with st.spinner("Generating presentation..."):
                    slides = generate_slides(topic, num_slides)
                    if slides:
                        st.session_state.slides = slides
                        st.session_state.selected_slide = 0
                        st.success(f"Generated {len(slides)} slides!")
            else:
                st.warning("Please enter a topic")
        
        st.divider()
        
        if st.session_state.slides:
            st.subheader("📑 Slides")
            for i, slide in enumerate(st.session_state.slides):
                slide_type = slide.get("type", "content")
                title = slide.get("title", f"Slide {i+1}")
                if st.button(f"{i+1}. [{slide_type}] {title[:25]}...", key=f"slide_{i}"):
                    st.session_state.selected_slide = i
            
            st.divider()
            
            if st.button("🗑️ Clear All"):
                st.session_state.slides = []
                st.session_state.selected_slide = 0
                st.rerun()
    
    col_main, col_preview = st.columns([1, 1])
    
    with col_main:
        st.subheader("✏️ Edit Slides")
        
        if st.session_state.slides:
            idx = st.selectbox(
                "Select Slide", 
                range(len(st.session_state.slides)), 
                index=st.session_state.selected_slide,
                key="slide_selector"
            )
            st.session_state.selected_slide = idx
            
            slide = st.session_state.slides[idx]
            
            current_type = slide.get("type", "content")
            type_index = list(SLIDE_TYPES.keys()).index(current_type) if current_type in SLIDE_TYPES else 1
            
            new_type = st.selectbox(
                "Layout", 
                list(SLIDE_TYPES.keys()), 
                index=type_index,
                format_func=lambda x: SLIDE_TYPES[x],
                key="layout_selector"
            )
            slide["type"] = new_type
            
            slide["title"] = st.text_input("Title", slide.get("title", ""))
            slide["subtitle"] = st.text_input("Subtitle", slide.get("subtitle", ""))
            
            if new_type in ("content", "bullets_image", "two_column"):
                bullets = "\n".join([b for b in slide.get("bullets", []) if b])
                slide["bullets"] = [b for b in st.text_area("Bullets", bullets).split("\n") if b.strip()]
            
            elif new_type == "quote":
                slide["quote"] = st.text_area("Quote", slide.get("quote", ""))
                slide["author"] = st.text_input("Author", slide.get("author", ""))
            
            elif new_type == "statistic":
                slide["big_number"] = st.text_input("Big Number", slide.get("big_number", ""))
                slide["stat_label"] = st.text_input("Label", slide.get("stat_label", ""))
            
            elif new_type == "comparison":
                slide["left_title"] = st.text_input("Left Title", slide.get("left_title", "Pros"))
                left_items = "\n".join([b for b in slide.get("left_items", []) if b])
                slide["left_items"] = [b for b in st.text_area("Left Items", left_items).split("\n") if b.strip()]
                slide["right_title"] = st.text_input("Right Title", slide.get("right_title", "Cons"))
                right_items = "\n".join([b for b in slide.get("right_items", []) if b])
                slide["right_items"] = [b for b in st.text_area("Right Items", right_items).split("\n") if b.strip()]
            
            elif new_type == "timeline":
                events_str = "\n".join([f"{e.get('date', '')} - {e.get('title', '')}" for e in slide.get("events", [])])
                events_text = st.text_area("Events (YYYY - Event)", events_str)
                slide["events"] = []
                for line in events_text.split("\n"):
                    if line.strip() and " - " in line:
                        parts = line.split(" - ", 1)
                        slide["events"].append({"date": parts[0].strip(), "title": parts[1].strip()})
            
            slide["image_keywords"] = st.text_input("Image Keywords", slide.get("image_keywords", ""))
            
            if st.button("💾 Save Changes"):
                st.success("Saved!")
        
        else:
            st.info("👈 Enter a topic and click Generate to create slides")
    
    with col_preview:
        st.subheader("👁️ Live Preview")
        
        if st.session_state.slides:
            try:
                import reveal_slides as rs
                md = build_presentation_markdown(st.session_state.slides)
                rs.slides(md, width="100%", height="500px")
            except:
                st.markdown("### Slide Preview")
                for i, slide in enumerate(st.session_state.slides):
                    st.markdown(f"**{i+1}. {slide.get('title', 'Untitled')}** ({slide.get('type', 'content')})")
                    bullets = slide.get("bullets", [])
                    if bullets:
                        for b in bullets:
                            st.markdown(f"- {b}")
                    st.divider()
        else:
            st.info("Generate slides to see preview")
    
    if st.session_state.slides:
        st.divider()
        st.subheader("📥 Export")
        
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("📊 Generate PPTX", use_container_width=True):
                pptx_data = export_pptx(st.session_state.slides, "Presentation")
                st.download_button(
                    "📊 Download PPTX",
                    pptx_data,
                    "presentation.pptx",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
        
        with c2:
            md = build_presentation_markdown(st.session_state.slides)
            st.download_button(
                "🌐 Download HTML",
                md,
                "presentation.html",
                "text/html",
                use_container_width=True
            )


if __name__ == "__main__":
    main()