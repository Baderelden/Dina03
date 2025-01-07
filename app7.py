import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import time

# Main Title and Logos
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("AI Simulator")
with col2:
    st.image("logo.jpg", width=100)
with col3:
    st.image("logo2.jpg", width=100)

st.markdown("---")
st.divider()

# Read predefined texts from external files located in the root folder
with open("case1.txt", "r") as f:
    case1_text = f.read()
with open("case2.txt", "r") as f:
    case2_text = f.read()
with open("case3.txt", "r") as f:
    case3_text = f.read()
with open("case4.txt", "r") as f:
    case4_text = f.read()
with open("case5.txt", "r") as f:
    case5_text = f.read()

# Create columns for the case buttons side-by-side
col1, col2, col3, col4, col5 = st.columns(5)

if col1.button("Case 1"):
    st.session_state["selected_case"] = case1_text
    st.session_state["file_name"] = "case1.txt"
if col2.button("Case 2"):
    st.session_state["selected_case"] = case2_text
    st.session_state["file_name"] = "case2.txt"
if col3.button("Case 3"):
    st.session_state["selected_case"] = case3_text
    st.session_state["file_name"] = "case3.txt"
if col4.button("Case 4"):
    st.session_state["selected_case"] = case4_text
    st.session_state["file_name"] = "case4.txt"
if col5.button("Case 5"):
    st.session_state["selected_case"] = case5_text
    st.session_state["file_name"] = "case5.txt"

st.divider()

# Display file name
if "file_name" in st.session_state:
    st.write(f"**Selected File:** {st.session_state['file_name']}")
else:
    st.write("**Selected File:** None")

st.write("You can optionally upload a file for context:")
uploaded_file = st.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])

file_content = ""
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.session_state["file_name"] = uploaded_file.name

# If a case has been selected, use that instead of file content
if "selected_case" in st.session_state:
    file_content = st.session_state["selected_case"]



# Ask the Patient Section
st.write("Ask the patient")
if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

prompt = st.text_input("Enter your question:")
if prompt:
    with st.spinner('Processing...'):
        time.sleep(2)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
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

# Diagnosis Section
st.header("Your Diagnosis")
user_diagnosis = st.text_area("Provide your diagnosis below:")
if st.button("Send Diagnosis"):
    with open(history_file_name, "a") as file:
        file.write("### User Diagnosis:\n")
        file.write(user_diagnosis + "\n")
    st.session_state["qa_history"].append({"question": "User Diagnosis", "answer": user_diagnosis})
    st.success("Diagnosis added to the file and history.")

# Generate Analysis Section
st.header("Generate Analysis")
if st.button("Generate Feedback"):
    if st.session_state["qa_history"] and user_diagnosis:
        with st.spinner('Generating analysis...'):
            time.sleep(2)
            analysis_llm = OpenAI(api_key=openai_api_key)
            
            analysis_template = """
            Based on the following Q&A history and user diagnosis, provide detailed feedback:

            Q&A History:
            {qa_history}

            User Diagnosis:
            {user_diagnosis}

            Provide constructive feedback on the questions asked and the diagnosis provided.
            """

            analysis_prompt = PromptTemplate(
                input_variables=["qa_history", "user_diagnosis"],
                template=analysis_template
            )

            analysis_chain = LLMChain(prompt=analysis_prompt, llm=analysis_llm)
            analysis_response = analysis_chain.run(
                qa_history=qa_history_text, user_diagnosis=user_diagnosis
            )

            st.subheader("Analysis Feedback")
            st.markdown(analysis_response)
    else:
        st.error("Please ensure both Q&A history and user diagnosis are available.")
