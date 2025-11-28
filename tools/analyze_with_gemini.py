from langchain_core.tools import tool
import requests
import os
import tempfile
from typing import Optional
import base64


@tool
def analyze_with_gemini(
    file_url: str,
    prompt: str = "Analyze this file and provide detailed information about its contents.",
    file_type: Optional[str] = None
) -> str:
    """
    Analyze any file (audio, image, PDF, video, etc.) using Google Gemini's multimodal capabilities.
    
    This is a general-purpose multimodal analysis tool that uses Gemini for tasks that
    Aipipe/OpenRouter cannot handle (audio, images, videos, PDFs, etc.).
    
    Use this tool when you need to:
    - Transcribe audio files (MP3, WAV, etc.)
    - Analyze images (PNG, JPG, etc.)
    - Extract text from PDFs
    - Analyze videos
    - Process any multimodal content
    
    For pure text/code tasks, the agent uses Aipipe (already configured).
    
    Parameters
    ----------
    file_url : str
        Direct URL to the file to analyze.
    prompt : str, optional
        What you want to know about the file. 
        Default: "Analyze this file and provide detailed information about its contents."
    file_type : str, optional
        File extension hint (.mp3, .jpg, .pdf, etc.). Auto-detected if not provided.
    
    Returns
    -------
    str
        Gemini's analysis of the file content.
    
    Examples
    --------
    - analyze_with_gemini("https://example.com/audio.mp3", "Transcribe this audio")
    - analyze_with_gemini("https://example.com/chart.png", "What data is shown in this chart?")
    - analyze_with_gemini("https://example.com/doc.pdf", "Summarize this document")
    """
    try:
        # Determine file type
        if not file_type:
            file_type = os.path.splitext(file_url)[1] or '.bin'
        
        print(f"\n🔍 Analyzing file with Gemini (multimodal)")
        print(f"   URL: {file_url}")
        print(f"   Type: {file_type}")
        print(f"   Task: {prompt[:60]}...")
        
        # Download the file
        print(f"📥 Downloading file...")
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Get API key
            gemini_key = os.getenv('GOOGLE_API_KEY')
            if not gemini_key:
                raise Exception("GOOGLE_API_KEY not found in environment")
            
            # Read and encode file
            print(f"📤 Encoding file...")
            with open(tmp_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            mime_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                '.pdf': 'application/pdf', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
                '.mp4': 'video/mp4', '.avi': 'video/x-msvideo'
            }
            mime_type = mime_types.get(file_type.lower(), 'application/octet-stream')
            
            # Call Gemini API with inline data
            print(f"🤖 Generating analysis with Gemini...")
            api_response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
                params={'key': gemini_key},
                json={
                    'contents': [{
                        'parts': [
                            {'text': prompt},
                            {'inlineData': {'mimeType': mime_type, 'data': file_data}}
                        ]
                    }]
                }
            )
            api_response.raise_for_status()
            
            result = api_response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"✅ Analysis complete ({len(result)} characters)")
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        error_msg = f"Error analyzing file with Gemini: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
