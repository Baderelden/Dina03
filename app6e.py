import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import time

# Sidebar for optional inputs
st.sidebar.header("Options")
history_file_name = st.sidebar.text_input("Enter the file name to save history:", value="chat_history.txt")
st.sidebar.write("You can optionally upload a file for context:")
uploaded_file = st.sidebar.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])

# Main Title and Logo
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("KMMS AI Simulator V6.e")
with col2:
    st.image("logo1.jpg", width=300)
with col3:
    st.image("logo2.jpg", width=300)

st.write('''
Instructions:\n
1- Choose a patient scenario (from Cases 1 or 2) or upload your own case file.\n
2- Interact with the virtual patient by asking relevant clinical questions.

3- The patient’s responses will reflect their symptoms and knowledge as an actual patient who does not yet know their diagnosis.

4- Use the information gathered to form and refine your differential diagnosis.

5- Continue exploring the case until you feel confident in your final diagnosis.
''')
st.markdown("---")

# Load predefined cases
with open("case1.txt", "r") as f:
    case1_text = f.read()
with open("case2.txt", "r") as f:
    case2_text = f.read()

# Select Case
st.header("Select a Case")
if st.button("Case 1"):
    st.session_state["selected_case"] = case1_text
    st.session_state["file_name"] = "case3.txt"
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
st.markdown("---")

# Ask the Patient Section
st.header("Ask the Virtual Patient")
if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

prompt = st.text_input("Enter your question:")
if prompt:
    with st.spinner('Processing...'):
        time.sleep(2)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    llm = OpenAI(api_key=openai_api_key)
    #llm = OpenAI(api_key="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")
    
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
        response = llm_chain.run(user_prompt=prompt, file_content=file_content)
    except OpenAI.AuthenticationError:
        st.error("test - Authentication failed. Please check your API key.")

    st.session_state["qa_history"].append({"question": prompt, "answer": response})

    with open(history_file_name, "a") as file:
        file.write(f"File Name: {file_name}\n")
        file.write(f"Q: {prompt}\n")
        file.write(f"A: {response}\n")
        file.write("\n")

    st.markdown(f"**Patient Response:** {response}")

st.markdown("---")

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

admin_input = st.text_input("Enter the admin code:")
# Generate Analysis Section
st.header("Generate Analysis")
if st.button("Generate Feedback"):
    if st.session_state["qa_history"] and admin_input == "admin1":
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
        st.error("Please ensure both Q&A history and user diagnosis are available.")
