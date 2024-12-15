import streamlit as st
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI

st.title("AI Simulator")

st.divider()

# Predefined case texts
case1_text = "This is the predefined text for Case 1."
case2_text = "This is the predefined text for Case 2."
case3_text = "This is the predefined text for Case 3."
case4_text = "This is the predefined text for Case 4."
case5_text = "This is the predefined text for Case 5."

# Create columns for the case buttons to appear side-by-side
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
    # Read the entire file content
    file_content = uploaded_file.read().decode("utf-8")

# If a case has been selected, use that instead of file content
if "selected_case" in st.session_state:
    file_content = st.session_state["selected_case"]

st.write("Ask the patient")

prompt = st.text_input("Your question:")

st.divider()

if prompt:
    st.balloons()
    #openai_api_key = st.secrets["OPENAI_API_KEY"]
    openai_api_key = "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"
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
    st.write(f"Patient: {response}")
