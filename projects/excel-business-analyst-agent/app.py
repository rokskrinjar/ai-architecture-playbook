import pandas as pd
import streamlit as st
import json

from tools import load_worksheet
from agent import (
    execute_tool,
    request_final_answer,
    request_tool_call,
)


st.set_page_config(
    page_title="Excel Business Analyst Agent",
    page_icon="📊",
    layout="wide",
)

st.title("Excel Business Analyst Agent")

st.write(
    "Upload an Excel workbook, inspect its worksheets, "
    "and ask business questions using trusted analytical tools."
)

uploaded_file = st.file_uploader(
    "Upload an Excel workbook",
    type=["xlsx"],
)

if uploaded_file is not None:
    st.success(f"Workbook uploaded: {uploaded_file.name}")

    excel_file = pd.ExcelFile(uploaded_file)

    selected_sheet = st.selectbox(
        "Select a worksheet",
        options=excel_file.sheet_names,
    )

    st.write(f"Selected worksheet: **{selected_sheet}**")

    dataframe = load_worksheet(
        uploaded_file=uploaded_file,
        sheet_name=selected_sheet,
    )

    st.subheader("Data preview")

    st.dataframe(
        dataframe.head(10),
        use_container_width=True,
    )

    st.caption(
        f"{len(dataframe)} rows × {len(dataframe.columns)} columns"
    )

    st.subheader("Column inspection")

    column_details = pd.DataFrame(
        {
            "Column": dataframe.columns,
            "Data type": dataframe.dtypes.astype(str).values,
            "Missing values": dataframe.isna().sum().values,
            "Unique values": dataframe.nunique(dropna=True).values,
        }
    )

    st.dataframe(
        column_details,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("AI tool selection test")

    business_question = st.text_input(
        "Ask a business question",
        value="Which channel generated the most net revenue?",
    )

    if st.button("Ask the agent"):
        with st.spinner("The agent is selecting a tool..."):
            response = request_tool_call(
                question=business_question,
                dataframe=dataframe,
            )

        for output_item in response.output:
            if output_item.type == "function_call":
                tool_name = output_item.name
                tool_arguments = json.loads(output_item.arguments)

                st.write("Requested tool")
                st.code(tool_name)

                st.write("Tool arguments")
                st.json(tool_arguments)

                tool_result = execute_tool(
                    tool_name=tool_name,
                    tool_arguments=tool_arguments,
                    dataframe=dataframe,
                )

                st.write("Tool result")
                st.json(tool_result)

                with st.spinner("The agent is preparing the final answer..."):
                    final_answer = request_final_answer(
                        previous_response_id=response.id,
                        tool_call_id=output_item.call_id,
                        tool_result=tool_result,
                    )

                st.write("Final answer")
                st.markdown(final_answer)