import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


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
        placeholder="Example: Dana confirmed that the project deadline is Friday...",
    )

    analyze_button = st.button("Analyze meeting")

    if analyze_button:
        if not meeting_notes.strip():
            st.warning("Please enter meeting notes before starting the analysis.")
            st.stop()

        prompt = f"""
    You are an enterprise meeting assistant.

    Analyze the following meeting notes and return:

    ## Executive Summary
    A concise summary of the meeting.

    ## Key Decisions
    List the decisions that were made.

    ## Action Items
    For every action item include:
    - Task
    - Owner
    - Deadline

    If the owner or deadline is not explicitly mentioned, write "Not specified".

    ## Risks and Open Questions
    List unresolved questions, risks, or dependencies.

    Meeting notes:
    {meeting_notes}
    """

        try:
            with st.spinner("Analyzing meeting notes..."):
                response = client.responses.create(
                    model=selected_model,
                    input=prompt,
                )

            st.subheader("Meeting Analysis")
            st.markdown(response.output_text)

        except Exception as error:
            st.error("The meeting analysis failed.")
            st.exception(error)

except Exception as error:
    st.error("The application could not connect to the OpenAI API.")
    st.exception(error)