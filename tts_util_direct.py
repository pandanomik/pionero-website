import os
import requests

def text_to_speech(text):
    # Get your subscription key, region, and voice name from environment variables.
    subscription_key = os.environ.get("AZURE_TTS_SPEECH_KEY")
    region = os.environ.get("AZURE_TTS_SPEECH_REGION")
    voice_name = os.environ.get("AZURE_TTS_VOICE_NAME", "en-US-AriaNeural")  # default if not set

    # The API endpoint URL for your region.
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    # Define request headers.
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Ocp-Apim-Subscription-Region": region,  # Include this if required by your endpoint.
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-48khz-96kbitrate-mono-mp3",
        "User-Agent": "YourAppName"  # Replace with your app name if desired.
    }

    # Create the SSML request body.
    ssml = f"""
    <speak version='1.0' xml:lang='az-AZ'>
      <voice xml:lang='az-AZ' xml:gender='Female' name='{voice_name}'>
        {text}
      </voice>
    </speak>
    """

    # Make the POST request to the TTS API.
    response = requests.post(endpoint, headers=headers, data=ssml.encode("utf-8"))
    
    # Check the response status.
    if response.status_code == 200:
        print("Speech synthesized successfully.")
        # The synthesized audio is returned as binary data (audio bytes).
        audio_bytes = response.content
        return audio_bytes
    else:
        print(f"Error synthesizing speech: {response.status_code}")
        print(response.text)
        return None

# Example usage:
if __name__ == "__main__":
    text = "Salam, mən Banu, bankınızın çağrı mərkəzinin operatoruyam. Sizə necə kömək edə bilərəm?"
    audio_bytes = text_to_speech(text)
    
    # For example, you can save the bytes to a file (optional):
    if audio_bytes:
        with open("output_audio.mp3", "wb") as f:
            f.write(audio_bytes)
