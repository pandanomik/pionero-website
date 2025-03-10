from io import BytesIO
import aiohttp
import asyncio
import time 
import json

import asyncio
import os
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs

LEMONFOX_TOKEN = os.environ.get("LEMONFOX_TOKEN")
CUSTOM_STT_ENDPOINT = os.environ.get("CUSTOM_STT_ENDPOINT")
CUSTOM_STT_TOKEN = os.environ.get("CUSTOM_STT_TOKEN")

async def audio_transcribe(audio_bytes = None, file_path = None, file_name = None):
    try:
        url = 'https://api.lemonfox.ai/v1/audio/transcriptions'
        headers = {
            'Authorization': f'Bearer {LEMONFOX_TOKEN}'
        }
        # await silence_padded_audio(file_path)
        # output_path = f'{file_path}_processed.mp3'
        # preprocess_audio(file_path, output_path, normalize=True, high_pass_cutoff=1000, clip_silence=False, silence_threshold=-40)

        data = aiohttp.FormData()
        if file_path:
            data.add_field('file', 
                           open(file_path, 'rb'),
                        filename=file_path.split('/')[-1],
                        content_type='application/octet-stream')
        else:
            data.add_field('file', 
                           audio_bytes,
                        filename=file_name,
                        content_type='application/octet-stream')
        data.add_field('response_format', 'json')
        data.add_field('language', 'azerbaijani')
        data.add_field('prompt', 'Mətnin azərbaycan dilində qrammatik düzgünlüyündən əmin olun. Mətn bank xidmətləri ilə bağlıdır.')

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, data=data, headers=headers) as response:
                #print("Status:", response.status)
                #print("Content-type:", response.headers['content-type'])
                text = await response.text()
                data = json.loads(text)
                if "error" in data:
                    raise Exception(data["error"]['message'])
                print(data)
                return data["text"]
    except Exception as e:
        raise e
        
async def audio_transcribe_custom(audio_bytes = None, file_path = None, file_name = None):
    try:
        url = CUSTOM_STT_ENDPOINT
        headers = {
            'Authorization': f'Bearer {CUSTOM_STT_TOKEN}',
            'accept': f'Bearer application/json',
        }
        # await silence_padded_audio(file_path)
        # output_path = f'{file_path}_processed.mp3'
        # preprocess_audio(file_path, output_path, normalize=True, high_pass_cutoff=1000, clip_silence=False, silence_threshold=-40)

        data = aiohttp.FormData()
        if file_path:
            data.add_field('file', 
                           open(file_path, 'rb'),
                        filename=file_path.split('/')[-1],
                        content_type='multipart/form-data')
        else:
            data.add_field('file', 
                           audio_bytes,
                        filename=file_name,
                        content_type='multipart/form-data')
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, data=data, headers=headers) as response:
                #print("Status:", response.status)
                #print("Content-type:", response.headers['content-type'])
                text = await response.text()
                data = json.loads(text)
                if "error" in data:
                    raise Exception(data["error"]['message'])
                return data["transcript"]
    except Exception as e:
        raise e

el_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)
    
async def audio_transcribe_elevenlabs(audio_bytes = None, file_path = None, file_name = None):
    try:
        audio_data = BytesIO(audio_bytes)
        transcription = el_client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1", # Model to use, for now only "scribe_v1" is supported
            tag_audio_events=True, # Tag audio events like laughter, applause, etc.
            language_code="az", # Language of the audio file. If set to None, the model will detect the language automatically.
            diarize=True, # Whether to annotate who is speaking
        )
        print(transcription.text)
        return transcription.text
    except Exception as e:
        raise e
    

if __name__ == "__main__":
    asyncio.run(audio_transcribe_custom(file_path='/Users/alakbar/Downloads/output_1.mp3'))