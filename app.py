"""Slider-Web - AI Presentation Maker - Professional Streamlit Web App"""

import streamlit as st
import json
import os
from io import BytesIO
from openai import OpenAI

st.set_page_config(
    page_title="Slider-Web - AI Presentations",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


SLIDE_TYPES = {
    "title": "Title - Big title with subtitle",
    "content": "Content - Title and bullets",
    "bullets_image": "Bullets + Image",
    "two_column": "Two Column",
    "divider": "Divider - Section break",
    "quote": "Quote - Testimonial",
    "statistic": "Statistic - Big numbers",
    "comparison": "Comparison - Pros/Cons",
    "timeline": "Timeline - History",
    "full_image": "Full Image - Hero",
    "section_header": "Section Header",
    "blank": "Blank",
    "caption_left": "Caption + Left",
    "caption_right": "Caption + Right",
}

THEMES = {
    "corporate": {"name": "Corporate Blue", "accent": "0A3D62", "primary": "1C2833"},
    "modern": {"name": "Modern Purple", "accent": "E94560", "primary": "1A1A2E"},
    "minimal": {"name": "Minimal Gray", "accent": "4A90D9", "primary": "F5F5F5"},
    "elegant": {"name": "Elegant Gold", "accent": "D4AF37", "primary": "1A1A1A"},
    "nature": {"name": "Nature Green", "accent": "27AE60", "primary": "2C3E50"},
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
        st.error(" Please set GROQ_API_KEY in Streamlit Cloud secrets")
        return None
    
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def generate_slides(topic: str, num_slides: int = 6) -> list:
    """Generate slides using Groq AI"""
    client = get_ai_client()
    if not client:
        return None
    
    prompt = f"""Create a professional presentation about: {topic}

Generate exactly {num_slides} slides in JSON format. Choose the BEST slide type:

Slide types:
- title: Main presentation title slide
- content: Standard content (title + subtitle + bullets)
- bullets_image: Content with image area
- two_column: Two columns of bullets
- divider: Section transition (big title)
- quote: Quote with author
- statistic: Big number with label (85%, $1B)
- comparison: Two-column pros/cons
- timeline: Events with dates
- full_image: Full image with caption
- section_header: Section header

For each slide include: type, title, subtitle, bullets, quote, author, big_number, stat_label, left_title, left_items, right_title, right_items, events, image_keywords, notes

Return ONLY valid JSON array:
[
  {{"type": "title", "title": "Main Title", "subtitle": "Subtitle"}},
  ...
]

Return only JSON, no other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        content = response.choices[0].message.content
        return parse_slides_json(content)
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def parse_slides_json(content: str) -> list:
    """Parse JSON from AI"""
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
    except:
        return []


def build_slide_markdown(slide: dict) -> str:
    """Build reveal.js markdown"""
    stype = slide.get("type", "content")
    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    bullets = slide.get("bullets", [])
    
    if stype == "title":
        return f"## {title}\n### {subtitle}"
    elif stype == "divider":
        return f"# {title}\n### {subtitle}"
    elif stype == "quote":
        return f"> {slide.get('quote', '')}\n\n> — *{slide.get('author', '')}*"
    elif stype == "statistic":
        return f"# {slide.get('big_number', '')}\n## {slide.get('stat_label', '')}\n### {subtitle}"
    elif stype == "comparison":
        left = "\n".join([f"- {i}" for i in slide.get("left_items", bullets[:3])])
        right = "\n".join([f"- {i}" for i in slide.get("right_items", bullets[3:])])
        return f"## {title}\n\n### {slide.get('left_title', 'Pros')}\n{left}\n\n### {slide.get('right_title', 'Cons')}\n{right}"
    elif stype == "timeline":
        tline = "\n".join([f"**{e.get('date', '')}** - {e.get('title', '')}" for e in slide.get("events", [])])
        return f"## {title}\n\n{tline}"
    else:
        blist = "\n".join([f"- {b}" for b in bullets])
        return f"## {title}\n### {subtitle}\n\n{blist}"


def build_presentation_markdown(slides: list, theme: str = "corporate") -> str:
    """Build reveal.js presentation"""
    theme_colors = {
        "corporate": {"bg": "#1C2833", "accent": "#0A3D62"},
        "modern": {"bg": "#1A1A2E", "accent": "#E94560"},
        "minimal": {"bg": "#F5F5F5", "accent": "#4A90D9"},
        "elegant": {"bg": "#1A1A1A", "accent": "#D4AF37"},
        "nature": {"bg": "#2C3E50", "accent": "#27AE60"},
    }
    colors = theme_colors.get(theme, theme_colors["corporate"])
    
    md = f"---\ntitle: Presentation\nauthor: Slider-Web\ntheme: {theme}\n---\n\n"
    md += f".theme-bg {{ background: {colors['bg']}; }}\n"
    md += f".theme-accent {{ background: {colors['accent']}; }}\n\n"
    
    for i, slide in enumerate(slides):
        md += f"## Slide {i+1}\n{build_slide_markdown(slide)}\n\n"
    return md


def export_pptx(slides: list, title: str, theme: str = "corporate") -> bytes:
    """Export professional PPTX"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    
    theme_colors = {
        "corporate": {"accent": RGBColor(10, 61, 98), "primary": RGBColor(28, 40, 51), "text": RGBColor(255, 255, 255)},
        "modern": {"accent": RGBColor(233, 69, 96), "primary": RGBColor(26, 26, 46), "text": RGBColor(255, 255, 255)},
        "minimal": {"accent": RGBColor(74, 144, 217), "primary": RGBColor(245, 245, 245), "text": RGBColor(26, 26, 26)},
        "elegant": {"accent": RGBColor(212, 175, 55), "primary": RGBColor(26, 26, 26), "text": RGBColor(255, 255, 255)},
        "nature": {"accent": RGBColor(39, 174, 96), "primary": RGBColor(44, 62, 80), "text": RGBColor(255, 255, 255)},
    }
    colors = theme_colors.get(theme, theme_colors["corporate"])
    
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    for slide_data in slides:
        stype = slide_data.get("type", "content")
        content_slide = prs.slides.add_slide(prs.slide_layouts[6])
        s = content_slide.shapes
        
        bg = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = colors["primary"]
        bg.line.fill.background()
        
        hdr = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.0))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = colors["accent"]
        hdr.line.fill.background()
        
        title_text = slide_data.get("title", "Slide")
        subtitle = slide_data.get("subtitle", "")
        
        tb = s.add_textbox(Inches(0.5), Inches(0.25), Inches(12), Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = colors["text"]
        
        if stype == "statistic":
            big = slide_data.get("big_number", "")
            label = slide_data.get("stat_label", "")
            nb = s.add_textbox(Inches(1), Inches(2.2), Inches(11.333), Inches(2.8))
            tf = nb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = big if big else "85%"
            p.font.size = Pt(80)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = colors["text"]
            
            if label:
                sb = s.add_textbox(Inches(1), Inches(5), Inches(11.333), Inches(1))
                tf = sb.text_frame
                p = tf.paragraphs[0]
                p.text = label
                p.font.size = Pt(28)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = colors["accent"]
        
        elif stype == "quote":
            qt = slide_data.get("quote", "")
            auth = slide_data.get("author", "")
            qb = s.add_textbox(Inches(1.5), Inches(1.8), Inches(10), Inches(3))
            tf = qb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f'"{qt}"' if qt else '"Quote"'
            p.font.size = Pt(32)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = colors["text"]
            
            if auth:
                ab = s.add_textbox(Inches(1.5), Inches(5), Inches(10), Inches(0.8))
                tf = ab.text_frame
                p = tf.paragraphs[0]
                p.text = f"— {auth}"
                p.font.size = Pt(22)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = colors["accent"]
        
        elif stype == "comparison":
            lt = slide_data.get("left_title", "Pros")
            ri = slide_data.get("right_title", "Cons")
            li = slide_data.get("left_items", slide_data.get("bullets", [])[:3])
            ri_items = slide_data.get("right_items", slide_data.get("bullets", [])[3:])
            
            ltb = s.add_textbox(Inches(0.5), Inches(1.2), Inches(6), Inches(0.5))
            tf = ltb.text_frame
            p = tf.paragraphs[0]
            p.text = lt
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = colors["accent"]
            
            rtb = s.add_textbox(Inches(7), Inches(1.2), Inches(6), Inches(0.5))
            tf = rtb.text_frame
            p = tf.paragraphs[0]
            p.text = ri
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 100, 100)
            
            left = s.add_textbox(Inches(0.5), Inches(1.8), Inches(6), Inches(5))
            tf = left.text_frame
            tf.word_wrap = True
            for j, item in enumerate(li):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.text = item
                p.font.size = Pt(18)
                p.space_before = Pt(8)
                p.font.color.rgb = colors["text"]
            
            right = s.add_textbox(Inches(7), Inches(1.8), Inches(6), Inches(5))
            tf = right.text_frame
            tf.word_wrap = True
            for j, item in enumerate(ri_items):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.text = item
                p.font.size = Pt(18)
                p.space_before = Pt(8)
                p.font.color.rgb = colors["text"]
        
        elif stype == "divider":
            db = s.add_textbox(Inches(1), Inches(3), Inches(11.333), Inches(2))
            tf = db.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title_text
            p.font.size = Pt(56)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = colors["text"]
            
            sub = slide_data.get("subtitle", "")
            if sub:
                sb = s.add_textbox(Inches(1), Inches(5.2), Inches(11.333), Inches(1))
                tf = sb.text_frame
                p = tf.paragraphs[0]
                p.text = sub
                p.font.size = Pt(24)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = colors["accent"]
        
        elif stype == "title":
            ab = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.15), Inches(7.5))
            ab.fill.solid()
            ab.fill.fore_color.rgb = colors["accent"]
            ab.line.fill.background()
            
            tb = s.add_textbox(Inches(2), Inches(2.5), Inches(10), Inches(2))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title_text
            p.font.size = Pt(52)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = colors["text"]
            
            if subtitle:
                sb = s.add_textbox(Inches(2), Inches(4.5), Inches(10), Inches(1))
                tf = sb.text_frame
                p = tf.paragraphs[0]
                p.text = subtitle
                p.font.size = Pt(24)
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = colors["accent"]
        
        elif stype == "timeline":
            events = slide_data.get("events", [])
            y = 1.3
            for e in events[:5]:
                date = e.get("date", "")
                event_title = e.get("title", "")
                
                marker = s.add_shape(MSO_SHAPE.OVAL, Inches(1.2), Inches(y), Inches(0.25), Inches(0.25))
                marker.fill.solid()
                marker.fill.fore_color.rgb = colors["accent"]
                marker.line.fill.background()
                
                db = s.add_textbox(Inches(1.8), Inches(y), Inches(2), Inches(0.4))
                tf = db.text_frame
                p = tf.paragraphs[0]
                p.text = date
                p.font.size = Pt(14)
                p.font.bold = True
                p.font.color.rgb = colors["accent"]
                
                tb = s.add_textbox(Inches(4), Inches(y), Inches(8), Inches(0.4))
                tf = tb.text_frame
                p = tf.paragraphs[0]
                p.text = event_title
                p.font.size = Pt(16)
                p.font.color.rgb = colors["text"]
                
                if y < 5.5:
                    line = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.3), Inches(y + 0.3), Inches(0.1), Inches(0.4))
                    line.fill.solid()
                    line.fill.fore_color.rgb = colors["accent"]
                    line.line.fill.background()
                
                y += 1.1
        
        else:
            sub = slide_data.get("subtitle", "")
            y = 1.3
            if sub:
                sb = s.add_textbox(Inches(0.5), Inches(1.1), Inches(12), Inches(0.4))
                tf = sb.text_frame
                p = tf.paragraphs[0]
                p.text = sub
                p.font.size = Pt(14)
                p.font.color.rgb = RGBColor(180, 180, 180)
                y = 1.6
            
            bb = s.add_textbox(Inches(0.5), Inches(y), Inches(12), Inches(5))
            tf = bb.text_frame
            tf.word_wrap = True
            
            for j, b in enumerate(slide_data.get("bullets", [])):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.text = b
                p.font.size = Pt(20)
                p.space_before = Pt(10)
                p.font.color.rgb = colors["text"]
    
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


