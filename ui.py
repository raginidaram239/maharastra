import os
import base64
import streamlit as st
import speech_recognition as sr
from main import process_input
from datetime import datetime

st.set_page_config(page_title="🗣️ VerbalAI Chatbot", layout="wide")

# Set transparent background wallpaper
def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

if os.path.exists("wallpaper.png"):
    wallpaper_base64 = get_base64_of_image("wallpaper.png")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255,255,255,0.80), rgba(255,255,255,0.80)),
                        url("data:image/png;base64,{wallpaper_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .message-bubble {{
            padding: 1rem;
            border-radius: 1rem;
            margin: 0.5rem 0;
            max-width: 70%;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .user-message {{
            background-color: #DCF8C6;
            align-self: flex-end;
        }}
        .bot-message {{
            background-color: #F1F0F0;
            align-self: flex-start;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

st.markdown("<h1 style='text-align: center;'>🗣️ VerbalAI Chatbot</h1>", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        with st.spinner("🎤 Listening... Speak now!"):
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
    try:
        return recognizer.recognize_google(audio)
    except Exception as e:
        st.error(f"❌ Could not recognize speech: {e}")
        return None

def display_response(user_input_or_file):
    if user_input_or_file:
        with st.spinner("🤖 Generating response..."):
            response_text, voice_filename = process_input(user_input_or_file)
            timestamp = datetime.now().strftime("%H:%M")

            st.session_state.chat_history.append(("🧑 You", user_input_or_file if isinstance(user_input_or_file, str) else "🎵 Audio File", "user", timestamp))
            st.session_state.chat_history.append(("🤖 Chatbot", response_text, "bot", timestamp))

        for role, message, msg_type, time in st.session_state.chat_history:
            style_class = "user-message" if msg_type == "user" else "bot-message"
            alignment = "right" if msg_type == "user" else "left"
            avatar = "🧑" if msg_type == "user" else "🤖"
            st.markdown(
                f"<div style='display: flex; justify-content: {alignment};'>"
                f"<div class='message-bubble {style_class}'>"
                f"<strong>{avatar} {role}</strong><br>{message}<br><small>{time}</small>"
                f"</div></div>",
                unsafe_allow_html=True
            )

        if os.path.exists(voice_filename):
            st.audio(voice_filename, format="audio/wav")
            with open(voice_filename, "rb") as file:
                st.download_button("⬇️ Download Response Audio", file, "chat_response.wav", "audio/wav")

# Sidebar Input Selector
with st.sidebar:
    st.header("🎛️ Select Input Mode")
    input_option = st.radio("", ("Text", "Live Voice", "Upload Audio File"))
    st.markdown("---")
    st.caption("🔊 Audio types supported: WAV, M4A")
    st.caption("🏁 Tip: Keep queries short and clear")
    st.markdown("Made with ❤️ using Streamlit")

st.markdown("## 🧠 Chat with VerbalAI")

# Input Options
if input_option == "Text":
    user_input = st.text_input("💬 Enter your query:")
    if st.button("🚀 Submit", use_container_width=True):
        display_response(user_input)

elif input_option == "Live Voice":
    if st.button("🎙️ Start Recording", use_container_width=True):
        user_input = recognize_speech()
        if user_input:
            display_response(user_input)

elif input_option == "Upload Audio File":
    uploaded_file = st.file_uploader("📤 Upload a WAV or M4A file", type=["wav", "m4a"])
    if uploaded_file and st.button("🔍 Process Audio", use_container_width=True):
        temp_file_path = os.path.join("input", uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.read())
        display_response(temp_file_path)




# import os
# import base64
# import streamlit as st
# import speech_recognition as sr
# from main import process_input
# from datetime import datetime

# st.set_page_config(page_title="🗣️ VerbalAI Chatbot", layout="wide")

# # Set background
# def get_base64_of_image(image_path):
#     with open(image_path, "rb") as img_file:
#         return base64.b64encode(img_file.read()).decode()

# if os.path.exists("wallpaper.png"):
#     wallpaper_base64 = get_base64_of_image("wallpaper.png")
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: url("data:image/png;base64,{wallpaper_base64}");
#             background-size: cover;
#             background-repeat: no-repeat;
#             background-attachment: fixed;
#         }}
#         .message-bubble {{
#             padding: 1rem;
#             border-radius: 1rem;
#             margin-bottom: 0.5rem;
#             max-width: 70%;
#         }}
#         .user-message {{
#             background-color: #DCF8C6;
#             align-self: flex-end;
#         }}
#         .bot-message {{
#             background-color: #F1F0F0;
#             align-self: flex-start;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# st.markdown("<h1 style='text-align: center;'>🗣️ VerbalAI Chatbot</h1>", unsafe_allow_html=True)

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# def recognize_speech():
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         with st.spinner("🎤 Listening... Speak now!"):
#             recognizer.adjust_for_ambient_noise(source)
#             audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
#     try:
#         return recognizer.recognize_google(audio)
#     except Exception as e:
#         st.error(f"❌ Could not recognize speech: {e}")
#         return None

# def display_response(user_input_or_file):
#     if user_input_or_file:
#         with st.spinner("🤖 Generating response..."):
#             response_text, voice_filename = process_input(user_input_or_file)
#             timestamp = datetime.now().strftime("%H:%M")

#             st.session_state.chat_history.append(("🧑 You", user_input_or_file if isinstance(user_input_or_file, str) else "🎵 Audio File", "user", timestamp))
#             st.session_state.chat_history.append(("🤖 Chatbot", response_text, "bot", timestamp))

#         for role, message, msg_type, time in st.session_state.chat_history:
#             style_class = "user-message" if msg_type == "user" else "bot-message"
#             alignment = "right" if msg_type == "user" else "left"
#             st.markdown(
#                 f"<div style='display: flex; justify-content: {alignment};'><div class='message-bubble {style_class}'><strong>{role}</strong> <br>{message} <br><small>{time}</small></div></div>",
#                 unsafe_allow_html=True
#             )

#         if os.path.exists(voice_filename):
#             st.audio(voice_filename, format="audio/wav")
#             with open(voice_filename, "rb") as file:
#                 st.download_button("⬇️ Download Response Audio", file, "chat_response.wav", "audio/wav")

# # Layout
# with st.sidebar:
#     st.header("🎛️ Select Input Mode")
#     input_option = st.radio("", ("Text", "Live Voice", "Upload Audio File"))
#     st.markdown("---")
#     st.caption("🔊 Audio types supported: WAV, M4A")
#     st.caption("🏁 Tip: Keep queries short and clear")
#     st.markdown("Made with ❤️ using Streamlit")

# st.markdown("## 🧠 Chat with VerbalAI")

# if input_option == "Text":
#     user_input = st.text_input("💬 Enter your query:")
#     if st.button("🚀 Submit", use_container_width=True):
#         display_response(user_input)

# elif input_option == "Live Voice":
#     if st.button("🎙️ Start Recording", use_container_width=True):
#         user_input = recognize_speech()
#         if user_input:
#             display_response(user_input)

# elif input_option == "Upload Audio File":
#     uploaded_file = st.file_uploader("📤 Upload a WAV or M4A file", type=["wav", "m4a"])
#     if uploaded_file and st.button("🔍 Process Audio", use_container_width=True):
#         temp_file_path = os.path.join("input", uploaded_file.name)
#         with open(temp_file_path, "wb") as f:
#             f.write(uploaded_file.read())
#         display_response(temp_file_path)






# import os
# import base64
# import streamlit as st
# import speech_recognition as sr
# from main import process_input

# st.set_page_config(page_title="🗣️ VerbalAI Chatbot", layout="wide")

# def get_base64_of_image(image_path):
#     with open(image_path, "rb") as img_file:
#         return base64.b64encode(img_file.read()).decode()

# if os.path.exists("wallpaper.png"):
#     wallpaper_base64 = get_base64_of_image("wallpaper.png")
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: url("data:image/png;base64,{wallpaper_base64}");
#             background-size: cover;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# st.title("🗣️ VerbalAI Chatbot")

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# def recognize_speech():
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         st.info("🎤 Speak now...")
#         recognizer.adjust_for_ambient_noise(source)
#         audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
#     try:
#         return recognizer.recognize_google(audio)
#     except Exception as e:
#         st.error(f"❌ Could not recognize speech: {e}")
#         return None

# def display_response(user_input_or_file):
#     if user_input_or_file:
#         response_text, voice_filename = process_input(user_input_or_file)
#         st.session_state.chat_history.append(("🧑 You", user_input_or_file if isinstance(user_input_or_file, str) else "🎵 Audio File"))
#         st.session_state.chat_history.append(("🤖 Chatbot", response_text))

#         for role, message in st.session_state.chat_history:
#             st.write(f"**{role}:** {message}")

#         if os.path.exists(voice_filename):
#             st.audio(voice_filename, format="audio/wav")
#             with open(voice_filename, "rb") as file:
#                 st.download_button("⬇️ Download Response", file, "chat_response.wav", "audio/wav")

# input_option = st.radio("Choose Input Type:", ("Text", "Live Voice", "Upload Audio File"))

# if input_option == "Text":
#     user_input = st.text_input("💬 Enter your query:")
#     if st.button("Submit"):
#         display_response(user_input)

# elif input_option == "Live Voice":
#     if st.button("🎙️ Speak Now"):
#         user_input = recognize_speech()
#         if user_input:
#             display_response(user_input)

# elif input_option == "Upload Audio File":
#     uploaded_file = st.file_uploader("Upload a WAV or M4A file", type=["wav", "m4a"])
#     if uploaded_file and st.button("Process Audio File"):
#         temp_file_path = os.path.join("input", uploaded_file.name)
#         with open(temp_file_path, "wb") as f:
#             f.write(uploaded_file.read())
#         display_response(temp_file_path)
