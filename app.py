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


def generate_gamma_style(topic, num_slides, tone):
    client = get_groq_client()
    if not client:
        return None
    
    prompt = f"""Create a stunning presentation about: {topic}

Create {num_slides} slides in JSON format.

Include for each slide:
- type: slide type
- title: slide title
- content: main text (string or array)
- subtitle: brief subtitle

Return ONLY valid JSON array:
[
  {{"type": "title", "title": "Title", "content": "", "subtitle": "Tagline"}},
  {{"type": "content", "title": "Slide", "content": "Points", "subtitle": ""}},
  ...
]

No extra text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
        )
        return parse_slides(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def parse_slides(content):
    try:
        content = content.strip()
        start = content.find("[")
        end = content.rfind("]")
        if start >= 0 and end > start:
            content = content[start:end+1]
        slides = json.loads(content)
        if isinstance(slides, list):
            for s in slides:
                s.setdefault("type", "content")
                s.setdefault("title", "")
                s.setdefault("content", "")
                s.setdefault("subtitle", "")
            return slides
        return []
    except:
        return []


def export_pptx(slides, theme):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    
    tone = PRESET_TONES.get(theme, PRESET_TONES["default"])
    
    def mk_rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    
    accent = mk_rgb(tone["accent"])
    text_color = RGBColor(255, 255, 255) if tone != "minimal" else RGBColor(26, 26, 26)
    
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    for sd in slides:
        tmpl = sd.get("type", "content")
        cont = sd.get("content", "")
        if isinstance(cont, list):
            bullets = cont
        else:
            bullets = cont.split("\n") if cont else []
        
        s = prs.slides.add_slide(prs.slide_layouts[6])
        
        title = sd.get("title", "Slide")
        
        tb = s.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = text_color
        
        sub = sd.get("subtitle", "")
        if sub:
            sb = s.add_textbox(Inches(0.5), Inches(1.1), Inches(12), Inches(0.5))
            sf = sb.text_frame
            sp = sf.paragraphs[0]
            sp.text = sub
            sp.font.size = Pt(14)
            sp.font.color.rgb = accent
        
        y = 1.8
        for b in bullets[:6]:
            bb = s.add_textbox(Inches(0.5), Inches(y), Inches(12), Inches(0.5))
            bf = bb.text_frame
            bf.word_wrap = True
            bp = bf.paragraphs[0]
            bp.text = "- " + str(b)
            bp.font.size = Pt(16)
            bp.font.color.rgb = text_color
            y += 0.4
    
    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()


st.markdown("""
<style>
    .stApp {background: linear-gradient(180deg, #0a0a0f 0%, #121218 100%);}
    div[data-testid="stSidebar"] {background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);}
    .stTextInput > div > div > input {background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px;}
    div.stButton > button {background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border: none; border-radius: 12px; padding: 16px 24px; font-weight: 600;}
    .gamma-hero {background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%); border-radius: 24px; padding: 48px; text-align: center; margin-bottom: 32px;}
    .gamma-hero h1 {font-size: 48px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
</style>
""", unsafe_allow_html=True)


def main():
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'theme' not in st.session_state:
        st.session_state.theme = "default"
    
    with st.sidebar:
        st.markdown("## ✨ Slider-Web")
        
        topic = st.text_area("What do you want to present?", placeholder="e.g., The Future of AI", height=80)
        
        col1, col2 = st.columns(2)
        with col1:
            num_slides = st.selectbox("Slides", [4, 5, 6, 7, 8, 10], index=2)
        with col2:
            theme = st.selectbox("Theme", list(PRESET_TONES.keys()), format_func=lambda x: PRESET_TONES[x]["name"])
        
        st.session_state.theme = theme
        
        if st.button("✨ Generate", type="primary", use_container_width=True):
            if topic:
                with st.spinner("Creating..."):
                    slides = generate_gamma_style(topic, num_slides, theme)
                    if slides:
                        st.session_state.slides = slides
                        st.rerun()
            else:
                st.warning("Enter a topic")
        
        if st.session_state.slides:
            if st.button("🗑️ New", use_container_width=True):
                st.session_state.slides = []
                st.rerun()
    
    if not st.session_state.slides:
        st.markdown("""
        <div class="gamma-hero">
            <h1>✨ Create Presentations</h1>
            <p>Describe your idea and AI generates beautiful slides.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("## ✨ Your Presentation")
        
        for i, slide in enumerate(st.session_state.slides):
            with st.expander(f"Slide {i+1}: {slide.get('title', 'Untitled')[:50]}"):
                st.markdown(f"**{slide.get('title', '')}**")
                st.markdown(f"_{slide.get('subtitle', '')}_")
                c = slide.get("content", "")
                if isinstance(c, list):
                    for x in c:
                        st.markdown(f"- {x}")
                else:
                    st.markdown(c)
        
        st.markdown("### 📥 Download")
        
        pptx_data = export_pptx(st.session_state.slides, st.session_state.theme)
        st.download_button(
            "📊 Download PPTX",
            pptx_data,
            "presentation.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
            type="primary"
        )


if __name__ == "__main__":
    main()