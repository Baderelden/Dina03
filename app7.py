import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import time

# Title
st.title("AI Simulator")

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

st.write("Ask the patient")

# User question input
prompt = st.text_input("Your question:")

# Divider
st.divider()

# Log questions and answers
if "chat_log" not in st.session_state:
    st.session_state["chat_log"] = []

if prompt:
    with st.spinner('hmmmmmmm...'):
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
        
        # Display ChatGPT's response
        st.write(f"Patient: {response}")
        
        # Log the conversation
        st.session_state["chat_log"].append({"question": prompt, "answer": response})

# Display chat log
st.divider()
st.write("### Chat Log")
for idx, entry in enumerate(st.session_state["chat_log"]):
    st.write(f"**Q{idx + 1}:** {entry['question']}")
    st.write(f"**A{idx + 1}:** {entry['answer']}")

# User input box at the end
st.divider()
st.write("### Your Answer")
user_answer = st.text_area("Please input your answer here:")
