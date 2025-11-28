from langchain_core.tools import tool
import requests
import os
import tempfile
import base64


@tool
def transcribe_audio(audio_url: str) -> str:
    """
    Transcribe audio from a URL using Google Gemini.
    
    This tool uses Gemini's multimodal capabilities to transcribe audio files.
    It downloads the audio file and sends it to Gemini for transcription.
    
    IMPORTANT:
    - Use this for audio transcription tasks (MP3, WAV, etc.)
    - Requires GOOGLE_API_KEY to be set in environment
    - For non-audio tasks, use other tools (Aipipe handles text/code)
    
    Parameters
    ----------
    audio_url : str
        Direct URL to the audio file to transcribe.
    
    Returns
    -------
    str
        The transcribed text from the audio file.
    """
    try:
        print(f"\n🎧 Transcribing audio from: {audio_url}")
        
        # Download the audio file
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        suffix = os.path.splitext(audio_url)[1] or '.mp3'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Get API key
            gemini_key = os.getenv('GOOGLE_API_KEY')
            if not gemini_key:
                raise Exception("GOOGLE_API_KEY not found in environment")
            
            # Read and encode audio file
            print(f"📤 Encoding audio file...")
            with open(tmp_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            mime_type = 'audio/mpeg' if suffix in ['.mp3', '.MP3'] else 'audio/wav'
            
            # Call Gemini API with inline data
            print(f"🔄 Generating transcription with Gemini...")
            api_response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
                params={'key': gemini_key},
                json={
                    'contents': [{
                        'parts': [
                            {'text': 'Transcribe this audio file. Return ONLY the transcribed text, nothing else.'},
                            {'inlineData': {'mimeType': mime_type, 'data': audio_data}}
                        ]
                    }]
                }
            )
            api_response.raise_for_status()
            
            transcription = api_response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"✅ Transcription complete ({len(transcription)} characters)")
            
            return transcription
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        error_msg = f"Error transcribing audio: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
