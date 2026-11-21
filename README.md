# ✂️ AutoClipperYT

> **Turn any long-form video into viral 9:16 YouTube Shorts — fully automated, GPU-accelerated, one-click upload.**

Built and maintained by **[Kundhan](https://github.com/Kundhan0)**

---

## 🚀 What It Does

AutoClipperYT takes any video (talk, podcast, gaming stream, vlog) and automatically:

1. **GPU Transcribes** it word-by-word using Faster-Whisper on your RTX GPU
2. **AI Scores** every moment via a local AI Gateway (Gemini / Claude compatible) to find the highest-virality hooks
3. **Reframes** to 9:16 vertical with smooth face-tracking and punch-in zoom
4. **Burns Karaoke Captions** (Hormozi-style) with word-by-word highlight in one encode pass
5. **Publishes to YouTube Shorts** in one click with AI-generated title, description and tags

---

## ✨ Key Features I Built

| Feature | What It Does |
|---|---|
| 🎯 **AI Hook Detection** | Custom gateway routing — sends transcript to Gemini Flash Lite (via Claude-compatible API), gets JSON clips with virality scores |
| 🖥️ **CUDA GPU Pipeline** | Patched ctranslate2/faster-whisper to find `cublas64_12.dll` from PyTorch's lib dir on Windows — no separate NVIDIA wheel needed |
| 📱 **9:16 Auto-Reframe** | Face detection (YuNet ONNX + OpenCV Haar fallback) with forward+backward EMA smoothing so the camera glides |
| 🔤 **Animated Captions** | Word-level karaoke, boxed, or bold style — burned directly in the reframe pass (1 FFmpeg encode, not 2) |
| ▶️ **1-Click YouTube Upload** | OAuth2 flow, AI-generated metadata via gateway, privacy selector, resumable upload |
| 🌐 **3D Hero UI** | Three.js WebGL hero on the frontend with floating 16:9 timeline, laser slicing blades, and pop-out 9:16 phone cards |
| 🔇 **Silence Trimming** | Pure word-timestamp-based silence removal — no extra audio decode pass needed |
| 🎬 **B-roll Cutaways** | Optional Pexels stock video overlays triggered on content keywords |
| ♻️ **Per-Clip Regeneration** | Re-render any single clip with new settings without re-processing the whole video |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Transcription** | faster-whisper (ctranslate2) · RTX 5070 Ti GPU |
| **AI Scoring** | Local Gateway (Anthropic Messages API compatible) → Gemini Flash Lite |
| **Video Processing** | FFmpeg (NVENC GPU encode), OpenCV (face tracking) |
| **Captions** | ASS subtitle format, burned via FFmpeg |
| **YouTube API** | google-api-python-client, OAuth2 |
| **Frontend** | Vanilla HTML/CSS/JS + Three.js (CDN) for 3D WebGL hero |

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- FFmpeg on PATH (`winget install Gyan.FFmpeg` on Windows)
- NVIDIA GPU recommended (RTX series) — CPU fallback works too
- A local AI Gateway running at `http://127.0.0.1:8000` (Anthropic Messages API compatible)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Kundhan0/AutoClipperYT.git
cd AutoClipperYT

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env — set GATEWAY_URL, WHISPER_MODEL, etc.

# 5. YouTube OAuth (optional — only needed for upload feature)
# Place your client_secret.json in the project root
# Run the app once and complete the browser OAuth flow

# 6. Start the server
python app.py
```

Open **http://localhost:8765** in your browser.

---

## 🎮 How to Use

1. **Drop a video** onto the upload zone (MP4, MOV, MKV)
2. **Choose settings** — aspect ratio, caption style, layout, clip length, number of clips
3. **Watch** the 5-stage pipeline: Listen → Select → Reframe → Caption → Export
4. **Download** any clip or click **▶ Upload** to publish directly to YouTube Shorts

---

## 🏎️ Performance (RTX 5070 Ti Laptop)

| Stage | Time (60-min video) |
|---|---|
| GPU Transcription (base.en) | ~45 seconds |
| AI Hook Scoring | ~3 seconds |
| Reframe + Captions (6 clips) | ~90 seconds |
| **Total** | **~2.5 minutes** |

---

## 🙏 Acknowledgements & Inspiration

This project was inspired by **[Steezy-code/clipper](https://github.com/Steezy-code/clipper)** — a great foundational concept for local clip generation.

AutoClipperYT is a **complete architectural overhaul** I built on top of that concept, adding:
- Custom AI Gateway routing (replacing Ollama with a Claude/Gemini-compatible API)
- Full YouTube OAuth2 upload pipeline
- CUDA Windows DLL patching for GPU transcription
- 3D animated frontend hero (Three.js WebGL)
- Per-clip regeneration without re-processing
- Silence trimming from pure word timestamps
- B-roll cutaway system via Pexels API
- Production-grade FastAPI server architecture

---

## 🛡️ Disclaimer

This software is developed for personal, educational, and content creation workflows. Users are responsible for adhering to YouTube's Terms of Service and respecting original copyright when processing and uploading third-party media. Provided "as is" without warranties of any kind.
