import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template, send_file, session
from openai import OpenAI
import asyncio
import datetime
from tts_util_custom import text_to_speech
from stt_util import audio_transcribe, audio_transcribe_custom, audio_transcribe_elevenlabs


app = Flask(__name__)
# Set a secret key for session management. In production, use a secure, random key.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

# Initialize the OpenAI client with your API key.
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ElevenLabs TTS voice IDs for each language.
TTS_VOICE_IDS = {
    "en-US": os.environ.get("ELEVENLABS_VOICE_EN", "0S5oIfi8zOZixuSj8K6n"),
    "ru-RU": os.environ.get("ELEVENLABS_VOICE_RU", "AB9XsbSA4eLG12t2myjN"), #Larisa Actrisa
    "tr-TR": os.environ.get("ELEVENLABS_VOICE_TR", "xyqF3vGMQlPk3e7yA4DI") #Ahu
}

# Dictionary of system prompts keyed by organization.
SYSTEM_PROMPTS = {
    "bank": (
        "You are Lucy, an AI call center operator for a major bank. "
        "Your role is to handle live audio phone calls with customers. Start each call with a warm, professional greeting similar to what a bank call center operator would say, without using exclamation marks. "
        "Your primary responsibility is to answer questions strictly related to banking services such as account information, transactions, loans, and credit cards. "
        "If a customer asks about topics outside of banking or requests details that require personal data verification, politely explain that you can only assist with banking-related inquiries and that you will connect them with a human operator if more detailed assistance is needed. "
        "Maintain a calm, empathetic, and professional tone at all times. "
    ),
    "insurance": (
        "You are Lucy, an AI customer service agent for a reputable insurance company. "
        "Your role is to engage with customers over the phone and provide clear, concise, and friendly assistance regarding insurance policies, claims, coverage details, and billing issues. "
        "Always use an empathetic and reassuring tone. If a caller inquires about matters outside of insurance or requires personal data verification, inform them that you can only address insurance-related queries and suggest connecting them with a human agent for further support. "
        "Keep your responses accurate and professional. "
    ),
    "retail": (
        "You are Lucy, an AI assistant for a leading retail company. "
        "Your task is to interact with customers over the phone by providing accurate product information, guiding them through order processes, handling inquiries about promotions, and assisting with order-related issues. "
        "Speak in a friendly, upbeat, and professional manner. If a customer asks about topics not related to products, orders, or promotions, kindly remind them that you specialize in retail assistance and offer to connect them with the appropriate department if necessary. "
        "Ensure your responses are clear and helpful. "
    ),
}

def generate_audio(text, voice_id):
    """Generate audio using ElevenLabs TTS API."""
    elevenlabs_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": os.environ.get("ELEVENLABS_API_KEY"),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    print(f"Generating TTS with ElevenLabs for language using voice: {voice_id}")
    try:
        tts_response = requests.post(elevenlabs_url, json=payload, headers=headers)
        tts_response.raise_for_status()
        return tts_response.content
    except Exception as e:
        error_details = tts_response.text if 'tts_response' in locals() else "No response body."
        raise Exception(f"Error generating TTS: {str(e)}. Details: {error_details}")
    
def correct_azerbaijani_text(text):
    """Uses the OpenAI ChatCompletion API to correct the grammar of the given Azerbaijani text."""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that corrects Azerbaijani grammar. Print only final corrected text form."
        },
        {
            "role": "user",
            "content": f"Please correct the spelling errors in the following Azerbaijani text.:\n\n{text}"
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0  # Setting temperature to 0 for more deterministic output
    )
    
    # Extract and return the corrected text
    corrected_text = response.choices[0].message.content.strip()
    return corrected_text

def language_name(lang_code):
    """Get the language name from a language code."""
    mapping = {
        "en-US": "English",
        "ru-RU": "Russian",
        "tr-TR": "Turkish",
        "az-AZ": "Azerbaijani"        
    }
    return mapping.get(lang_code, "English")

@app.route("/")
def index():
    """Render the main index page."""
    return render_template("index.html")

