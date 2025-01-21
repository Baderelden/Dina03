import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import openai
import av
import tempfile
import os
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import time
from pydub import AudioSegment

# --- Your existing imports and code here ---

# --- Example function to handle audio frames ---
def audio_frame_callback(frame):
    """
    This callback receives a PyAV frame from webrtc_streamer and returns it.
    We’ll collect the raw audio data here for further processing.
    """
    audio = frame.to_ndarray()
    return av.AudioFrame.from_ndarray(audio, layout=frame.layout.name)

# Title or other UI elements:
st.title("KMMS AI Simulator with Voice Input")

# 1. Create a Streamlit webrtc component to capture microphone input.
#    This snippet captures audio in real-time, but we still need to process
#    it as small recorded chunks for Whisper.
webrtc_ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDONLY,
    audio_frame_callback=audio_frame_callback,
    media_stream_constraints={
        "audio": True,
        "video": False
    },
    async_processing=True,
)

# 2. Once the user stops recording or if you want to provide a 'Record'/'Stop' button,
#    you can then process the recorded audio to a temporary file and send it to Whisper.

# We'll provide a simple button for manual finalisation of the recording:
if st.button("Transcribe Audio"):
    if webrtc_ctx.state.playback_buffer:
        # The playback buffer holds the recorded audio frames
        wav_bytes = webrtc_ctx.state.playback_buffer.tobytes()
        
        # 2a. Save the raw audio into a temporary WAV file.
        temp_dir = tempfile.TemporaryDirectory()
        temp_wav_path = os.path.join(temp_dir.name, "temp_audio.wav")
        
        # Use pydub to ensure proper WAV formatting
        audio_segment = AudioSegment(
            data=wav_bytes,
            sample_width=2,  # 16-bit audio
            frame_rate=webrtc_ctx.state.playback_buffer.sample_rate,
            channels=1
        )
        audio_segment.export(temp_wav_path, format="wav")
        
        st.info("Transcribing audio with OpenAI Whisper...")
        
        # 2b. Call the OpenAI Whisper API to transcribe the audio file
        # (You need to have openai_api_key defined somewhere in your app)
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        
        # Note: This is not truly streaming, but rather sending the captured chunk
        # to the API each time the user presses 'Transcribe Audio'.
        with open(temp_wav_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        
        # 2c. The returned transcript is a dictionary containing a 'text' field
        st.success(f"Transcribed text: {transcript['text']}")
        
        # Now you can feed the transcript text to your existing LLM chain.
        
        user_prompt = transcript["text"]
        
        # Construct your LLM chain similarly to your existing text input approach
        template = """
        You are a virtual patient. Below is additional context from a file or case:
        {file_content}

        The user asks: {user_prompt}
        Please respond as helpfully and accurately as possible.
        """

        prompt_template = PromptTemplate(
            input_variables=["user_prompt", "file_content"],
            template=template
        )
        
        llm = OpenAI(api_key=openai.api_key)
        llm_chain = LLMChain(prompt=prompt_template, llm=llm)

        # Example: Suppose 'file_content' is your selected_case or your uploaded file content
        # In your existing code, you might have this in st.session_state or similar
        file_content = st.session_state.get("selected_case", "No case selected.")

        response = llm_chain.run(user_prompt=user_prompt, file_content=file_content)

        st.markdown(f"**Patient Response (from voice input):** {response}")
        
        # Optional: Add to history or further logging if you wish
        if "qa_history" not in st.session_state:
            st.session_state["qa_history"] = []
        st.session_state["qa_history"].append({"question": user_prompt, "answer": response})

    else:
        st.error("No audio has been recorded yet. Please speak into the microphone.")

# --- The remainder of your app logic (history display, admin, etc.) can follow ---
