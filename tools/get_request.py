from langchain_core.tools import tool
import requests
from typing import Any, Dict, Optional


@tool
def get_request(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Send an HTTP GET request to an API endpoint with optional headers and parameters.
    
    Use this for:
    - Fetching data from REST APIs
    - APIs requiring authentication headers (API keys, tokens)
    - APIs with query parameters
    
    Parameters
    ----------
    url : str
        The API endpoint URL to request.
    headers : dict, optional
        HTTP headers (e.g., {"Authorization": "Bearer TOKEN", "X-API-Key": "key123"})
    params : dict, optional
        Query parameters (e.g., {"page": 1, "limit": 100})
    
    Returns
    -------
    Any
        The API response. Returns JSON dict if possible, otherwise raw text.
    
    Examples
    --------
    # Simple GET
    get_request("https://api.example.com/data")
    
    # With API key header
    get_request("https://api.example.com/data", headers={"X-API-Key": "abc123"})
    
    # With query params
    get_request("https://api.example.com/data", params={"category": "sports", "limit": 10})
    """
    headers = headers or {}
    params = params or {}
    
    try:
        print(f"\n📡 GET Request to: {url}")
        if headers:
            print(f"   Headers: {list(headers.keys())}")
        if params:
            print(f"   Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # Try to return JSON, fallback to text
        try:
            data = response.json()
            print(f"✅ Response received ({len(str(data))} chars)")
            return data
        except ValueError:
            text = response.text
            print(f"✅ Response received ({len(text)} chars, non-JSON)")
            return text
            
    except requests.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
