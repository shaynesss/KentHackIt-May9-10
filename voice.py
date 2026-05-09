import os

from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

_OUTPUT_PATH = "static/roast.mp3"


def generate_roast_audio(roast_text: str) -> str:
    audio = client.text_to_speech.convert(
        voice_id="QegsK1eBP9R2FBZkvngf",
        text=roast_text,
        model_id="eleven_multilingual_v2",
    )

    with open(_OUTPUT_PATH, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return _OUTPUT_PATH
