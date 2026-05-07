"""Slider-Web - Gamma-like AI Presentation Maker"""

import streamlit as st
import json
import os
from io import BytesIO
from openai import OpenAI

st.set_page_config(
    page_title="Slider-Web",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)


PRESET_TONES = {
    "default": {"name": "Professional", "bg": "#1a1a2e", "accent": "#6366f1"},
    "bold": {"name": "Bold & Modern", "bg": "#0f0f23", "accent": "#f43f5e"},
    "minimal": {"name": "Minimal Clean", "bg": "#fafafa", "accent": "#1e293b"},
    "elegant": {"name": "Elegant", "bg": "#1c1917", "accent": "#d4af37"},
    "playful": {"name": "Playful", "bg": "#1e1b4b", "accent": "#ec4899"},
}

SLIDE_TEMPLATES = {
    "title": {"icon": "🎯", "name": "Title"},
    "content": {"icon": "📝", "name": "Content"},
    "bullets": {"icon": "📋", "name": "Bullets"},
    "two_col": {"icon": "📊", "name": "Two Columns"},
    "big_text": {"icon": "💬", "name": "Big Text"},
    "quote": {"icon": "💭", "name": "Quote"},
    "stats": {"icon": "📈", "name": "Stats"},
    "comparison": {"icon": "⚖️", "name": "Comparison"},
    "timeline": {"icon": "📅", "name": "Timeline"},
    "image": {"icon": "🖼️", "name": "Image"},
}


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except:
            api_key = ""
    if not api_key:
        st.error(" Please add GROQ_API_KEY in Streamlit Cloud settings")
        return None
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def generate_gamma_style(topic, num_slides, tone, title_text):
    client = get_groq_client()
    if not client:
        return None
    
    prompt = f"""Create a stunning AI presentation about: {topic}

Create {num_slides} beautiful slides. Make them feel like Gamma - professional, modern, visually appealing.

Format: Return JSON array.

Slide structure for each:
- type: template name
- title: slide title
- content: the main text/points
- subtitle: secondary info (keep brief)
- template: which template to use

Choose templates naturally:
- First slide = title
- For big ideas/stats = stats  
- For quotes = quote
- For comparisons = comparison
- For history = timeline
- Content with images = image or bullets
- Regular content = content or two_col

Tone: {tone}

Include these fields for each slide:
- type: the slide type
- title: title
- content: main text (can be array or text)
- subtitle: brief subtitle
- template: use natural template names

Return ONLY valid JSON:
[
  {{"type": "title", "title": "Presentation Title", "subtitle": "Tagline", "template": "title"}},
  {{"type": "content", "title": "Slide Title", "content": "Key points here", "template": "content"}},
  ...
]

No extra text - ONLY JSON."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2500,
        )
        content = response.choices[0].message.content
        return parse_gamma_slides(content)
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def parse_gamma_slides(content):
    try:
        content = content.strip()
        start = content.find("[")
        end = content.rfind("]")
        if start >= 0 and end > start:
            content = content[start:end+1]
        
        slides = json.loads(content)
        
        if isinstance(slides, list):
            for slide in slides:
                slide.setdefault("type", "content")
                slide.setdefault("title", "")
                slide.setdefault("content", "")
                slide.setdefault("subtitle", "")
                slide.setdefault("template", slide.get("type", "content"))
            return slides
        return []
    except:
        return []


def render_card(slide, theme, index):
    """Render a beautiful card like Gamma"""
    tone = PRESET_TONES.get(theme, PRESET_TONES["default"])
    accent = tone["accent"]
    
    content = slide.get("content", "")
    if isinstance(content, list):
        content_text = "<br>".join([f"• {c}" for c in content[:4]])
    else:
        content_text = content[:200] if content else ""
    
    template = slide.get("template", "content")
    icon = SLIDE_TEMPLATES.get(template, {}).get("icon", "📝")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {tone['bg']} 0%, #1a1a2e 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        border: 1px solid rgba(255,255,255,0.1);
        min-height: 120px;
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 24px;">{icon}</span>
            <span style="color: {accent}; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                {SLIDE_TEMPLATES.get(template, {}).get('name', 'Content')}
            </span>
        </div>
        <h3 style="color: white; margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">
            {slide.get('title', 'Slide')}
        </h3>
        <div style="color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.5;">
            {content_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


def export_gamma_pptx(slides, theme):
    """Modern PPTX export"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    
    tone = PRESET_TONES.get(theme, PRESET_TONES["default"])
    accent = tone["accent"]
    
    def hex_rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    
    primary = hex_rgb(tone["bg"])
    accent_color = hex_rgb(accent)
    text_color = RGBColor(255, 255, 255) if tone != "minimal" else RGBColor(26, 26, 26)
    subtext = RGBColor(150, 150, 150)
    
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    for slide_data in slides:
        tmpl = slide_data.get("template", "content")
        content = slide_data.get("content", "")
        if isinstance(content, list):
            bullets = content
        else:
            bullets = content.split("\n") if content else []
        
        s = prs.slides.add_slide(prs.slide_layouts[6])
        
        bg = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = primary
        bg.line.fill.background()
        
        bar = s.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.08))
        bar.fill.solid()
        bar.fill.fore_color.rgb = accent_color
        bar.line.fill.background()
        
        title_tb = s.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(1))
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_p = title_tf.paragraphs[0]
        title_p.text = slide_data.get("title", "Slide")
        title_p.font.size = Pt(36)
        title_p.font.bold = True
        title_p.font.color.rgb = text_color
        
        sub = slide_data.get("subtitle", "")
        if sub:
            sub_tb = s.add_textbox(Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.6))
            sub_tf = sub_tb.text_frame
            sub_p = sub_tf.paragraphs[0]
            sub_p.text = sub
            sub_p.font.size = Pt(18)
            sub_p.font.color.rgb = accent_color
        
        y_pos = 2.2
        if tmpl == "title":
            title_tb.top = Inches(2.5)
            title_tb.left = Inches(1)
            if sub:
                sub_tb.top = Inches(4)
            bg.fill.fore_color.rgb = accent_color
        
        elif tmpl == "stats":
            stat_text = slide_data.get("stats", "85%")
            stat_tb = s.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(2))
            stat_tf = stat_tb.text_frame
            stat_p = stat_tf.paragraphs[0]
            stat_p.text = str(stat_text)
            stat_p.font.size = Pt(80)
            stat_p.font.bold = True
            stat_p.alignment = PP_ALIGN.CENTER
            stat_p.font.color.rgb = accent_color
        
        elif tmpl == "quote":
            quote_tb = s.add_textbox(Inches(1.5), Inches(2), Inches(10), Inches(3))
            quote_tf = quote_tb.text_frame
            quote_tf.word_wrap = True
            quote_p = quote_tf.paragraphs[0]
            quote_p.text = f'"{content}"' if content else '"Quote"'
            quote_p.font.size = Pt(32)
            quote_p.font.italic = True
            quote_p.alignment = PP_ALIGN.CENTER
            quote_p.font.color.rgb = text_color
            
            if slide_data.get("author"):
                author_tb = s.add_textbox(Inches(1.5), Inches(5.2), Inches(10), Inches(0.5))
                author_tf = author_tb.text_frame
                author_p = author_tf.paragraphs[0]
                author_p.text = f"— {slide_data['author']}"
                author_p.font.size = Pt(18)
                author_p.alignment = PP_ALIGN.CENTER
                author_p.font.color.rgb = accent_color
        
        elif tmpl == "comparison":
            left_items = bullets[:len(bullets)//2] if bullets else ["Pros"]
            right_items = bullets[len(bullets)//2:] if bullets else ["Cons"]
            
            for i, item in enumerate(left_items):
                tb = s.add_textbox(Inches(0.8), Inches(y_pos), Inches(6), Inches(0.5))
                tf = tb.text_frame
                p = tf.paragraphs[0]
                p.text = f"✓ {item}"
                p.font.size = Pt(18)
                p.font.color.rgb = accent_color
                y_pos += 0.5
            
            y_pos = 2.2
            for i, item in enumerate(right_items):
                tb = s.add_textbox(Inches(7), Inches(y_pos), Inches(6), Inches(0.5))
                tf = tb.text_frame
                p = tf.paragraphs[0]
                p.text = f"✗ {item}"
                p.font.size = Pt(18)
                p.font.color.rgb = RGBColor(255, 100, 100)
                y_pos += 0.5
        
        elif tmpl == "timeline":
            for i, item in enumerate(bullets[:5]):
                marker = s.add_shape(MSO_SHAPE.OVAL, Inches(1), Inches(y_pos), Inches(0.2), Inches(0.2))
                marker.fill.solid()
                marker.fill.fore_color.rgb = accent_color
                marker.line.fill.background()
                
                tb = s.add_textbox(Inches(1.5), Inches(y_pos), Inches(11), Inches(0.4))
                tf = tb.text_frame
                p = tf.paragraphs[0]
                p.text = str(item)
                p.font.size = Pt(16)
                p.font.color.rgb = text_color
                y_pos += 0.7
        
        else:
            for i, bullet in enumerate(bullets[:6]):
                tb = s.add_textbox(Inches(0.8), Inches(y_pos), Inches(11.5), Inches(0.5))
                tf = tb.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.text = f"• {bullet}"
                p.font.size = Pt(18)
                p.font.color.rgb = text_color
                y_pos += 0.45
    
    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()


st.markdown("""
<style>
    .main {background: #0a0a0f;}
    .stApp {background: linear-gradient(180deg, #0a0a0f 0%, #121218 100%);}
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2);
    }
    
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 12px;
        padding: 16px 24px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(99,102,241,0.3);
    }
    
    h1, h2, h3 {letter-spacing: -0.02em;}
    
    .gamma-hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
        border-radius: 24px;
        padding: 48px;
        text-align: center;
        margin-bottom: 32px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .gamma-hero h1 {
        font-size: 48px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
    }
    
    .gamma-hero p {
        color: rgba(255,255,255,0.6);
        font-size: 18px;
    }
    
    .template-badge {
        display: inline-block;
        background: rgba(99,102,241,0.2);
        color: #6366f1;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .animate-fade {
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)


def main():
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'theme' not in st.session_state:
        st.session_state.theme = "default"
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 24px 0;">
            <h2 style="margin: 0; font-size: 28px;">✨ Slider-Web</h2>
            <p style="color: #888; margin-top: 8px;">AI Presentations</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Create")
        
        topic = st.text_area(
            "What do you want to present?", 
            placeholder="e.g., The Future of AI in Healthcare",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            num_slides = st.selectbox("Slides", [4, 5, 6, 7, 8, 10, 12], index=2)
        with col2:
            theme = st.selectbox("Theme", list(PRESET_TONES.keys()), 
                                 format_func=lambda x: PRESET_TONES[x]["name"],
                                 index=0)
        
        st.session_state.theme = theme
        
        if st.button("✨ Generate", type="primary", use_container_width=True):
            if topic:
                st.session_state.generating = True
                with st.spinner("Creating your presentation..."):
                    slides = generate_gamma_style(topic, num_slides, theme, topic)
                    if slides:
                        st.session_state.slides = slides
                        st.session_state.generating = False
                        st.rerun()
            else:
                st.warning("Enter a topic")
        
        st.markdown("---")
        
        if st.session_state.slides:
            st.markdown(f"### 📑 {len(st.session_state.slides)} Slides")
            
            selected = st.radio("View", ["All", "Edit"], label_visibility="collapsed")
            
            if selected == "Edit" and st.session_state.slides:
                edit_idx = st.selectbox("Edit", range(len(st.session_state.slides)), 
                                     format_func=lambda x: f"Slide {x+1}")
                
                with st.expander("✏️ Edit Slide", expanded=True):
                    st.session_state.slides[edit_idx]["title"] = st.text_input("Title", st.session_state.slides[edit_idx].get("title", ""))
                    st.session_state.slides[edit_idx]["content"] = st.text_area("Content", st.session_state.slides[edit_idx].get("content", ""))
                    st.session_state.slides[edit_idx]["subtitle"] = st.text_input("Subtitle", st.session_state.slides[edit_idx].get("subtitle", ""))
                    
                    if st.button("💾 Save"):
                        st.success("Saved!")
            
            if st.button("🗑️ New Presentation"):
                st.session_state.slides = []
                st.rerun()
    
    if not st.session_state.slides:
        st.markdown("""
        <div class="gamma-hero animate-fade">
            <h1>✨ Create Stunning Presentations</h1>
            <p>Describe your idea and let AI generate beautiful, professional slides - instantly.</p>
            <p style="margin-top: 24px; color: #6366f1; font-size: 14px;">
                🎨 Professional themes • 📱 No downloads • ⚡ Instant results
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Quick Examples", unsafe_allow_html=True)
        
        examples = [
            "The Future of Artificial Intelligence",
            "How Blockchain Technology Works",
            "Climate Change Solutions 2025",
            "Startup Pitch Deck Template",
            "Product Launch Announcement",
        ]
        
        for ex in examples:
            if st.button(f"📝 {ex}"):
                st.session_state.slides = generate_gamma_style(ex, 6, "default", ex)
                if st.session_state.slides:
                    st.rerun()
    
    else:
        st.markdown("## ✨ Your Presentation")
        
        tone = PRESET_TONES.get(st.session_state.theme, PRESET_TONES["default"])
        
        for i, slide in enumerate(st.session_state.slides):
            with st.expander(f"Slide {i+1}: {slide.get('title', 'Untitled')[:40]}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{slide.get('title', '')}**")
                    st.markdown(f"_{slide.get('subtitle', '')}_" if slide.get("subtitle") else "")
                    st.markdown(f"```\n{slide.get('content', '')}\n```")
                with col2:
                    template = slide.get("template", "content")
                    st.markdown(f'<span class="template-badge">{template}</span>', unsafe_allow_html=True)
        
        st.markdown("### 📥 Download")
        
        c1, c2 = st.columns(2)
        
        with c1:
            pptx = export_gamma_pptx(st.session_state.slides, st.session_state.theme)
            st.download_button(
                "📊 Download PPTX",
                pptx,
                "presentation.pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                type="primary"
            )
        
        with c2:
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