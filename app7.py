import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import openai
import time
import tempfile
import os

# For TTS
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

# Replace with your own info for the client settings
WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={
        "audio": True,
        "video": False,
    },
)

st.title("KMMS AI Simulator V6.e - With Voice Support")

# Sidebar for optional inputs
st.sidebar.header("Options")
history_file_name = st.sidebar.text_input("Enter the file name to save history:", value="chat_history.txt")

# Provide your own images, logos, or other UI elements here
st.image("logo1.jpg", width=300)
st.image("logo2.jpg", width=300)

st.write('''
Instructions:\n
1. Choose a patient scenario (from Cases 1 or 2) or upload your own case file.\n
2. Interact with the virtual patient by asking relevant clinical questions (text or voice).

3. The patient’s responses will reflect their symptoms and knowledge as an actual patient who does not yet know their diagnosis.

4. Use the information gathered to form and refine your differential diagnosis.

5. Continue exploring the case until you feel confident in your final diagnosis.
''')

# Load predefined cases
with open("case4.txt", "r") as f:
    case1_text = f.read()
with open("case5.txt", "r") as f:
    case2_text = f.read()

# Store session info
if "selected_case" not in st.session_state:
    st.session_state["selected_case"] = ""
if "file_name" not in st.session_state:
    st.session_state["file_name"] = ""

# Case selection
st.header("Select a Case")
if st.button("Case 1"):
    st.session_state["selected_case"] = case1_text
    st.session_state["file_name"] = "case4.txt"
if st.button("Case 2"):
    st.session_state["selected_case"] = case2_text
    st.session_state["file_name"] = "case5.txt"

# You can also allow file uploads
st.sidebar.write("You can optionally upload a file for context:")
uploaded_file = st.sidebar.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])
file_content = ""
file_name = "Uploaded file"

if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.session_state["file_name"] = uploaded_file.name

if st.session_state["selected_case"]:
    file_content = st.session_state["selected_case"]
    file_name = st.session_state["file_name"]

st.markdown(f"**File Name:** {file_name}")

# Q&A History
if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

# Set your OpenAI API key
openai_api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openai_api_key

# --- Helper functions for TTS and STT ---

def text_to_speech(response_text):
    """Convert text to speech using gTTS and return an audio file path."""
    tts = gTTS(text=response_text, lang='en', tld='co.uk')  # 'en' for British accent
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

def play_audio(file_path):
    """Play the audio file in Streamlit."""
    # Convert the MP3 to WAV (so we can use streamlit audio player)
    sound = AudioSegment.from_file(file_path, format="mp3")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
        sound.export(wav_file.name, format="wav")
        st.audio(wav_file.name, format="audio/wav")

