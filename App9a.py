@@ -65,60 +57,59 @@ def text_to_speech(text):
    file_name = st.session_state["file_name"]

st.markdown(f"**File Name:** {file_name}")
#st.markdown("---")

# Voice Input Section
# Ask the Patient Section
st.header("Ask the Virtual Patient")
webrtc_ctx = webrtc_streamer(key="example", rtc_configuration=RTC_CONFIGURATION, media_stream_constraints={"audio": True, "video": False})
if webrtc_ctx.state.playing:
    st.text("Please speak now...")
    audio_data = webrtc_ctx.audio_receiver.get_frames(timeout=None)
    # You need to implement processing of audio_data to convert it to text
    prompt = "Converted audio to text here"  # Placeholder for actual conversion logic
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
        
        try:
            llm_chain = LLMChain(prompt=prompt_template, llm=llm)
            response = llm_chain.run(user_prompt=prompt, file_content=file_content)
            text_to_speech(response)  # Speak the response
        except OpenAI.AuthenticationError:
            st.error("Authentication failed. Please check your API key.")
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
    st.session_state["qa_history"].append({"question": prompt, "answer": response})

        with open(history_file_name, "a") as file:
            file.write(f"File Name: {file_name}\n")
            file.write(f"Q: {prompt}\n")
            file.write(f"A: {response}\n")
            file.write("\n")
    with open(history_file_name, "a") as file:
        file.write(f"File Name: {file_name}\n")
        file.write(f"Q: {prompt}\n")
        file.write(f"A: {response}\n")
        file.write("\n")

        st.markdown(f"**Patient Response:** {response}")
    st.markdown(f"**Patient Response:** {response}")
#st.markdown("---")

# Q&A History Section
st.header("Q&A History")
if "qa_history" in st.session_state:
    qa_history_text = "\n".join(
        [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in st.session_state["qa_history"]]
    )
    st.text_area("Conversation History", qa_history_text, height=300, disabled=True)
qa_history_text = "\n".join(
    [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in st.session_state["qa_history"]]
)
st.text_area("Conversation History", qa_history_text, height=300, disabled=True)
if st.session_state["qa_history"]:
    history_download = "\n".join(
        [f"File Name: {file_name}\nQ: {qa['question']}\nA: {qa['answer']}\n" for qa in st.session_state["qa_history"]]
    )
@@ -129,35 +120,53 @@ def text_to_speech(text):
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
st.markdown("---")

# Admin Section
st.title("For Admin Use ONLY")
admin_input = st.text_input("Enter the admin code:")
# Generate Analysis Section
if st.button("Generate Feedback") and admin_input == "admin1":
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
        analysis_response = analysis_chain.run(qa_history=qa_history_text)
        st.subheader("Analysis Feedback")
        st.markdown(analysis_response)
else:
    st.error("This is for admin use only - please make sure the code is correct.")
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
                st.error("This is for admin use only - please make sure the code is correct.")
    else:
        st.error("Please ensure both Q&A history are available.")
