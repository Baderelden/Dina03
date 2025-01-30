import streamlit as st
import time
import os
import base64

# For audio recording in Streamlit
from streamlit_audio_recorder import audio_recorder

# For speech recognition
import speech_recognition as sr

# For text-to-speech
from gtts import gTTS

from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI

# ------------------------------
# 1. SIDEBAR FOR OPTIONAL INPUTS
# ------------------------------
st.sidebar.header("Options")
history_file_name = st.sidebar.text_input("Enter the file name to save history:", value="chat_history.txt")
st.sidebar.write("You can optionally upload a file for context:")
uploaded_file = st.sidebar.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])

# ------------------------------
# 2. MAIN TITLE AND LOGOS
# ------------------------------
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("KMMS AI Simulator V6.e")
with col2:
    st.image("logo1.jpg", width=300)
with col3:
    st.image("logo2.jpg", width=300)

st.write('''
**Instructions**:
1. Choose a patient scenario (from Cases 1 or 2) or upload your own case file.  
2. Interact with the virtual patient by asking relevant clinical questions.  
3. The patient’s responses will reflect their symptoms and knowledge as an actual patient who does not yet know their diagnosis.  
4. Use the information gathered to form and refine your differential diagnosis.  
5. Continue exploring the case until you feel confident in your final diagnosis.
''')

# ------------------------------
# 3. LOAD PREDEFINED CASES
# ------------------------------
with open("case4.txt", "r") as f:
    case1_text = f.read()
with open("case5.txt", "r") as f:
    case2_text = f.read()

# ------------------------------
# 4. SELECT CASE
# ------------------------------
st.header("Select a Case")
if st.button("Case 1"):
    st.session_state["selected_case"] = case1_text
    st.session_state["file_name"] = "case4.txt"
if st.button("Case 2"):
    st.session_state["selected_case"] = case2_text
    st.session_state["file_name"] = "case5.txt"

file_content = ""
file_name = "Uploaded file"
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.session_state["file_name"] = uploaded_file.name

if "selected_case" in st.session_state:
    file_content = st.session_state["selected_case"]
    file_name = st.session_state["file_name"]

st.markdown(f"**File Name:** {file_name}")

# ------------------------------
# 5. ASK THE PATIENT SECTION
# ------------------------------
st.header("Ask the Virtual Patient")

# Initialise Q&A history if it doesn't exist
if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

# --- Text input for user’s prompt ---
text_prompt = st.text_input("Type your question here:")

# --- Audio recorder for user’s prompt ---
st.write("Or record your question:")
audio_bytes = audio_recorder()

# Convert audio to text if audio is recorded
voice_prompt = ""
if audio_bytes:
    st.write("Processing your recorded audio...")
    with open("temp_recorded.wav", "wb") as f:
        f.write(audio_bytes)

    recogniser = sr.Recognizer()
    with sr.AudioFile("temp_recorded.wav") as source:
        audio_data = recogniser.record(source)
    try:
        voice_prompt = recogniser.recognize_google(audio_data)
        st.write(f"Transcribed Text: **{voice_prompt}**")
    except sr.UnknownValueError:
        st.warning("Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")

# Decide final prompt to send
final_prompt = ""
if text_prompt.strip():
    final_prompt = text_prompt.strip()
elif voice_prompt.strip():
    final_prompt = voice_prompt.strip()

if final_prompt:
    with st.spinner('Generating response...'):
        time.sleep(2)
    openai_api_key = st.secrets["OPENAI_API_KEY"]  # or your own method of retrieval
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

    try:
        llm_chain = LLMChain(prompt=prompt_template, llm=llm)
        response = llm_chain.run(user_prompt=final_prompt, file_content=file_content)
    except Exception as e:
        st.error(f"Error from LLM: {e}")
        response = ""

    # Store Q&A in session
    st.session_state["qa_history"].append({"question": final_prompt, "answer": response})

    # Write Q&A to local history file
    with open(history_file_name, "a", encoding="utf-8") as file:
        file.write(f"File Name: {file_name}\n")
        file.write(f"Q: {final_prompt}\n")
        file.write(f"A: {response}\n\n")

    # Show response text
    st.markdown(f"**Patient Response:** {response}")

    # ----------------------
    # 6. CONVERT RESPONSE TO AUDIO
    # ----------------------
    if response.strip():
        tts = gTTS(response, lang='en')  # British English code is still 'en'; 
                                         # if you want a specific accent, 
                                         # you might try `en-uk` or different TTS services.
        tts.save("response_audio.mp3")

        # Encode the MP3 to base64
        with open("response_audio.mp3", "rb") as f:
            audio_data = f.read()
        b64 = base64.b64encode(audio_data).decode()
        
        # Display audio player
        st.audio(f"data:audio/mp3;base64,{b64}", format="audio/mp3")

# ------------------------------
# 7. Q&A HISTORY SECTION
# ------------------------------
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

# ------------------------------
# 8. ADMIN SECTION (OPTIONAL)
# ------------------------------
st.title("For Admin Use ONLY")

admin_input = st.text_input("Enter the admin code:")
# Generate Analysis Section
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
                
                Provide constructive feedback on the questions asked provided.
                """

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
            st.error("This is for admin use only – please ensure the code is correct.")
    else:
        st.error("Please ensure both Q&A history and admin code are provided.")
