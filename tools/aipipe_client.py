"""
Aipipe/OpenRouter client helper for code generation and reasoning tasks.
Uses AIPIPE_API_KEY and AIPIPE_BASE_URL from environment.
"""
import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List

load_dotenv()

DEFAULT_BASE = "https://aipipe.org/openrouter/v1"


def get_base_url():
    """Get Aipipe base URL from environment or use default."""
    return os.getenv("AIPIPE_BASE_URL") or os.getenv("AI_PIPE_BASE_URL") or DEFAULT_BASE


def get_api_key():
    """Get Aipipe API key from environment.
    
    Raises:
        RuntimeError: If API key is not set.
    """
    key = os.getenv("AIPIPE_API_KEY") or os.getenv("AI_PIPE_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing AIPIPE_API_KEY (or AI_PIPE_API_KEY). "
            "Set it in your environment or .env file."
        )
    return key


def get_session():
    """Return a requests.Session preconfigured with Authorization header."""
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json"
    })
    return sess


def request(path: str, method: str = "POST", json: dict | None = None, **kwargs):
    """Make a request to the Aipipe/OpenRouter endpoint.

    Args:
        path: API path (e.g., "chat/completions")
        method: HTTP method
        json: Request payload
        **kwargs: Additional requests parameters

    Returns:
        Response JSON dict

    Raises:
        requests.HTTPError: If request fails
    """
    base = get_base_url().rstrip("/")
    path = path.lstrip("/")
    url = f"{base}/{path}"
    sess = get_session()
    resp = sess.request(method, url, json=json, **kwargs)
    resp.raise_for_status()
    return resp.json()


def request_completion(
    messages: List[Dict[str, str]],
    model: str = "anthropic/claude-3.5-sonnet",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs
) -> Dict[str, Any]:
    """
    Request a chat completion from Aipipe/OpenRouter.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Model identifier (default: anthropic/claude-3.5-sonnet).
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        **kwargs: Additional parameters to pass to the API.
    
    Returns:
        Response dict from the API.
    
    Raises:
        RuntimeError: If AIPIPE_API_KEY is not set.
        requests.HTTPError: If the API returns an error status.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs
    }
    
    return request("chat/completions", method="POST", json=payload)
