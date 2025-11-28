FROM python:3.12-slim

# --- Create non-root user for HuggingFace Spaces ---
RUN useradd -m -u 1000 user

# --- System deps required by Playwright browsers ---
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates curl unzip \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libgtk-3-0 libgbm1 libasound2 libxcomposite1 libxdamage1 libxrandr2 \
    libxfixes3 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# --- Install Playwright + Chromium as root (before switching to user) ---
RUN pip install playwright && playwright install --with-deps chromium

# --- Install uv package manager ---
RUN pip install uv

# --- Switch to non-root user ---
USER user

# --- Set PATH for user-level binaries ---
ENV PATH="/home/user/.local/bin:$PATH"

# --- Copy app to container ---
WORKDIR /app

COPY --chown=user . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# --- Environment variables (set via docker run -e or HuggingFace Spaces secrets) ---
# Required: EMAIL, SECRET, AIPIPE_API_KEY, GOOGLE_API_KEY

# --- Install project dependencies using uv ---
RUN uv sync --frozen

# HuggingFace Spaces exposes port 7860
EXPOSE 7860

# --- Run your FastAPI app ---
# uvicorn must be in pyproject dependencies
CMD ["uv", "run", "main.py"]
