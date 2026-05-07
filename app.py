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
- type: the slide type
- title: slide title
- content: main text/points (can be array)
- subtitle: brief subtitle
- template: which template to use

Choose templates naturally:
- First slide = title
- For big ideas/stats = stats  
- For quotes = quote
- For comparisons = comparison
- For history = timeline
- Regular content = content or bullets

Include fields:
- type
- title  
- content (main text)
- subtitle
- template

Return ONLY valid JSON:
[
  {{"type": "title", "title": "Title", "content": "", "subtitle": "Tagline", "template": "title"}},
  {{"type": "content", "title": "Slide Title", "content": "Key points", "template": "content"}},
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


def export_simple_pptx(slides, theme):
    """Simple PPTX export without complex shapes"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    
    tone = PRESET_TONES.get(theme, PRESET_TONES["default"])
    
    def hex_rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    
    accent_color = hex_rgb(tone["accent"])
    text_color = RGBColor(255, 255, 255) if tone != "minimal" else RGBColor(26, 26, 26)
    
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
        
        title = slide_data.get("title", "Slide")
        
        title_tb = s.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(1))
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_p = title_tf.paragraphs[0]
        title_p.text = title
        title_p.font.size = Pt(36)
        title_p.font.bold = True
        title_p.font.color.rgb = text_color
        
        sub = slide_data.get("subtitle", "")
        if sub:
            sub_tb = s.add_textbox(Inches(0.8), Inches(1.2), Inches(11.5), Inches(0.5))
            sub_tf = sub_tb.text_frame
            sub_p = sub_tf.paragraphs[0]
            sub_p.text = sub
            sub_p.font.size = Pt(16)
            sub_p.font.color.rgb = accent_color
        
        if tmpl == "title":
            title_tb.top = Inches(2.5)
            title_tb.left = Inches(1)
            subtitle_box = s.add_textbox(Inches(1), Inches(4), Inches(11.333), Inches(1))
            subtitle_tf = subtitle_box.text_frame
            subtitle_p = subtitle_tf.paragraphs[0]
            subtitle_p.text = sub if sub else title
            subtitle_p.font.size = Pt(24)
            subtitle_p.alignment = PP_ALIGN.CENTER
            subtitle_p.font.color.rgb = accent_color
        
        elif tmpl == "stats":
            stat_text = str(slide_data.get("content", "85%"))
            stat_tb = s.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(2))
            stat_tf = stat_tb.text_frame
            stat_p = stat_tf.paragraphs[0]
            stat_p.text = stat_text
            stat_p.font.size = Pt(72)
            stat_p.font.bold = True
            stat_p.alignment = PP_ALIGN.CENTER
            stat_p.font.color.rgb = accent_color
        
        else:
            y_pos = 2.0
            for bullet in bullets[:6]:
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
    }
    
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
    }
    
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 12px;
        padding: 16px 24px;
        font-size: 16px;
        font-weight: 600;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(99,102,241,0.3);
    }
    
    .gamma-hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
        border-radius: 24px;
        padding: 48px;
        text-align: center;
        margin-bottom: 32px;
    }
    
    .gamma-hero h1 {
        font-size: 48px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)


def main():
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'theme' not in st.session_state:
        st.session_state.theme = "default"
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 24px 0;">
            <h2 style="margin: 0;">✨ Slider-Web</h2>
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
                with st.spinner("Creating your presentation..."):
                    slides = generate_gamma_style(topic, num_slides, theme, topic)
                    if slides:
                        st.session_state.slides = slides
                        st.rerun()
            else:
                st.warning("Enter a topic")
        
        st.markdown("---")
        
        if st.session_state.slides:
            st.markdown(f"### 📑 {len(st.session_state.slides)} Slides")
            
            if st.button("🗑️ New Presentation"):
                st.session_state.slides = []
                st.rerun()
    
    if not st.session_state.slides:
        st.markdown(f"""
        <div class="gamma-hero">
            <h1>✨ Create Stunning Presentations</h1>
            <p>Describe your idea and let AI generate beautiful slides - instantly.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Quick Examples")
        
        examples = [
            "The Future of Artificial Intelligence",
            "How Blockchain Technology Works",
            "Climate Change Solutions 2025",
        ]
        
        for ex in examples:
            if st.button(f"📝 {ex}"):
                slides = generate_gamma_style(ex, 6, "default", ex)
                if slides:
                    st.session_state.slides = slides
                    st.rerun()
    
    else:
        st.markdown("## ✨ Your Presentation")
        
        for i, slide in enumerate(st.session_state.slides):
            with st.expander(f"Slide {i+1}: {slide.get('title', 'Untitled')[:50]}", expanded=False):
                st.markdown(f"**{slide.get('title', '')}**")
                st.markdown(f"_{slide.get('subtitle', '')}_" if slide.get("subtitle") else "")
                content = slide.get("content", "")
                if isinstance(content, list):
                    for c in content:
                        st.markdown(f"- {c}")
                else:
                    st.markdown(content)
        
        st.markdown("### 📥 Download")
        
        pptx = export_simple_pptx(st.session_state.slides, st.session_state.theme)
        st.download_button(
            "📊 Download PPTX",
            pptx,
            "presentation.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
            type="primary"
        )


if __name__ == "__main__":
    main()