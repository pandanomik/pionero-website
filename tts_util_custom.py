import os
import requests

def text_to_speech(text):
    url = os.environ.get("CUSTOM_TTS_ENDPOINT")
    token = os.environ.get("CUSTOM_TTS_TOKEN")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {"text": text}

    print(url)

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.content
    else:
        print("Error:", response.status_code)
        print(response.text)
        return None

# Example usage:
if __name__ == "__main__":
    text = "Salam, mən Banu, bankınızın çağrı mərkəzinin operatoruyam. Sizə necə kömək edə bilərəm?"
    audio_bytes = text_to_speech(text)
    
    # For example, you can save the bytes to a file (optional):
    if audio_bytes:
        with open("output_audio.wav", "wb") as f:
            f.write(audio_bytes)
