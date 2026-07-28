import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

if "meeting_analysis" not in st.session_state:
    st.session_state.meeting_analysis = None

if "usage" not in st.session_state:
    st.session_state.usage = None

MAX_MEETING_NOTES_CHARACTERS = 12_000
MEETING_ASSISTANT_INSTRUCTIONS = """
You are an enterprise meeting assistant.

Analyze the meeting notes and return:

## Executive Summary
Provide a concise summary of the meeting.

## Key Decisions
List decisions that were explicitly made.

## Action Items
For every action item include:
- Task
- Owner
- Deadline

If the owner or deadline is not explicitly mentioned, write "Not specified".

## Risks and Open Questions
List unresolved questions, risks, and dependencies.

Do not invent information that is not present in the meeting notes.
"""


# Load environment variables from the local .env file
load_dotenv()

# Read the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Basic Streamlit page
st.title("First LLM Application")
st.write("Testing the connection to the OpenAI API.")

# Stop the application if the key is missing
if not api_key:
    st.error("OPENAI_API_KEY was not found in the .env file.")
    st.stop()

# Create an OpenAI API client
client = OpenAI(api_key=api_key)

try:
    # Request the models available to this API project
    models_response = client.models.list()

    # Extract and alphabetically sort model IDs
    available_model_ids = {
    model.id for model in models_response.data
    }

    preferred_models = [
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-4.1-mini",
    ]

    model_ids = [
        model
        for model in preferred_models
        if model in available_model_ids
    ]

    # Stop before creating the dropdown if no supported models exist
    if not model_ids:
        st.error("No supported text-generation models were found.")
        st.stop()

    st.success("Connection to the OpenAI API was successful.")

    selected_model = st.selectbox(
        "Select an available model:",
        options=model_ids,
    )

    st.write("Selected model:", selected_model)

    st.divider()

    meeting_notes = st.text_area(
        "Paste meeting notes:",
        height=250,
        max_chars=MAX_MEETING_NOTES_CHARACTERS,
        placeholder="Example: Dana confirmed that the project deadline is Friday...",
    )

    character_count = len(meeting_notes)

    st.caption(
        f"{character_count:,} / "
        f"{MAX_MEETING_NOTES_CHARACTERS:,} characters"
    )

    analyze_button = st.button("Analyze meeting")

    if analyze_button:
        if not meeting_notes.strip():
            st.warning("Please enter meeting notes before starting the analysis.")
            st.stop()

        if character_count > MAX_MEETING_NOTES_CHARACTERS:
            st.error(
                "The meeting notes are too long. "
                f"Please reduce them to "
                f"{MAX_MEETING_NOTES_CHARACTERS:,} characters."
            )
            st.stop()

        try:
            with st.spinner("Analyzing meeting notes..."):
                response = client.responses.create(
                    model=selected_model,
                    instructions=MEETING_ASSISTANT_INSTRUCTIONS,
                    input=meeting_notes,
                )

            st.session_state.meeting_analysis = response.output_text
            st.session_state.usage = response.usage

        except Exception as error:
            st.error("The meeting analysis failed.")
            st.exception(error)

    if st.session_state.meeting_analysis:
        st.subheader("Meeting Analysis")
        st.markdown(st.session_state.meeting_analysis)

        st.download_button(
            label="Download analysis",
            data=st.session_state.meeting_analysis,
            file_name="meeting-analysis.md",
            mime="text/markdown",
        )

        if st.session_state.usage:
            st.subheader("API Usage")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Input tokens",
                st.session_state.usage.input_tokens,
            )

            col2.metric(
                "Output tokens",
                st.session_state.usage.output_tokens,
            )

            col3.metric(
                "Total tokens",
                st.session_state.usage.total_tokens,
            )

        

except Exception as error:
    st.error("The application could not connect to the OpenAI API.")
    st.exception(error)