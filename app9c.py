#import streamlit as st
#from langchain import PromptTemplate, LLMChain
#from langchain.llms import OpenAI
#import openai
#from audio_recorder_streamlit import audio_recorder
#import time
#import openai
#import base64

import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI as LangChainOpenAI  # rename to avoid clash
from openai import OpenAI as OpenAIClient, AuthenticationError  # SDK client + exception
from audio_recorder_streamlit import audio_recorder
import time
import base64
from openai import RateLimitError

def transcribe_audio(client, audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript= client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text

def text_to_audio(client, text, audio_path, nVoice):
    response = client.audio.speech.create(model="tts-1", voice="ash", input=text)
    response.stream_to_file(audio_path)

def auto_play_audio(audio_file, ph2):
    with open(audio_file, "rb") as audio_file:
        audio_bytes=audio_file.read()
    base64_audio=base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
    ph2.markdown(audio_html, unsafe_allow_html=True)
        
# Sidebar for optional inputs
st.sidebar.header("Options")
history_file_name = st.sidebar.text_input("Enter the file name to save history:", value="chat_history.txt")
st.sidebar.write("You can optionally upload a file for context:")
uploaded_file = st.sidebar.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])
# Main Title and Logo
col1, col2 = st.columns([3, 1])
with col1:
    st.title("KMMS AI Simulator V9.b - No Feedback")
with col2:
    st.image("logo1.jpg", width=300)
    #st.image("logo2.jpg", width=300)

st.write('''
Instructions:\n
1- Choose a patient scenario (click on Cases 1) or upload your own case file.\n
2- Interact with the virtual patient by asking relevant clinical questions.

3- The patient’s responses will reflect their symptoms and knowledge as an actual patient who does not yet know their diagnosis.

4- Use the information gathered to form and refine your differential diagnosis.

5- Continue exploring the case until you feel confident in your final diagnosis.
''')
#st.markdown("---")

# Load predefined cases
with open("case05.txt", "r") as f:
    case1_text = f.read()


# Select Case
st.header("Select a Case")
if st.button("Case 1"):
    cVoice = "ash"
    st.session_state["selected_case"] = case1_text
    st.session_state["file_name"] = "case05.txt"
else:
    cVoice = "echo"
    

file_content = ""
file_name = "Uploaded file"
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.session_state["file_name"] = uploaded_file.name

if "selected_case" in st.session_state:
    file_content = st.session_state["selected_case"]
    file_name = st.session_state["file_name"]

st.markdown(f"**File Name:** {file_name}")
#st.markdown("---")

openai_api_key = st.secrets["OPENAI_API_KEY"]
#llm2 = openai.OpenAI(api_key=openai_api_key)
llm2 = OpenAIClient(api_key=openai_api_key)


# Ask the Patient Section
st.header("Ask the Virtual Patient")
# st.write("Click on the voice recorder to ask question")
recorded_audio = audio_recorder()
placeholder = st.empty()
prompt = placeholder.text_input("Or type your question:")
placeholder2 = st.empty()

if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

if recorded_audio:
    audio_file = "audio.mp3"
    with open(audio_file, "wb") as f:
        f.write(recorded_audio)
    transcribed_text=transcribe_audio(llm2, audio_file)
    prompt = placeholder.text_input("Or type your question:", transcribed_text)
    
if "last_prompt" not in st.session_state:
    st.session_state["last_prompt"] = None
if prompt and prompt != st.session_state["last_prompt"]:
    st.session_state["last_prompt"] = prompt
    #with st.spinner('Processing...'):
    #    time.sleep(2)
    #llm = OpenAI(api_key=openai_api_key)
    llm = LangChainOpenAI(api_key=openai_api_key)
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
    
    #try:
    #    llm_chain = LLMChain(prompt=prompt_template, llm=llm)
    #    response = llm_chain.run(user_prompt=prompt, file_content=file_content)
    response = ""
    try:
        llm_chain = LLMChain(prompt=prompt_template, llm=llm)
        # simple backoff retry (3 attempts)
        for attempt in range(3):
            try:
                response = llm_chain.run(user_prompt=prompt, file_content=file_content)
                break
            except RateLimitError:
                if attempt == 2:
                    st.warning("Rate limit reached. Please wait a moment and try again.")
                    st.stop()
                time.sleep(2 * (attempt + 1))  # 2s, 4s, 6s
    except AuthenticationError:
        st.error("Authentication failed. Please check your API key / Streamlit secrets.")
        st.stop()

    st.session_state["qa_history"].append({"question": prompt, "answer": response})

    with open(history_file_name, "a") as file:
        file.write(f"File Name: {file_name}\n")
        file.write(f"Q: {prompt}\n")
        file.write(f"A: {response}\n")
        file.write("\n")

    st.markdown(f"**Patient Response:** {response}")
    response_audio_file = "audio_response.mp3"
    text_to_audio(llm2, response, response_audio_file, cVoice)
    #placeholder2.audio(response_audio_file)
    auto_play_audio(response_audio_file, placeholder2)

#st.markdown("---")

# Q&A History Section
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

## Diagnosis Section
#st.header("Your Diagnosis")
#user_diagnosis = st.text_area("Provide your diagnosis below:")
#if st.button("Send Diagnosis"):
#    with open(history_file_name, "a") as file:
#        file.write("### User Diagnosis:\n")
#        file.write(user_diagnosis + "\n")
#    st.session_state["qa_history"].append({"question": "User Diagnosis", "answer": user_diagnosis})
#    st.success("Diagnosis added to the file and history.")
