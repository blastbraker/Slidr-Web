# Slider-Web

AI Presentation Maker - Free Web App, No Downloads

## Features

- **10 Slide Layouts**: Title, Content, Bullets+Image, Two Column, Divider, Quote, Statistic, Comparison, Timeline, Full Image
- **AI Auto-Layout**: AI automatically selects the best layout for each slide
- **Live Preview**: Real-time slide preview with reveal.js
- **Professional Editor**: Edit slides with dynamic fields per layout
- **Export**: Download as PPTX or HTML
- **Free**: Everything is free - AI, hosting, no downloads

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set Groq API key (free at console.groq.com)
export GROQ_API_KEY="your-groq-api-key"

# Run the app
streamlit run app.py
```

### Deployment (Streamlit Cloud)

1. Push to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repo
4. Click "Deploy"
5. Add secrets:
   - `GROQ_API_KEY` = your Groq API key (get free at console.groq.com)

## Getting a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card required)
3. Click "API Keys" → "Create Key"
4. Copy the key and add to Streamlit Cloud secrets

## Usage

1. Enter a topic (e.g., "History of Artificial Intelligence")
2. Select number of slides
3. Click "Generate"
4. Edit slides in the editor
5. View live preview
6. Export as PPTX or HTML

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | Streamlit |
| Slide Editor | streamlit-reveal-slides |
| AI | Groq (free tier) |
| Export | python-pptx |
| Hosting | Streamlit Cloud (free) |

## Rate Limits

Free Groq tier: 30 requests/minute, 6,000 tokens/minute, 500,000 tokens/day

## License

MIT License - See LICENSE file for details.

## Author

Ali Bahar