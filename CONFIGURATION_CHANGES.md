# Configuration Changes - Aipipe/OpenRouter Integration

## Summary
The project now uses **Aipipe/OpenRouter** for reasoning and code generation tasks, while keeping **Google Gemini** available for future multimodal needs (audio, vision, etc.).

## What Changed

### 1. Main LLM Provider (`agent.py`)
- **Before**: Used Google Gemini (`google_genai` provider with `gemini-2.5-flash` model)
- **After**: Uses Aipipe/OpenRouter (`ChatOpenAI` with `anthropic/claude-3.5-sonnet` model via OpenRouter API)

### 2. New Files Created
- **`tools/aipipe_client.py`**: Helper functions for Aipipe/OpenRouter API calls
  - `get_api_key()`: Validates and retrieves `AIPIPE_API_KEY`
  - `get_base_url()`: Gets base URL (defaults to `https://aipipe.org/openrouter/v1`)
  - `request_completion()`: Makes chat completion requests

- **`tools/gemini_client.py`**: Helper for Google Gemini (multimodal tasks only)
  - `get_gemini_client()`: Returns Gemini client for audio/vision tasks
  - Requires `GOOGLE_API_KEY` environment variable

### 3. Dependencies Updated (`pyproject.toml`)
- Added: `langchain-openai>=0.1.0`
- Kept: `langchain-google-genai` and `google-genai` (for future multimodal use)

### 4. Tools Updated
- **`tools/run_code.py`**: Removed Google GenAI imports (no longer needed at import time)
- All other tools remain unchanged (no multimodal requirements currently)

## Environment Variables Required

### Primary (Required)
```bash
AIPIPE_API_KEY=your_aipipe_key_here      # REQUIRED for agent to work
EMAIL=your_email@example.com             # REQUIRED for quiz submissions
SECRET=your_secret_here                  # REQUIRED for quiz submissions
```

### Optional
```bash
AIPIPE_BASE_URL=https://aipipe.org/openrouter/v1  # Optional, has default
GOOGLE_API_KEY=your_gemini_key           # Only needed for multimodal tasks
```

## How to Run

1. Copy `.env.example` to `.env`:
   ```powershell
   cp .env.example .env
   ```

2. Edit `.env` and add your `AIPIPE_API_KEY`, `EMAIL`, and `SECRET`

3. Sync dependencies:
   ```powershell
   uv sync
   ```

4. Start the server:
   ```powershell
   uv run main.py
   ```

5. Test with curl or PowerShell:
   ```powershell
   curl -X POST http://localhost:7860/solve `
     -H "Content-Type: application/json" `
     -d '{
       "email": "23f2001262@ds.study.iitm.ac.in",
       "secret": "jaguar",
       "url": "https://tds-llm-analysis.s-anand.net/demo"
     }'
   ```

## Model Selection

You can change the model used by editing `agent.py`:

```python
llm = ChatOpenAI(
    model="anthropic/claude-3.5-sonnet",  # Change this to any OpenRouter model
    openai_api_key=AIPIPE_API_KEY,
    openai_api_base=AIPIPE_BASE_URL,
    temperature=0.7,
    rate_limiter=rate_limiter
).bind_tools(TOOLS)
```

Available models via OpenRouter include:
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3-opus`
- `openai/gpt-4o`
- `google/gemini-2.0-flash-exp`
- And many more...

## Future Multimodal Tasks

If you need to add audio transcription, image analysis, or other multimodal features:

1. Import the Gemini client in your tool:
   ```python
   from tools.gemini_client import get_gemini_client
   ```

2. Use it for multimodal tasks:
   ```python
   client = get_gemini_client()  # Requires GOOGLE_API_KEY in .env
   # Use client for audio/vision tasks
   ```

## Troubleshooting

- **Import error**: Run `uv sync` to install all dependencies
- **Missing AIPIPE_API_KEY**: Set it in `.env` file
- **403 Forbidden**: Check that `SECRET` in `.env` matches the test request
- **Rate limit errors**: Adjust `requests_per_second` in `agent.py`