@app.route("/dial", methods=["POST"])
def dial():
    """Handle the initial dial request to start a conversation."""
    try:
        data = request.get_json() or {}

        org = data.get("organization", "bank")  # default to "bank"
        lang = data.get("language", "en-US")      # default to English
        
        # Append instruction to respond in the chosen language.
        base_prompt = SYSTEM_PROMPTS.get(org, SYSTEM_PROMPTS["bank"])
        system_prompt = base_prompt + f" Respond in {language_name(lang)}. AI operator name have to be in {language_name(lang)}."
        
        # Reset conversation history.
        session.pop("conversation", None)
        conversation = [{"role": "system", "content": system_prompt}]
        conversation.append({"role": "user", "content": "Dial in"})

        try:
            response_llm = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation
            )
            answer = response_llm.choices[0].message.content
            conversation.append({"role": "assistant", "content": answer})
            session["conversation"] = conversation
        except Exception as e:
            app.logger.error(f"LLM Error: {str(e)}")
            return jsonify({"error": f"Error generating response: {str(e)}"}), 500

        try:
            print(f'Generating audio for: {answer}')
            if lang == "az-AZ":
                audio_content = text_to_speech(answer)
                if not audio_content:
                    raise Exception("Failed to generate Azerbaijani TTS")
            else:
                voice_id = TTS_VOICE_IDS.get(lang, TTS_VOICE_IDS["en-US"])
                audio_content = generate_audio(answer, voice_id)
        except Exception as e:
            app.logger.error(f"TTS Error: {str(e)}")
            return jsonify({"error": f"Error generating speech: {str(e)}"}), 500

        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        return jsonify({"text": answer, "audio": audio_base64})
    
    except Exception as e:
        app.logger.error(f"Unexpected error in dial: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/process", methods=["POST"])
def process():
    """Process user input during the conversation."""
    try:
        data = request.get_json()
        user_input = data.get("input")
        lang = data.get("language", "en-US")

        print(f'Processing input: {user_input} in language: {lang}')
        
        if not user_input:
            return jsonify({"error": "No input received."}), 400

        conversation = session.get("conversation", [])
        if not conversation:
            # If no conversation exists, create one with the default system prompt
            base_prompt = SYSTEM_PROMPTS["bank"]
            system_prompt = base_prompt + f" Respond in {language_name(lang)}."
            conversation.append({"role": "system", "content": system_prompt})
            
        conversation.append({"role": "user", "content": user_input})
        
        try:
            response_llm = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation
            )
            answer = response_llm.choices[0].message.content
            conversation.append({"role": "assistant", "content": answer})
            session["conversation"] = conversation
        except Exception as e:
            app.logger.error(f"LLM Error: {str(e)}")
            return jsonify({"error": f"Error generating response: {str(e)}"}), 500

        try:
            if lang == "az-AZ":
                audio_content = text_to_speech(answer)
                if not audio_content:
                    raise Exception("Failed to generate Azerbaijani TTS")
            else:
                voice_id = TTS_VOICE_IDS.get(lang, TTS_VOICE_IDS["en-US"])
                audio_content = generate_audio(answer, voice_id)
        except Exception as e:
            app.logger.error(f"TTS Error: {str(e)}")
            return jsonify({"error": f"Error generating speech: {str(e)}"}), 500

        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        return jsonify({"text": answer, "audio": audio_base64})
    
    except Exception as e:
        app.logger.error(f"Unexpected error in process: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe uploaded audio files, particularly for Azerbaijani."""
    try:
        # Check if the POST request contains an 'audio' file.
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        
        # Ensure the file has a valid filename.
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        selected_model = request.form.get('model')  # This will be either "model_1" or "model_2"

        if not selected_model:
            return jsonify({'error': 'No model selected.'}), 400

        try:
            # Read the audio data directly from the uploaded file.
            audio_bytes = audio_file.read()
            print(f"Transcribing audio with model: {selected_model}")
            
            if selected_model == "model_1":
                # Use ElevenLabs STT
                transcript = asyncio.run(audio_transcribe_elevenlabs(audio_bytes=audio_bytes, file_name=audio_file.filename))
            else:
                # Use custom STT
                transcript = asyncio.run(audio_transcribe_custom(audio_bytes=audio_bytes, file_name=audio_file.filename))

            if not transcript:
                raise Exception("Failed to transcribe audio")

        except Exception as e:
            app.logger.error(f"STT Error: {str(e)}")
            return jsonify({'error': f'Error transcribing audio: {str(e)}'}), 500

        # Correct Azerbaijani text using OpenAI
        try:
            corrected_transcript = correct_azerbaijani_text(transcript)
        except Exception as e:
            app.logger.error(f"Text correction error: {str(e)}")
            # Continue with the uncorrected transcript if correction fails
            corrected_transcript = transcript

        # Return the transcript as a JSON response.
        return jsonify({'transcript': corrected_transcript}), 200
    
    except Exception as e:
        app.logger.error(f"Unexpected error in transcribe: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == "__main__":
    # For local development
    app.run(debug=True)