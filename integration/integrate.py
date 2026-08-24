from google import genai
from google.genai._gaos.lib.compat_errors import RateLimitError
import base64
import wave
import os
import io
from core.settings import GEMINI_API_KEY
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from dotenv import load_dotenv
from pathlib import Path
from baseapp.utils import error_response, success_response


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))


def generate_text(topic, interaction_id=None, first_name=None, student_message=None):
    topic_instruction = (
        f"You are talking to {first_name}. " if first_name else "You are talking to a student. "
    ) + (
        "In the first response just greet and ask what's problem about the topic in short context"
        f"You are an AI educational assistant named Curio. "
        f"You must ONLY answer questions related to {topic}. "
        f"If a student asks about anything else out of topic, "
        f"politely refuse and guide them back to topic."
    )
    
    user_input = student_message if student_message else "Tell shortly about the topic"
    try:
        if interaction_id:
            interaction = client.interactions.create(
                previous_interaction_id=interaction_id,
                model="gemini-3.1-flash-lite",
                system_instruction=topic_instruction,
                input=user_input
            )
        else:
            interaction = client.interactions.create(
                model="gemini-3.1-flash-lite",
                system_instruction=topic_instruction,
                input=user_input
            )
    except RateLimitError as e:
        return {"text": "You have reached the data limit, please try again later", "interaction_id": None, 'error': str(e)}
        
    return {"text": interaction.output_text, "interaction_id": interaction.id}


def generate_audio(text_input, filename="ai_response.wav"):
    try:
        interaction = client.interactions.create(
            model="gemini-3.1-flash-tts-preview",
            input=f"Talk friendly like a human(breathing and umm): {text_input}",
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [
                    {"voice": "Kore"}
                ]
            }
        )
    
    except Exception as e:
        return error_response(message="AI can't response right now, try again later", errors={
            "Error": str(e),
            "file_path": None,
            "file_url": None
        })
    
    pcm_bytes = base64.b64decode(interaction.output_audio.data)
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(pcm_bytes)
    
    wav_buffer.seek(0)
    
    file_path = os.path.join("ai_audio", filename)
    saved_path = default_storage.save(file_path, ContentFile(wav_buffer.read()))
    
    file_url = default_storage.url(saved_path)
    
    return success_response(message="Audio created", data={
        "file_path": saved_path,
        "file_url": file_url
    })