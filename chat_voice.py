#part8
#------------------
#chat UI+voice
#---------------
#voice
#----------
from config import client

def transcribe_audio(file_bytes: bytes, filename: str = "audio.webm", language: str = "ar") -> str:
    transcription = client.audio.transcriptions.create(
        file=(filename, file_bytes),
        model="whisper-large-v3-turbo",
        language=language,
        response_format="json",
        temperature=0.0,
    )
    return transcription.text