st.markdown("""
<style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .sidebar .stButton > button {width: 100%;}
    
    .slide-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .slide-preview {
        background: #0f0f23;
        padding: 1rem;
        border-radius: 8px;
        min-height: 150px;
        margin: 0.5rem 0;
    }
    
    .preview-title {color: #4A90D9; font-size: 1.2rem; font-weight: bold;}
    .preview-bullet {color: #aaa; font-size: 0.9rem;}
    
    .stTextInput > div > div {border-radius: 8px;}
    .stTextArea > div > div {border-radius: 8px;}
    
    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📊 Slider-Web")
    st.caption("Professional AI Presentations | Free, No Downloads")
    
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'selected_slide' not in st.session_state:
        st.session_state.selected_slide = 0
    if 'theme' not in st.session_state:
        st.session_state.theme = "corporate"
    
    with st.sidebar:
        st.markdown("### 🎛️ Create Presentation")
        
        topic = st.text_input("Topic", placeholder="e.g., History of Artificial Intelligence", key="topic_input")
        col1, col2 = st.columns(2)
        with col1:
            num_slides = st.selectbox("Slides", list(range(4, 13)), index=2, key="slide_count")
        with col2:
            theme = st.selectbox("Theme", list(THEMES.keys()), format_func=lambda x: THEMES[x]["name"], key="theme_sel")
            st.session_state.theme = theme
        
        st.markdown("---")
        
        if st.button("🚀 Generate Presentation", type="primary", use_container_width=True):
            if topic:
                with st.spinner("🤖 AI is creating your presentation..."):
                    slides = generate_slides(topic, num_slides)
                    if slides:
                        st.session_state.slides = slides
                        st.session_state.selected_slide = 0
                        st.session_state.theme = theme
                        st.rerun()
            else:
                st.warning("Please enter a topic")
        
        st.markdown("---")
        
        if st.session_state.slides:
            st.markdown("#### 📑 All Slides")
            
            for i, slide in enumerate(st.session_state.slides):
                stype = slide.get("type", "content")
                title = slide.get("title", f"Slide {i+1}")[:30]
                
                with st.expander(f"**{i+1}. {title}** ({stype})"):
                    st.markdown(f"**Type:** {SLIDE_TYPES.get(stype, stype)}")
                    if slide.get("subtitle"):
                        st.markdown(f"**Subtitle:** {slide.get('subtitle')}")
                    if slide.get("bullets"):
                        for b in slide.get("bullets", [])[:3]:
                            st.markdown(f"• {b}")
                    
                    if st.button(f"Edit {i+1}", key=f"edit_{i}"):
                        st.session_state.selected_slide = i
                        st.rerun()
            
            st.markdown("---")
            
            if st.button("🗑️ New Presentation", use_container_width=True):
                st.session_state.slides = []
                st.session_state.selected_slide = 0
                st.rerun()
    
    col_main, col_prev = st.columns([1, 1])
    
    with col_main:
        st.markdown("### ✏️ Edit Slide")
        
        if st.session_state.slides:
            idx = st.selectbox(
                "Select Slide", 
                range(len(st.session_state.slides)), 
                index=st.session_state.selected_slide,
                format_func=lambda x: f"Slide {x+1}",
                key="slide_sel"
            )
            st.session_state.selected_slide = idx
            
            slide = st.session_state.slides[idx]
            
            with st.expander("📋 Layout & Content", expanded=True):
                current_type = slide.get("type", "content")
                type_index = list(SLIDE_TYPES.keys()).index(current_type) if current_type in SLIDE_TYPES else 1
                
                new_type = st.selectbox(
                    "Slide Layout", 
                    list(SLIDE_TYPES.keys()), 
                    index=type_index,
                    format_func=lambda x: SLIDE_TYPES[x],
                    key="layout_sel"
                )
                slide["type"] = new_type
                
                slide["title"] = st.text_input("Title", slide.get("title", ""))
                slide["subtitle"] = st.text_input("Subtitle", slide.get("subtitle", ""))
                
                if new_type in ("content", "bullets_image", "two_column"):
                    bullets = "\n".join([b for b in slide.get("bullets", []) if b])
                    slide["bullets"] = [b for b in st.text_area("Bullet Points", bullets, height=100).split("\n") if b.strip()]
                
                elif new_type == "quote":
                    slide["quote"] = st.text_area("Quote", slide.get("quote", ""), height=80)
                    slide["author"] = st.text_input("Author", slide.get("author", ""))
                
                elif new_type == "statistic":
                    slide["big_number"] = st.text_input("Big Number", slide.get("big_number", ""))
                    slide["stat_label"] = st.text_input("Label", slide.get("stat_label", ""))
                
                elif new_type == "comparison":
                    slide["left_title"] = st.text_input("Left Column Title", slide.get("left_title", "Pros"))
                    left_items = "\n".join([b for b in slide.get("left_items", []) if b])
                    slide["left_items"] = [b for b in st.text_area("Left Items", left_items, height=80).split("\n") if b.strip()]
                    slide["right_title"] = st.text_input("Right Column Title", slide.get("right_title", "Cons"))
                    right_items = "\n".join([b for b in slide.get("right_items", []) if b])
                    slide["right_items"] = [b for b in st.text_area("Right Items", right_items, height=80).split("\n") if b.strip()]
                
                elif new_type == "timeline":
                    events_str = "\n".join([f"{e.get('date', '')} - {e.get('title', '')}" for e in slide.get("events", [])])
                    events_text = st.text_area("Events (YYYY - Event)", events_str, height=100)
                    slide["events"] = []
                    for line in events_text.split("\n"):
                        if line.strip() and " - " in line:
                            parts = line.split(" - ", 1)
                            slide["events"].append({"date": parts[0].strip(), "title": parts[1].strip()})
                
                slide["image_keywords"] = st.text_input("Image Keywords", slide.get("image_keywords", ""))
                
                if st.button("💾 Save Changes", type="primary"):
                    st.success("✅ Changes saved!")
                    st.rerun()
        else:
            st.markdown("""
            <div class="slide-card" style="text-align: center; padding: 3rem;">
                <h3>👋 Welcome to Slider-Web!</h3>
                <p>Enter a topic in the sidebar and click Generate to create your AI presentation.</p>
                <p style="color: #888; margin-top: 1rem;">Free, professional presentations in seconds.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_prev:
        st.markdown("### 👁️ Live Preview")
        
        if st.session_state.slides:
            try:
                import reveal_slides as rs
                md = build_presentation_markdown(st.session_state.slides, st.session_state.theme)
                rs.slides(md, width="100%", height="450px")
            except:
                st.markdown("#### 📊 Slide Preview")
                for i, slide in enumerate(st.session_state.slides[:3]):
                    with st.expander(f"Slide {i+1}: {slide.get('title', 'Untitled')[:40]}"):
                        st.markdown(f"**Type:** {slide.get('type', 'content')}")
                        if slide.get("bullets"):
                            for b in slide.get("bullets", []):
                                st.markdown(f"• {b}")
        else:
            st.info("Generate slides to see preview")
    
    if st.session_state.slides:
        st.markdown("---")
        st.markdown("### 📥 Export")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            pptx_data = export_pptx(st.session_state.slides, "Presentation", st.session_state.theme)
            st.download_button(
                "📊 Download PPTX",
                pptx_data,
                "presentation.pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                type="primary"
            )
        
        with c2:
            md = build_presentation_markdown(st.session_state.slides, st.session_state.theme)
            st.download_button(
                "🌐 Download HTML",
                md,
                "presentation.html",
                "text/html",
                use_container_width=True
            )
        
        with c3:
            json_data = json.dumps(st.session_state.slides, indent=2)
            st.download_button(
                "📋 Download JSON",
                json_data,
                "slides.json",
                "application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()