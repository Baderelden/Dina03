import os
from typing import List

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# ---------- Configuration ----------

AASU_NAME = "Abdullah Al-Salem University (AASU)"

MODEL_OPTIONS = {
    "GPT-4.1": "gpt-4.1",
    "GPT-4o": "gpt-4o",
    "GPT-4o mini": "gpt-4o-mini",
}

UNIVERSITY_OPTIONS = [
    "Qatar - Qatar University",
    "Qatar - Hamad Bin Khalifa University",
    "Bahrain - University of Bahrain",
    "Oman - Sultan Qaboos University",
    "UAE - Zayed University",
    "UAE - Khalifa University",
    "UAE  - Mohamed bin Zayed University of Artificial Intelligence – MBZUAI",
    "Saudi - King Saud University",
    "Saudi - King Abdulaziz University",
    "Saudi - King Fahd University of Petroleum and Minerals",
    "Saudi - King Abdullah University of Science and Technology – KAUST",
]

COMPARISON_TYPES = [
    "Academic Colleges",
    "Academic Courses – Overview",
    "Academic Courses – Detailed",
    "Research",
]

DISCIPLINE_OPTIONS = [
    "Computing & IT",
    "Engineering",
    "Business & Management",
    "Science",
    "Medicine & Health",
    "Law & Humanities",
    "Other",
]


# ---------- Helper functions ----------

def load_files_content(files: List) -> str:
    contents = []
    max_chars_per_file = 8000

    for f in files:
        try:
            raw = f.read()
            text = raw.decode("utf-8", errors="ignore")
            if len(text) > max_chars_per_file:
                text = text[:max_chars_per_file] + "\n\n...[truncated]..."
            contents.append(f"\n--- File: {f.name} ---\n{text}")
        except Exception as e:
            contents.append(f"\n--- File: {f.name} ---\n[Could not read file: {e}]")

    return "\n".join(contents)


def build_prompt(
    aasu_name: str,
    target_university: str,
    comparison_type: str,
    extra_comments: str,
    files_text: str,
    level_filter: str,
    discipline_filters: List[str],
    research_depth_flag: bool,
) -> List:

    level_text = {
        "All levels": "Consider both undergraduate and postgraduate levels.",
        "Undergraduate only": "Focus only on undergraduate (bachelor-level) programmes.",
        "Postgraduate only": "Focus only on postgraduate (masters and doctoral) programmes.",
    }.get(level_filter, "Consider both undergraduate and postgraduate levels.")

    if discipline_filters:
        discipline_text = (
            "Focus in particular on the following disciplines: "
            + ", ".join(discipline_filters)
            + "."
        )
    else:
        discipline_text = "Consider all relevant disciplines; do not limit to a single field."

    research_extra = ""
    if comparison_type == "Research":
        research_extra = """
For research comparisons:
- Highlight research strengths and focus areas in the relevant disciplines.
- Comment on research centres, institutes and laboratories where possible.
- Comment on opportunities and risks for strategic collaboration with AASU.
"""
        if research_depth_flag:
            research_extra += """
Place particular emphasis on:
- Research rankings and reputation, where known.
- Publication output and international collaboration.
- Alignment with GCC and national strategic priorities.
"""

    system_prompt = f"""
You are an expert in higher education policy and research strategy in the GCC.
Always compare other universities against {aasu_name}.
""".strip()

    user_prompt = f"""
Compare:

Base: {aasu_name}
Target: {target_university}

Comparison type: {comparison_type}
Level filter: {level_filter}
{level_text}

Disciplines: {", ".join(discipline_filters) if discipline_filters else "[All disciplines]"}
{discipline_text}

Additional notes:
{extra_comments if extra_comments.strip() else "[None]"}

{research_extra}

Uploaded documents (context):
{files_text if files_text else "[No files uploaded]"}
""".strip()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    return messages


def call_llm(model_name: str, messages: List):
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.3,
    )
    response = llm.invoke(messages)
    return response.content


# ---------- Streamlit UI ----------

def main():
    st.set_page_config(
        page_title="AASU GCC Programme Comparison",
        layout="wide",
    )

    st.title("AASU – GCC University Programme Comparison Tool")
    st.markdown(
        f"""
This tool compares **{AASU_NAME}** with selected GCC universities.
"""
    )

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        model_label = st.selectbox("ChatGPT model", list(MODEL_OPTIONS.keys()))
        model_name = MODEL_OPTIONS[model_label]

        st.markdown("---")
        st.header("Filters")

        level_filter = st.radio(
            "Study level",
            ["All levels", "Undergraduate only", "Postgraduate only"],
            index=0,
        )

        discipline_filters = st.multiselect(
            "Discipline focus (optional)",
            DISCIPLINE_OPTIONS,
        )

        st.markdown("---")
        st.header("OpenAI API")
        api_key = st.text_input("OpenAI API key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Please enter your OpenAI API key to continue.")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Configuration")

        university = st.selectbox(
            "Select GCC university",
            UNIVERSITY_OPTIONS,
        )

        comparison_type = st.selectbox(
            "Comparison focus",
            COMPARISON_TYPES,
        )

        research_depth_flag = False
        if comparison_type == "Research":
            research_depth_flag = st.checkbox(
                "Deep research mode",
                value=True,
            )

        extra_comments = st.text_area(
            "Extra comments (optional)",
            height=140,
        )

        uploaded_files = st.file_uploader(
            "Upload AASU documents",
            accept_multiple_files=True,
        )

        run_button = st.button("Generate comparison", type="primary")

    with col2:
        st.subheader("Comparison result")

        if run_button:
            try:
                files_text = ""
                if uploaded_files:
                    with st.spinner("Reading files..."):
                        files_text = load_files_content(uploaded_files)

                with st.spinner("Generating report..."):
                    messages = build_prompt(
                        AASU_NAME,
                        university,
                        comparison_type,
                        extra_comments,
                        files_text,
                        level_filter,
                        discipline_filters,
                        research_depth_flag,
                    )
                    result = call_llm(model_name, messages)

                st.markdown(result)

                # ---- SAVE BUTTON ----
                st.download_button(
                    label="💾 Save Report",
                    data=result,
                    file_name="aasu_comparison_report.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.info("Select your options, then click **Generate comparison**.")


if __name__ == "__main__":
    main()
