import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import openai
import tempfile

WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
)

st.title("Speech-to-Text with Whisper (No TTS)")

# Replace with your actual OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to transcribe audio to text
def transcribe_audio_to_text(audio_data: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav.write(audio_data)
        tmp_wav.flush()
        tmp_wav_name = tmp_wav.name

    # Use OpenAI Whisper to transcribe
    with open(tmp_wav_name, "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    return transcription["text"]

webrtc_ctx = webrtc_streamer(
    key="speech_to_text",
    mode=WebRtcMode.RECVONLY,
    client_settings=WEBRTC_CLIENT_SETTINGS,
    async_processing=True
)

st.write("Press 'Transcribe Voice' after speaking to capture your audio.")

if st.button("Transcribe Voice"):
    # Make sure we have a valid context and an audio receiver
    if webrtc_ctx and webrtc_ctx.audio_receiver:
        # Grab any available frames
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        if audio_frames:
            # Combine all audio data into a single bytes object
            combined_audio = b"".join(frame.to_ndarray().tobytes() for frame in audio_frames)
            st.info("Transcribing your voice with Whisper...")
            user_question = transcribe_audio_to_text(combined_audio)
            st.write(f"**Transcribed Text:** {user_question}")
        else:
            st.warning("No audio frames received. Please speak again.")
    else:
        st.warning("WebRTC context not initialised or no audio receiver found.")
