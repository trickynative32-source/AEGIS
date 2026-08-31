# AEGIS — Assisted Executive Guidance and Intelligence System

**SIH Domain**: SIH2611 — Assistive Technologies and Inclusive Innovation  
**Problem Statement ID**: SIH26204  
**Problem Statement**: AI-Powered Personal Assistant for Proactive Daily Task Automation and Inclusive Accessibility

---

## 🌟 Overview

**AEGIS** is an agentic Windows AI Personal Assistant that combines the conversational intelligence of **ChatGPT**, the voice/HUD personality of **JARVIS**, the operating system integration of **Windows Copilot**, real-time **Computer-Use Automation**, **Advanced Environmental Vision & Spatial Memory**, and **Inclusive Accessibility**.

Users can speak or type naturally without memorizing commands:
- *"What time is it?"* → Exact Windows system clock
- *"Open Paint and draw a house"* → Autonomous MS Paint canvas illustration
- *"Play Believer by Imagine Dragons"* → Direct YouTube playback
- *"Give me directions to Bangalore Airport"* → Google Maps with auto-resolved location
- *"Create a Python calculator on my Desktop"* → Generates complete working `.py` file
- *"Where is the clock?"* → Queries short-term spatial visual memory
- *"Remind me tomorrow at 5 PM to submit my assignment"* → User-defined reminder with real-time countdown
- *"Start dictation"* → Continuous speech transcription & Word/Docx generation
- *"Goodbye"* → Polite farewell & clean self-shutdown

---

## 🏗 Architecture

```
                                  ┌─────────────────────────────────────────┐
                                  │   AEGIS Desktop UI (React + Tailwind)   │
                                  │  - HUD / Push-to-Talk / Live Clock      │
                                  │  - Chatbox / Camera Active Preview      │
                                  │  - Visual Memory / Reminders / Routines │
                                  │  - Accessibility (High-Contrast/Dyslexia│
                                  └────────────────────┬────────────────────┘
                                                       │ WebSocket (/ws) & REST
                                                       ▼
                                  ┌─────────────────────────────────────────┐
                                  │           FastAPI Core Engine           │
                                  └────────────────────┬────────────────────┘
                                                       │
        ┌───────────────────┬──────────────────────────┼──────────────────────────┬───────────────────┐
        ▼                   ▼                          ▼                          ▼                   ▼
┌──────────────┐    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐    ┌──────────────┐
│  Perception  │    │  Intel Router│           │Visual Memory │           │Tool Registry │    │Assistant Svc │
├──────────────┤    ├──────────────┤           ├──────────────┤           ├──────────────┤    ├──────────────┤
│• Microphone  │    │• Determin-   │           │• Scene Det   │           │• App Finder  │    │• Real Clock  │
│  (VAD / STT) │    │  istic Fast  │           │• Object &    │           │• MS Paint    │    │• Reminders   │
│• Web Audio   │    │  Local Path  │           │  Spatial Rel │           │• Browser     │    │  (Strictly   │
│• Camera      │    │• OpenRouter  │           │• Semantic    │           │• YouTube     │    │   User-Def)  │
│  (OpenCV)    │    │  LLM Agent   │           │  Retrieval   │           │• Google Maps │    │• Routines    │
│• Screen Capture│  │• Web Search  │           │• Expiration  │           │• File Engine │    │• Memory      │
│  (mss)       │    │  (DuckDuckGo)│           │  & Updates   │           │• PyAutoGUI   │    │• SAPI / Edge │
└──────────────┘    └──────────────┘           └──────────────┘           └──────────────┘    │  TTS Engine  │
                                                                                              └──────────────┘
```

---

## 🚀 Key Capabilities

### 1. Real Windows System Clock & Telemetry
- Connected directly to Windows local system time (`datetime.now()`).
- Live independent digital clock with seconds, date, and synchronization badge.
- Zero LLM hallucination for time and date queries.

### 2. Environmental Vision & Spatial Visual Memory
- **Camera OFF by default** with a prominent glowing `CAMERA ACTIVE` indicator when enabled.
- **Continuous 24/7 Mode**: Real-time OpenCV video stream with local person/face detection.
- **Short-Term Spatial Visual Memory**: Stores compact semantic representations of objects and their spatial relationships (`left`, `right`, `above`, `below`, `on`, `under`, `beside`, `near the window`, `on the blue wall`) without storing raw video.
- Answers visual memory queries naturally: *"Where is my laptop?"* → *"It's on the table near the window."*

