---
title: AI Quiz Solver - Multi-Agent System
---

# AI Quiz Solver - Autonomous Multi-Agent System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.3+-green.svg)](https://fastapi.tiangolo.com/)

An intelligent, autonomous agent built with LangGraph and LangChain that solves complex data science quizzes involving web scraping, multimodal analysis, data processing, machine learning, and visualization. The system uses a **dual AI architecture** with Aipipe/OpenRouter (gpt-5-nano) for reasoning and Google Gemini for multimodal tasks.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [AI Models & Routing](#ai-models--routing)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Tools & Capabilities](#tools--capabilities)
- [Docker Deployment](#docker-deployment)
- [How It Works](#how-it-works)
- [Rate Limiting & Fallback](#rate-limiting--fallback)
- [License](#license)

## 🔍 Overview

This project was developed for the TDS (Tools in Data Science) course project, where the objective is to build an application that can autonomously solve multi-step quiz tasks involving:

- **Data sourcing**: Web scraping, API calls, file downloads
- **Multimodal analysis**: Audio transcription, image analysis, PDF extraction, video processing
- **Data preparation**: Cleaning, transformation, feature engineering
- **Data analysis**: Statistical analysis, ML models, predictions
- **Data visualization**: Charts, graphs, dashboards with matplotlib/plotly
- **Code generation**: Dynamic Python code for complex computations

The system receives quiz URLs via a REST API, navigates through multiple quiz pages, solves each task using intelligent AI routing and specialized tools, and submits answers back to the evaluation server - all within a 3-minute time limit per quiz.

## 🏗️ Architecture

The project uses a **dual AI architecture** with automatic failover:

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Server                       │
│              Receives POST /solve requests               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Agent Orchestrator                │
│                                                           │
│  ┌──────────────────┐         ┌────────────────────┐   │
│  │  PRIMARY LLM     │ FALLBACK│   BACKUP LLM       │   │
│  │  Aipipe/GPT-5-nano  │────────>│   Google Gemini    │   │
│  │  (Reasoning)     │         │   (Rate limit)     │   │
│  └────────┬─────────┘         └────────────────────┘   │
│           │                                              │
│           │ Decides which tool to use                   │
└───────────┼──────────────────────────────────────────────┘
            │
            ├───────┬───────┬───────┬───────┬──────────┐
            ▼       ▼       ▼       ▼       ▼          ▼
      ┌─────────┐ ┌────┐ ┌─────┐ ┌────┐ ┌─────┐ ┌────────┐
      │Scraper  │ │Code│ │API  │ │Down│ │Deps │ │Gemini  │
      │(Playwrg)│ │Exec│ │Calls│ │load│ │Inst.│ │Tools   │
      └─────────┘ └────┘ └─────┘ └────┘ └─────┘ └────────┘
                                                   │
                                         ┌─────────┴─────────┐
                                         ▼                   ▼
                                   transcribe_audio   analyze_with_gemini
                                   (Audio → Text)     (Images, PDFs, Videos)
```

### Key Components:

1. **FastAPI Server** (`main.py`): HTTP endpoint for quiz submissions
2. **LangGraph Agent** (`agent.py`): State machine with dual AI + automatic fallback
3. **Primary LLM**: Aipipe/OpenRouter (GPT-5-nano) - cheap, fast reasoning
4. **Fallback LLM**: Google Gemini 2.0 Flash - automatic failover on rate limits
5. **Multimodal Tools**: Gemini-powered audio, image, PDF, video analysis
6. **Execution Tools**: Python code runner, web scraper, file handlers

## ✨ Features

- ✅ **Dual AI architecture**: GPT-5-nano (primary) + Gemini (fallback + multimodal)
- ✅ **Automatic failover**: Seamlessly switches from Aipipe → Gemini on rate limits
- ✅ **Multimodal analysis**: Audio transcription, image/video/PDF analysis
- ✅ **Autonomous multi-step solving**: Chains together unlimited quiz pages
- ✅ **Dynamic JavaScript rendering**: Playwright for SPA/React pages
- ✅ **Code generation & execution**: Writes Python for data analysis, ML, viz
- ✅ **Self-installing dependencies**: Auto-installs pandas, numpy, sklearn, etc.
- ✅ **Time-optimized**: Minimal waits (2s max) to respect 3-minute deadline
- ✅ **Rate limiting**: Intelligent throttling for both APIs
- ✅ **Docker ready**: Containerized for HuggingFace Spaces deployment

## 🤖 AI Models & Routing

### Primary: Aipipe/OpenRouter - GPT-5-nano
- **Purpose**: Main reasoning engine, code generation, text analysis
- **Cost**: ~$0.15 per 1M tokens (20x cheaper than Claude)
- **Rate Limit**: 9 requests per minute
- **Use Cases**: 
  - Planning and decision making
  - Python code generation
  - Data analysis logic
  - JSON/text parsing
  - Mathematical calculations

### Backup: Google Gemini 2.0 Flash
- **Purpose**: Fallback on rate limits + LLM reasoning
- **Cost**: Free tier (15 RPM)
- **Rate Limit**: 1 request per 5 seconds (with retries)
- **Use Cases**:
  - Takes over when Aipipe hits rate limit
  - Same reasoning capabilities as Aipipe
  - Can call all the same tools

### Multimodal: Gemini Tools (REST API)
- **Tools**: `transcribe_audio`, `analyze_with_gemini`
- **Capabilities**:
  - Audio transcription (MP3, WAV, etc.)
  - Image analysis (charts, diagrams, photos)
  - PDF text extraction
  - Video analysis
- **Implementation**: Direct REST API calls with base64 inline data
- **Why**: Both Aipipe and Gemini LLMs call these tools for multimodal content

### Intelligent Routing Logic

The agent **reads quiz instructions first**, then chooses tools based on what's required:

**Example 1: Audio Transcription Task**
```
Quiz page: "Transcribe the audio file"
    ↓
1. Aipipe scrapes quiz page
2. Reads instruction: "Transcribe the audio file"
3. Finds audio URL on page
4. Calls: transcribe_audio(url)
    ↓
5. Gemini API returns: "Hello, my name is John"
6. Aipipe submits: "Hello, my name is John"
```

**Example 2: Audio + Analysis Task**
```
Quiz page: "Listen to audio and sum all numbers"
    ↓
1. Aipipe scrapes quiz page
2. Reads instruction: "sum all numbers"
3. Calls: transcribe_audio(url)
    ↓
4. Gemini returns: "The values are 5, 10, and 15"
5. Aipipe extracts numbers: [5, 10, 15]
6. Aipipe calculates: 5 + 10 + 15 = 30
7. Submits: 30
```

**Example 3: Data Analysis Task**
```
Quiz page: "Analyze CSV and create bar chart"
    ↓
1. Aipipe reads instructions
2. Downloads CSV with download_file()
3. Generates Python code (pandas + matplotlib)
4. Calls run_code() to execute
5. Code creates chart.png
6. Submits the file
```

**Key Point**: The agent doesn't assume what to do - it **follows quiz instructions exactly**.

## 📁 Project Structure

```
LLM-Analysis-TDS-Project-2/
├── agent.py                    # LangGraph with dual AI + fallback
├── main.py                     # FastAPI server
├── pyproject.toml              # Dependencies
├── Dockerfile                  # Container with Playwright
├── .env                        # Environment variables
├── tools/
│   ├── __init__.py             # Tool exports
│   ├── web_scraper.py          # Playwright HTML renderer
│   ├── run_code.py             # Python code executor
│   ├── download_file.py        # File downloader
│   ├── send_request.py         # POST/GET API calls
│   ├── add_dependencies.py     # Package installer
│   ├── transcribe_audio.py     # Audio → text (Gemini)
│   ├── analyze_with_gemini.py  # Images/PDFs/videos (Gemini)
│   ├── aipipe_client.py        # Aipipe helper
│   └── gemini_client.py        # Gemini helper
└── README.md
```

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/Atulmishra22/llm-quiz-solver.git
cd llm-quiz-solver
```

### Step 2: Install Dependencies

```bash
# Install uv if needed
pip install uv

# Sync dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium
```

### Step 3: Start the Server

```bash
uv run main.py
```

The server will start at `http://0.0.0.0:7860`.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
# Your credentials
EMAIL=your.email@example.com
SECRET=your_secret_string

# Aipipe/OpenRouter API Key
AIPIPE_API_KEY=your_aipipe_key_here

# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_key_here
```

### Getting API Keys

**Aipipe/OpenRouter:**
1. Sign up at [aipipe.org](https://aipipe.org)
2. Get your API key from dashboard
3. Add credits (GPT-5-nano is very cheap)

**Google Gemini:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Free tier: 15 RPM, 1500 RPD

## 🚀 Usage

### Testing the Endpoint

```bash
curl -X POST http://localhost:7860/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "secret": "your_secret_string",
    "url": "https://tds-llm-analysis.s-anand.net/demo-audio?email=your.email@example.com&id=123"
  }'
```

**PowerShell:**
```powershell
$body = @{
  email = "your.email@example.com"
  secret = "your_secret_string"
  url = "https://tds-llm-analysis.s-anand.net/demo-audio?email=your.email@example.com&id=123"
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:7860/solve' -Method Post -Body $body -ContentType 'application/json'
```

Expected response:
```json
{
  "status": "ok"
}
```

## 🌐 API Endpoints

### `POST /solve`

Triggers the autonomous quiz-solving agent.

**Request:**
```json
{
  "email": "your.email@example.com",
  "secret": "your_secret_string",
  "url": "https://example.com/quiz-url"
}
```

**Responses:**

| Code | Description |
|------|-------------|
| 200  | Agent started successfully |
| 403  | Invalid secret |
| 400  | Invalid request format |

### `GET /healthz`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## 🛠️ Tools & Capabilities

### 1. **Web Scraper** (`get_rendered_html`)
- Playwright-based JavaScript rendering
- Waits for network idle
- Returns fully rendered HTML

### 2. **Code Executor** (`run_code`)
- Runs Python code in subprocess
- Returns stdout/stderr
- Used for data analysis, ML, visualization

### 3. **File Downloader** (`download_file`)
- Downloads files from URLs
- Saves to `LLMFiles/` directory
- Supports all file types

### 4. **API Caller** (`post_request`, `get_request`)
- POST/GET HTTP requests
- Custom headers support
- JSON payload handling

### 5. **Package Installer** (`add_dependencies`)
- Installs Python packages dynamically
- Uses `uv add` for speed
- Auto-resolves dependencies

### 6. **Audio Transcriber** (`transcribe_audio`)
- Gemini-powered audio → text
- Supports MP3, WAV, etc.
- Base64 inline data upload

### 7. **Multimodal Analyzer** (`analyze_with_gemini`)
- Images: Charts, diagrams, photos
- PDFs: Text extraction
- Videos: Content analysis
- Custom prompts supported

## 🐳 Docker Deployment

### Build & Run

```bash
# Build
docker build -t llm-analysis-agent .

# Run
docker run -p 7860:7860 \
  -e EMAIL="your.email@example.com" \
  -e SECRET="your_secret" \
  -e AIPIPE_API_KEY="your_aipipe_key" \
  -e GOOGLE_API_KEY="your_gemini_key" \
  llm-analysis-agent
```

### Deploy to HuggingFace Spaces

1. Create Docker Space
2. Push repository
3. Add secrets in Settings:
   - `EMAIL`
   - `SECRET`
   - `AIPIPE_API_KEY`
   - `GOOGLE_API_KEY`

## 🧠 How It Works

### 1. Request Reception
- FastAPI validates secret
- Returns 200 OK immediately
- Starts agent in background (non-blocking)

### 2. Agent Loop

```
┌──────────────────────────────────────┐
│ 1. Aipipe LLM analyzes task          │
│    - Reads quiz instructions         │
│    - Plans which tool to use         │
└───────────────┬──────────────────────┘
                ▼
┌──────────────────────────────────────┐
│ 2. Tool execution                    │
│    - Scrapes page / downloads        │
│    - Calls Gemini tools for audio    │
│    - Runs Python code for analysis   │
│    - Submits answer                  │
└───────────────┬──────────────────────┘
                ▼
┌──────────────────────────────────────┐
│ 3. Response evaluation               │
│    - Checks server response          │
│    - Extracts next quiz URL          │
└───────────────┬──────────────────────┘
                ▼
┌──────────────────────────────────────┐
│ 4. Decision                          │
│    - New URL? → Continue loop        │
│    - No URL? → Return "END"          │
└──────────────────────────────────────┘
```

### 3. Intelligent Task Routing

**Text/Code Tasks:**
- Aipipe generates Python code
- `run_code` executes it
- Aipipe formats answer

**Audio Tasks:**
- Aipipe calls `transcribe_audio`
- Gemini API transcribes
- Aipipe processes transcription

**Image Tasks:**
- Aipipe calls `analyze_with_gemini`
- Gemini analyzes image
- Aipipe uses analysis

**Data Analysis:**
- Aipipe generates pandas/numpy code
- `run_code` executes analysis
- Results returned to Aipipe

## ⚡ Rate Limiting & Fallback

### Primary: Aipipe (GPT-5-nano)
- **Limit**: 9 requests per minute
- **Mechanism**: `InMemoryRateLimiter`
- **On failure**: Switches to Gemini

### Fallback: Gemini 2.0 Flash
- **Limit**: 1 request per 5 seconds
- **Retries**: Up to 5 attempts
- **Wait time**: 2 seconds on 429 error

### Optimization for 3-Minute Deadline
- **No waits** before fallback (instant switch)
- **2s retry** on Gemini rate limit (minimal)
- **Fail fast** if both APIs exhausted
- Saves up to **35 seconds per fallback**

### Fallback Flow

```
Aipipe request
    │
    ├─ Success → Continue
    │
    ├─ Rate limit (429) → Switch to Gemini instantly
    │                           │
    │                           ├─ Success → Continue
    │                           │
    │                           ├─ Also 429 → Wait 2s → Retry once
    │                                              │
    │                                              ├─ Success → Continue
    │                                              └─ Fail → Raise error
```

## 📝 Key Design Decisions

1. **Dual AI**: Aipipe (cheap) + Gemini (fallback + multimodal)
2. **GPT-5-nano over Claude**: 20x cheaper, prevents token exhaustion
3. **REST API for multimodal**: Avoids SDK dependency conflicts
4. **Base64 inline data**: Faster than file upload API
5. **Time-optimized fallback**: 2s max wait (vs 35s before)
6. **Background processing**: Prevents HTTP timeouts
7. **LangGraph routing**: Flexible decision-making
8. **Tool modularity**: Easy testing and debugging

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.