def transcribe_audio_to_text(audio_data):
    """Transcribe using OpenAI's Whisper API from raw audio bytes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav.write(audio_data)
        tmp_wav.flush()
        tmp_wav_name = tmp_wav.name

    # Use the OpenAI Whisper API to transcribe
    with open(tmp_wav_name, "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    return transcription["text"]

# --- Streamlit UI for voice input ---
st.header("Ask the Virtual Patient via Voice")
webrtc_ctx = webrtc_streamer(
    key="speech_to_text",
    mode=WebRtcMode.RECVONLY,
    client_settings=WEBRTC_CLIENT_SETTINGS,
    async_processing=True
)

audio_data_buffer = None
if webrtc_ctx.state.playback_audio:
    # This returns the raw bytes of the audio
    audio_data_buffer = webrtc_ctx.audio_receiver.get_frames(timeout=1)

if st.button("Transcribe Voice"):
    if audio_data_buffer:
        # Combine all frames into one byte array
        combined_audio = b"".join([frame.to_ndarray().tobytes() for frame in audio_data_buffer])
        st.info("Transcribing your voice...")
        # transcribe with Whisper
        user_question = transcribe_audio_to_text(combined_audio)
        st.write(f"**Transcribed Text:** {user_question}")

        if user_question.strip():
            # Now feed to your LLM
            with st.spinner('Processing voice question...'):
                time.sleep(2)
            
            llm = OpenAI(api_key=openai_api_key)
            
            template = """
            You are a virtual patient. Below is additional context from a file or a selected case:
            {file_content}

            The user asks (via voice): {user_prompt}
            Please respond as helpfully and accurately as possible.
            """

            prompt_template = PromptTemplate(
                input_variables=["user_prompt", "file_content"],
                template=template
            )
            
            llm_chain = LLMChain(prompt=prompt_template, llm=llm)
            response = llm_chain.run(user_prompt=user_question, file_content=file_content)

            st.session_state["qa_history"].append({"question": user_question, "answer": response})

            # Save to file
            with open(history_file_name, "a") as file:
                file.write(f"File Name: {file_name}\n")
                file.write(f"Q (Voice): {user_question}\n")
                file.write(f"A: {response}\n\n")

            st.markdown(f"**Patient Response:** {response}")

            # Output the TTS
            audio_file_path = text_to_speech(response)
            play_audio(audio_file_path)

        else:
            st.warning("No transcribed text found.")
    else:
        st.warning("No audio to transcribe. Please speak or record again.")

# --- Text-based Interaction (existing code) ---
st.header("Ask the Virtual Patient via Text")
prompt = st.text_input("Enter your question:")
if prompt:
    with st.spinner('Processing...'):
        time.sleep(2)
    
    llm = OpenAI(api_key=openai_api_key)
    
    template = """
    You are a virtual patient. Below is additional context from a file or a selected case:
    {file_content}

    The user asks: {user_prompt}
    Please respond as helpfully and accurately as possible.
    """

    prompt_template = PromptTemplate(
        input_variables=["user_prompt", "file_content"],
        template=template
    )
    
    llm_chain = LLMChain(prompt=prompt_template, llm=llm)
    response = llm_chain.run(user_prompt=prompt, file_content=file_content)

    st.session_state["qa_history"].append({"question": prompt, "answer": response})

    # Save to file
    with open(history_file_name, "a") as file:
        file.write(f"File Name: {file_name}\n")
        file.write(f"Q (Text): {prompt}\n")
        file.write(f"A: {response}\n\n")

    st.markdown(f"**Patient Response:** {response}")

    # Output the TTS if you also want to read the response aloud
    audio_file_path = text_to_speech(response)
    play_audio(audio_file_path)

# Display Q&A history
st.header("Q&A History")
qa_history_text = "\n".join(
    [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in st.session_state["qa_history"]]
)
st.text_area("Conversation History", qa_history_text, height=300, disabled=True)
if st.session_state["qa_history"]:
    history_download = "\n".join(
        [f"File Name: {file_name}\nQ: {qa['question']}\nA: {qa['answer']}\n" for qa in st.session_state["qa_history"]]
    )
    st.download_button(
        label="Download History",
        data=history_download,
        file_name=history_file_name,
        mime="text/plain"
    )

st.markdown("---")

# Admin Section (unchanged from your existing code)
st.title("For Admin Use ONLY")

admin_input = st.text_input("Enter the admin code:")
st.header("Generate Analysis")
if st.button("Generate Feedback"):
    if st.session_state["qa_history"]:
        if admin_input == "admin1":
            with st.spinner('Generating analysis...'):
                time.sleep(2)
                analysis_llm = OpenAI(api_key=openai_api_key)
    
                analysis_template = """
                Based on the following Q&A history, provide detailed feedback:

                Q&A History:
                {qa_history}

                Provide constructive feedback on the questions asked.
                """

                from langchain import PromptTemplate, LLMChain
                analysis_prompt = PromptTemplate(
                    input_variables=["qa_history"],
                    template=analysis_template
                )
    
                analysis_chain = LLMChain(prompt=analysis_prompt, llm=analysis_llm)
                analysis_response = analysis_chain.run(
                    qa_history=qa_history_text
                )
    
                st.subheader("Analysis Feedback")
                st.markdown(analysis_response)
        else:
            st.error("This is for admin use only - please make sure the code is correct.")
    else:
        st.error("Please ensure Q&A history is available.")