### 3. Microsoft Paint Drawing Automation
- Dynamically finds the MS Paint window and canvas dimensions.
- Executes smooth coordinate mouse strokes for structured illustrations: `house`, `circle/sun`, `landscape`, `birthday_card`, `aura_text`, `geometric`.

### 4. Application Discovery & Windows Control
- Discovers installed Windows applications from Start Menu shortcuts (`.lnk`), Program Files, and Registry.
- Supports aliases: `Chrome`, `VS Code`, `Spotify`, `Discord`, `WhatsApp`, `Notepad`, `Paint`, `Calculator`, `File Explorer`, `Settings`, `Terminal`, `Word`, `Excel`, `PowerPoint`, `Downloads`, `Desktop`.

### 5. Multi-Format File Generation & Dictation
- Generates complete working files: `TXT`, `MD`, `PY`, `JS`, `TS`, `HTML`, `CSS`, `SQL`, `JSON`, `CSV`, `DOCX`, `PPTX`, `XLSX`.
- Includes **Dictation Mode**: continuous speech-to-text recording, formatting into Word documents or code.
- Overwrite safety protection: warns before overwriting existing files.

### 6. Strictly User-Defined Reminders
- Reminders are strictly user-defined and anchored to the local system clock.
- If no time is specified (*"Remind me to submit assignment"*), AURA asks *"When should I remind you?"*.
- Background scheduler checks reminders every 3 seconds and fires push alerts + speech notifications.

### 7. SIH Inclusive Accessibility
- **High-Contrast Mode**: Crisp black/cyan color scheme.
- **Large Text Mode**: Enlarged UI fonts.
- **OpenDyslexic Font**: Dyslexia-friendly reading.
- **Voice-First Mode**: Automatic spoken readouts with speech interruption (barge-in).
- **Simplified UI Mode**: Low cognitive load layout.

---

## 📦 Installation & Quick Start

### Prerequisites
- Windows 10 / 11
- Python 3.10+
- Node.js 18+ (for building frontend)

### 1. Configure Environment
Copy `.env.example` to `.env` and set your OpenRouter API key (optional for online mode):
```bash
copy .env.example .env
```

### 2. Start AURA
Double-click `run_aura.bat` or run:
```powershell
.\run_aura.bat
```
Or via PowerShell:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open **http://127.0.0.1:8000** in your browser.

---

## 🧪 Testing Commands (SIH Evaluation)

| Command | Expected Action |
|---|---|
| `"What time is it?"` | Reads exact Windows system clock |
| `"What date is today?"` | Reads current system day and date |
| `"Open Chrome"` | Launches Google Chrome |
| `"Open Paint and draw a house"` | Launches MS Paint and draws a house on canvas |
| `"Play Believer by Imagine Dragons"` | Opens and plays track on YouTube |
| `"Give me directions to Bangalore Airport"` | Opens Google Maps with auto-resolved origin |
| `"Create a Python calculator on my Desktop"` | Generates working `calculator.py` on Desktop |
| `"Turn on the camera"` | Activates webcam feed & displays `CAMERA ACTIVE` HUD |
| `"What do you see?"` | Analyzes environment & populates visual memory |
| `"Where is the clock?"` | Answers from remembered spatial visual memory |
| `"Is there a person in front of me?"` | Runs local person presence detector |
| `"Remind me to submit assignment"` | Asks: *"When should I remind you?"* |
| `"Remind me tomorrow at 5 PM to submit assignment"` | Sets reminder & starts live countdown |
| `"Start dictation"` | Begins continuous transcription |
| `"Goodbye"` | Speaks farewell & closes AURA application safely |

---

## 🔒 Safety & Privacy Principles
1. **No Unrestricted Shell**: Actions run through a typed, validated tool registry.
2. **Local Vision Processing**: No continuous video uploaded to cloud; frames processed selectively.
3. **Graceful Self-Shutdown**: AURA only terminates its own processes, never triggering Windows OS shutdowns.
4. **Offline Capability**: Core features (clock, app launching, files, local person detection, pyttsx3 speech, reminders) run 100% offline.
