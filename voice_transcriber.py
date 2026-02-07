"""
Voice Transcription Module
Uses Groq's Whisper API for free, fast speech-to-text
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribe_voice(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """
    Transcribe audio using Groq's Whisper API
    
    Args:
        audio_bytes: Raw audio file bytes
        filename: Name with extension for MIME type detection
    
    Returns:
        Transcribed text or error message
    """
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is not set!")
        return "[Transcription failed: API key not configured]"
    
    try:
        async with httpx.AsyncClient() as client:
            # Prepare multipart form data
            files = {
                "file": (filename, audio_bytes, "audio/ogg"),
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "text",
            }
            
            response = await client.post(
                GROQ_WHISPER_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                },
                files=files,
                data=data,
                timeout=60.0  # Voice notes can take time
            )
            
            if response.status_code != 200:
                print(f"Whisper API error: {response.status_code} - {response.text}")
                return f"[Transcription failed: {response.status_code}]"
            
            # Response is plain text when response_format is "text"
            transcription = response.text.strip()
            
            if not transcription:
                return "[Voice note was empty or inaudible]"
            
            return transcription
            
    except httpx.TimeoutException:
        print("Whisper API timeout")
        return "[Transcription failed: timeout]"
    except Exception as e:
        print(f"Transcription error: {e}")
        return f"[Transcription failed: {str(e)}]"
