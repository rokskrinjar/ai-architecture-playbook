import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import run_aggregation_tool

AGGREGATION_TOOL_SCHEMA = {
    "type": "function",
    "name": "aggregate_data",
    "description": (
        "Group rows by one column and calculate a validated aggregation "
        "over another column."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "group_by_column": {
                "type": "string",
                "description": (
                    "The column used to group the rows."
                ),
            },
            "value_column": {
                "type": "string",
                "description": (
                    "The numeric column used for the calculation."
                ),
            },
            "aggregation": {
                "type": "string",
                "enum": [
                    "sum",
                    "mean",
                    "min",
                    "max",
                    "count",
                ],
                "description": (
                    "The aggregation operation to perform."
                ),
            },
            "sort_order": {
                "type": "string",
                "enum": [
                    "ascending",
                    "descending",
                ],
                "description": (
                    "How to sort the calculated result."
                ),
            },
        },
        "required": [
            "group_by_column",
            "value_column",
            "aggregation",
            "sort_order",
        ],
        "additionalProperties": False,
    },
}


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def request_tool_call(
    question,
    dataframe,
):
    """
    Ask the model to select an analytical tool.

    Args:
        question: Business question entered by the user.
        dataframe: DataFrame containing the selected worksheet.

    Returns:
        The complete OpenAI response.
    """

    column_names = dataframe.columns.tolist()

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=(
            "You are a business data analyst. "
            "Use only the provided analytical tools. "
            "Never calculate business metrics yourself. "
            "Only reference columns that exist in the supplied dataset."
        ),
        input=(
            f"Available columns: {column_names}\n\n"
            f"Business question: {question}"
        ),
        tools=[
            AGGREGATION_TOOL_SCHEMA,
        ],
        tool_choice="required",
    )

    return response


def request_final_answer(
    previous_response_id,
    tool_call_id,
    tool_result,
):
    """
    Send a trusted tool result back to the model.

    Args:
        previous_response_id: ID of the response that requested the tool.
        tool_call_id: ID of the specific tool call.
        tool_result: Dictionary returned by the trusted Python tool.

    Returns:
        The model's final business-friendly answer.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        previous_response_id=previous_response_id,
        instructions=(
            "Explain the verified tool result in clear business language. "
            "Do not invent values or perform additional calculations. "
            "State the main conclusion first, then briefly support it "
            "with the relevant result."
        ),
        input=[
            {
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": json.dumps(tool_result),
            }
        ],
    )

    return response.output_text


def execute_tool(
    tool_name,
    tool_arguments,
    dataframe,
):
    """
    Execute one approved analytical tool.

    Args:
        tool_name: Name requested by the model.
        tool_arguments: Dictionary of arguments requested by the model.
        dataframe: pandas DataFrame used by the tool.

    Returns:
        A serializable dictionary containing the tool result.
    """

    if tool_name == "aggregate_data":
        return run_aggregation_tool(
            dataframe=dataframe,
            group_by_column=tool_arguments["group_by_column"],
            value_column=tool_arguments["value_column"],
            aggregation=tool_arguments["aggregation"],
            sort_order=tool_arguments["sort_order"],
        )

    raise ValueError(
        f"Unknown or unauthorized tool: {tool_name}"
    )

def upload_workbook_to_openai(uploaded_file):
    """
    Upload the Excel workbook to OpenAI for flexible analysis.

    Args:
        uploaded_file: File received from Streamlit.

    Returns:
        The OpenAI file ID.
    """

    uploaded_file.seek(0)

    openai_file = client.files.create(
        file=uploaded_file,
        purpose="user_data",
    )

    return openai_file.id


def analyze_workbook_flexibly(
    file_id,
    question,
):
    """
    Ask the model to analyze an Excel workbook using Code Interpreter.

    Args:
        file_id: OpenAI file ID for the uploaded workbook.
        question: Business question entered by the user.

    Returns:
        The complete OpenAI response.
    """

    response = client.responses.create(
        model="gpt-5.6",
        instructions=(
            "You are a careful business data analyst. "
            "Use the python tool to inspect and analyze the uploaded Excel workbook. "
            "Read all relevant worksheets and join them when necessary. "
            "Perform calculations in Python rather than estimating values. "
            "State the business conclusion first, then briefly explain the calculation. "
            "Mention which worksheets were used. "
            "Do not invent columns or values."
        ),
        input=question,
        tools=[
            {
                "type": "code_interpreter",
                "container": {
                    "type": "auto",
                    "memory_limit": "1g",
                    "file_ids": [file_id],
                },
            }
        ],
        tool_choice="required",
    )

    return response

def extract_code_interpreter_trace(response):
    """
    Extract Code Interpreter execution details from an OpenAI response.

    Args:
        response: Complete response returned by the Responses API.

    Returns:
        A list of dictionaries containing execution trace details.
    """

    trace_items = []

    for output_item in response.output:
        if output_item.type == "code_interpreter_call":
            trace_items.append(
                {
                    "tool": "code_interpreter",
                    "status": output_item.status,
                    "container_id": output_item.container_id,
                    "code": output_item.code,
                    "outputs": output_item.outputs,
                }
            )

    return trace_items