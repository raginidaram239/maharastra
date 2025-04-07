
import os
import openai
import faiss
import pickle
import numpy as np
import azure.cognitiveservices.speech as speechsdk
from langdetect import detect
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
import datetime
import speech_recognition as sr

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_DEPLOYMENT_EMBEDDINGS = os.getenv("AZURE_DEPLOYMENT_EMBEDDINGS")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")

translator_client = TextTranslationClient(
    credential=AzureKeyCredential(AZURE_TRANSLATOR_KEY),
    endpoint=f"https://{AZURE_TRANSLATOR_REGION}.cognitiveservices.azure.com/"
)

os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)

chat_history = []

def load_faiss_index():
    try:
        with open("chunks.pkl", "rb") as f:
            chunks = pickle.load(f)
        index = faiss.read_index("faiss_index.bin")
        return index, chunks
    except Exception as e:
        print(f"⚠️ Error loading FAISS index: {e}")
        return None, None

faiss_index, chunks = load_faiss_index()

def setup_openai():
    openai.api_type = "azure"
    openai.api_base = AZURE_OPENAI_ENDPOINT
    openai.api_version = AZURE_OPENAI_API_VERSION
    openai.api_key = AZURE_OPENAI_API_KEY

def translate_text(text, from_lang, to_lang):
    try:
        response = translator_client.translate(
            body={"contents": [text], "from": from_lang, "to": [to_lang]}
        )
        return response[0].translations[0].text
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text

def get_response_from_faiss(query, detected_lang="en"):
    if not faiss_index or not chunks:
        return "⚠️ Knowledge base is not loaded."

    setup_openai()

    try:
        embedding_response = openai.Embedding.create(
            deployment_id=AZURE_DEPLOYMENT_EMBEDDINGS,
            input=[query]
        )
        query_embedding = np.array(embedding_response["data"][0]["embedding"], dtype=np.float32).reshape(1, -1)
    except Exception as e:
        return f"⚠️ Error generating embeddings: {e}"

    distances, indices = faiss_index.search(query_embedding, k=3)
    retrieved_chunks = [chunks[i] for i in indices[0] if i != -1]

    if all(dist > 1.5 for dist in distances[0]) or not retrieved_chunks:
        polite_message = {
            "en": "I'm sorry, I couldn't find relevant information. Could you please rephrase your question?",
            "hi": "माफ़ कीजिए, मुझे प्रासंगिक जानकारी नहीं मिली। कृपया अपना प्रश्न दोबारा पूछें।"
        }
        return polite_message["hi"] if detected_lang in ["hi", "hi-en"] else polite_message["en"]

    context = "\n---\n".join(retrieved_chunks)

    messages = [
        {"role": "system", "content": "You are an intelligent assistant. Answer based on the context provided."},
    ]

    for user_msg, bot_msg in chat_history[-5:]:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})

    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"})

    try:
        completion = openai.ChatCompletion.create(
            engine=AZURE_OPENAI_DEPLOYMENT,
            temperature=0.3,
            messages=messages
        )
        return completion["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error generating response: {e}"

def generate_speech(response_text, language="en"):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = "hi-IN-SwaraNeural" if language != "en" else "en-IN-NeerjaNeural"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"output/response_{timestamp}.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_name)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(response_text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"⚠️ Speech synthesis error: {result.reason}")
    return file_name

def recognize_audio_file(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except Exception as e:
        print(f"⚠️ Speech recognition error: {e}")
        return ""

def save_text_to_file(text, folder="input"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    path = os.path.join(folder, f"{folder}_{timestamp}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def process_input(input_text_or_file):
    if os.path.isfile(input_text_or_file):
        input_text = recognize_audio_file(input_text_or_file)
    else:
        input_text = input_text_or_file

    save_text_to_file(input_text, "input")

    detected_lang = detect(input_text)
    is_hinglish = any(ord(c) > 127 for c in input_text) and any(ord(c) < 128 for c in input_text)
    detected_lang = "hi-en" if is_hinglish else detected_lang

    translated_query = translate_text(input_text, detected_lang, "en") if detected_lang != "en" else input_text
    response_text = get_response_from_faiss(translated_query, detected_lang)

    final_response = translate_text(response_text, "en", "hi") if detected_lang in ["hi", "hi-en"] else response_text

    chat_history.append((input_text, final_response))
    save_text_to_file(final_response, "output")

    audio_file = generate_speech(final_response, "hi" if detected_lang in ["hi", "hi-en"] else "en")

    return final_response, audio_file

