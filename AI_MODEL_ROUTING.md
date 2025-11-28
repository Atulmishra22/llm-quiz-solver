# AI Model Routing Strategy

## Overview
The agent intelligently routes tasks to the appropriate AI model/API based on the task type:

- **Aipipe/OpenRouter (Claude 3.5 Sonnet)** - Reasoning, code generation, text analysis
- **Google Gemini (gemini-2.0-flash-exp)** - Multimodal tasks (audio, images, videos, PDFs)

## Task Routing Matrix

| Task Type | Tool Used | Model/API | Why |
|-----------|-----------|-----------|-----|
| **Text reasoning** | _(agent itself)_ | Aipipe | Cheaper, faster for pure text |
| **Code generation** | `run_code` | Aipipe | Excellent at code tasks |
| **Web scraping** | `get_rendered_html` | N/A | Uses Playwright |
| **Audio transcription** | `transcribe_audio` or `analyze_with_gemini` | Gemini | Multimodal capability |
| **Image analysis** | `analyze_with_gemini` | Gemini | Visual understanding |
| **PDF extraction** | `analyze_with_gemini` | Gemini | Document processing |
| **Video analysis** | `analyze_with_gemini` | Gemini | Video understanding |
| **Chart/Graph reading** | `analyze_with_gemini` | Gemini | Visual data analysis |
| **Unknown file type** | `analyze_with_gemini` | Gemini | Handles most formats |
| **HTTP requests** | `post_request` | N/A | Direct API call |
| **File download** | `download_file` | N/A | Direct download |
| **Package install** | `add_dependencies` | N/A | UV package manager |

## Example Scenarios

### Scenario 1: Audio Quiz
```
Quiz: "Transcribe this audio and find the hidden number"
URL: https://example.com/audio.mp3

Agent Flow:
1. Agent (Aipipe) reads quiz instructions
2. Detects audio file → calls analyze_with_gemini(url, "Transcribe this audio")
3. Gemini transcribes the audio
4. Agent (Aipipe) analyzes transcription to find the number
5. Agent (Aipipe) submits answer via post_request
```

### Scenario 2: Image Chart Analysis
```
Quiz: "What is the sum of values in this bar chart?"
URL: https://example.com/chart.png

Agent Flow:
1. Agent (Aipipe) reads quiz instructions
2. Detects image → calls analyze_with_gemini(url, "Extract all values from this bar chart")
3. Gemini reads the chart and returns values
4. Agent (Aipipe) calculates the sum
5. Agent (Aipipe) submits answer
```

### Scenario 3: PDF Document
```
Quiz: "How many times does 'python' appear in this PDF?"
URL: https://example.com/doc.pdf

Agent Flow:
1. Agent (Aipipe) reads quiz instructions
2. Detects PDF → calls analyze_with_gemini(url, "Extract all text from this PDF")
3. Gemini extracts text
4. Agent (Aipipe) counts occurrences of 'python'
5. Agent (Aipipe) submits answer
```

### Scenario 4: CSV Data Analysis
```
Quiz: "Find the average of column 'score' in this CSV"
URL: https://example.com/data.csv

Agent Flow:
1. Agent (Aipipe) reads quiz instructions
2. Downloads CSV with download_file
3. Generates Python code to analyze it
4. Runs code with run_code tool
5. Agent (Aipipe) submits result
```

### Scenario 5: Mixed Tasks
```
Quiz: "Transcribe audio.mp3, then multiply the number by the value in chart.png"

Agent Flow:
1. Agent (Aipipe) understands multi-step task
2. Step 1: analyze_with_gemini("audio.mp3", "Transcribe and extract any numbers")
3. Gemini returns: "The number is 42"
4. Step 2: analyze_with_gemini("chart.png", "What is the value shown?")
5. Gemini returns: "The value is 7"
6. Agent (Aipipe) calculates: 42 × 7 = 294
7. Agent (Aipipe) submits answer
```

## Fallback Strategy

If the agent encounters an unknown task type or new requirement:

1. **First**: Try to solve with existing tools
2. **If unsure**: Use `analyze_with_gemini` with a descriptive prompt
3. **If still fails**: Agent will report the error back to the system

Example of unknown file type:
```python
# Agent encounters .webm video file
analyze_with_gemini(
    "https://example.com/video.webm",
    "Analyze this file and tell me: 1) What type of content is it? 2) What information does it contain?"
)
```

## Cost Optimization

- **Cheap tasks** (text, code, reasoning) → Aipipe ($0.003/1M tokens)
- **Expensive tasks** (multimodal) → Gemini (only when necessary)
- Agent intelligently minimizes Gemini usage by:
  - Using Gemini only for multimodal content
  - Processing Gemini outputs with Aipipe for further reasoning
  - Batching multimodal requests when possible

## Adding New Capabilities

If you need a new type of analysis (e.g., 3D models, audio synthesis):

### Option 1: Use analyze_with_gemini (if Gemini supports it)
```python
analyze_with_gemini(
    file_url="https://example.com/model.obj",
    prompt="Describe this 3D model's structure and dimensions"
)
```

### Option 2: Create a specialized tool
```python
# tools/analyze_3d_model.py
@tool
def analyze_3d_model(file_url: str) -> str:
    """Analyze 3D models using specialized API"""
    # Your custom logic here
    pass
```

Then add to `tools/__init__.py` and `agent.py` TOOLS list.

## Environment Variables

```bash
# Required for reasoning and code generation
AIPIPE_API_KEY=your_aipipe_key

# Required for multimodal tasks (audio, images, PDFs, videos)
GOOGLE_API_KEY=your_gemini_key

# Quiz system credentials
EMAIL=your_email
SECRET=your_secret
```

## Summary

The system is **flexible and extensible**:
- ✅ Handles known multimodal tasks automatically (audio, images, PDFs, videos)
- ✅ Falls back to Gemini for unknown file types
- ✅ Uses cheap Aipipe for all reasoning/code tasks
- ✅ Easy to add new tools for specialized tasks
- ✅ Agent intelligently chooses the right tool based on task requirements
