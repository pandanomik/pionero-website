#8l08BrPio7tvWR0FiKL6SUJNKTHh7ToufjFUuuk9z73GvRAuq6MEJQQJ99BBACYeBjFXJ3w3AAAYACOGpIH7
#3bTgf52xufVjIy2uY43WTM00mtWa4PPCG9rsCtXos7UEmLBS08TEJQQJ99BBACYeBjFXJ3w3AAAYACOG52V4
#eastus
#https://eastus.api.cognitive.microsoft.com/

import azure.cognitiveservices.speech as speechsdk
import os

def text_to_speech(text, output_filename="./output_audio.mp3"):
    # Replace these with your own subscription key and service region (e.g., "westus", "eastus2", etc.)
    speech_key = os.environ.get("AZURE_TTS_SPEECH_KEY")
    service_region = os.environ.get("AZURE_TTS_SPEECH_REGION")

    # Create an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    
    # Set the voice name to an Azerbaijani voice.
    # (Check the latest supported voices on https://learn.microsoft.com/azure/cognitive-services/speech-service/language-support)
    speech_config.speech_synthesis_voice_name = os.environ.get("AZURE_TTS_VOICE_NAME")
    #speech_config.speech_synthesis_output_format = speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    speech_config.speech_synthesis_output_format = speechsdk.SpeechSynthesisOutputFormat.Audio48Khz96KBitRateMonoMp3

    # Specify the audio output configuration - here we save the speech to a WAV file.
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)

    # Create a speech synthesizer using the given settings.
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Synchronously synthesize the provided text to speech.
    result = synthesizer.speak_text_async(text).get()

    # Check result and provide feedback.
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #print(f"Speech synthesized successfully and saved to '{output_filename}'")
        audio_bytes = result.audio_data  # This is a bytearray containing the MP3 audio.
        print("Speech synthesized successfully.")
        return audio_bytes
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

if __name__ == "__main__":
    # Azerbaijani sample text. Replace with your desired text.
    text_to_speak = "Salam, mən Banu, bankınızın çağrı mərkəzinin operatoruyam. Sizə necə kömək edə bilərəm?"
    text_to_speech(text=text_to_speak)
