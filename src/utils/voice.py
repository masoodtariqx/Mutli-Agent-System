"""
Voice Utility - ElevenLabs Text-to-Speech for AI Prediction Battle
Uses ElevenLabs API for high-quality, natural voices.
Falls back to edge-tts if ElevenLabs is not configured.
"""

import os
import tempfile
import pygame

# ElevenLabs voice IDs for each agent (distinct voices)
ELEVENLABS_VOICES = {
    "ChatGPT": "onwK4e9ZLuTAKqWW03F9",    # Daniel - calm, professional
    "Grok": "TX3LPaxmHKxFdv7VOQHJ",        # Liam - energetic, casual
    "Gemini": "EXAVITQu4vr4xnSDxMaL",      # Sarah - analytical
    "Moderator": "21m00Tcm4TlvDq8ikWAM",   # Rachel - neutral, clear
}

# Fallback edge-tts voices
EDGE_VOICES = {
    "ChatGPT": "en-US-GuyNeural",
    "Grok": "en-US-ChristopherNeural",
    "Gemini": "en-US-EricNeural",
    "Moderator": "en-GB-SoniaNeural",
}

DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"


def _speak_elevenlabs(text, agent_name):
    """Speak using ElevenLabs API."""
    try:
        from elevenlabs import ElevenLabs
        
        api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_KEY")
        if not api_key:
            return False
        
        client = ElevenLabs(api_key=api_key)
        voice_id = ELEVENLABS_VOICES.get(agent_name, DEFAULT_VOICE)
        
        # Generate audio
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128"
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            for chunk in audio:
                f.write(chunk)
            temp_path = f.name
        
        # Play audio
        pygame.mixer.init()
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.quit()
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"[ElevenLabs Error: {e}]")
        return False


def _speak_edge_tts(text, agent_name):
    """Fallback to edge-tts."""
    try:
        import asyncio
        import edge_tts
        import sys
        
        voice = EDGE_VOICES.get(agent_name, "en-US-AriaNeural")
        
        async def _speak_async():
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_path = f.name
            
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_path)
                
                pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.quit()
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_speak_async())
        finally:
            loop.close()
        
        return True
    except Exception as e:
        print(f"[Edge-TTS Error: {e}]")
        return False


def speak(text, agent_name="Moderator"):
    """
    Speak text using agent's voice.
    Tries ElevenLabs first, falls back to edge-tts.
    """
    # Try ElevenLabs first
    if _speak_elevenlabs(text, agent_name):
        return
    
    # Fallback to edge-tts
    _speak_edge_tts(text, agent_name)


def get_voice_for_agent(agent_name):
    """Get the voice ID for a given agent."""
    return ELEVENLABS_VOICES.get(agent_name, DEFAULT_VOICE)


def test_voice():
    """Test all agent voices."""
    from src.utils.console import console
    
    console.print("\n Testing ElevenLabs voices...")
    
    test_texts = {
        "Moderator": "Welcome to the AI Prediction Battle.",
        "ChatGPT": "I predict YES with 75% confidence.",
        "Grok": "Early signals suggest this will happen.",
        "Gemini": "Historical constraints make this unlikely.",
    }
    
    for agent, text in test_texts.items():
        console.print(f"   {agent} speaking...")
        speak(text, agent)
        console.print(f"   Done")
    
    console.print("\n Voice test complete!")
    return True
