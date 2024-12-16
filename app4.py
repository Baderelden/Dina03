import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import time


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
if col2.button("Case 2"):
    st.session_state["selected_case"] = case2_text
if col3.button("Case 3"):
    st.session_state["selected_case"] = case3_text
if col4.button("Case 4"):
    st.session_state["selected_case"] = case4_text
if col5.button("Case 5"):
    st.session_state["selected_case"] = case5_text

st.divider()

st.write("You can optionally upload a file for context:")
uploaded_file = st.file_uploader("Upload a file (e.g., .txt)", type=["txt", "md", "csv", "json"])

file_content = ""
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")

# If a case has been selected, use that instead of file content
if "selected_case" in st.session_state:
    file_content = st.session_state["selected_case"]

st.write("Ask the patient")

prompt = st.text_input("Your question:")

st.divider()

if prompt:
    #st.balloons()
    with st.spinner('hmmmmmmm...'):
        time.sleep(2)
   # st.success("Done!")
    # Retrieve the API key from Streamlit secrets
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    llm = OpenAI(api_key=OPENAI_API_KEY)

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
    st.write(f"Patient: {response}")
