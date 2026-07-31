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