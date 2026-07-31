import pandas as pd

def format_business_value(value):
    """
    Format numeric values for business-friendly display.

    Args:
        value: Value returned by the analytical calculation.

    Returns:
        A formatted string for numeric values.
        Non-numeric values are returned unchanged.
    """

    if isinstance(value, (int, float)):
        return f"{value:,.2f}"

    return value

def load_worksheet(uploaded_file, sheet_name):
    """
    Load one worksheet from an uploaded Excel workbook.

    Args:
        uploaded_file: Excel file uploaded through Streamlit.
        sheet_name: Name of the worksheet to load.

    Returns:
        A pandas DataFrame containing the worksheet data.
    """

    dataframe = pd.read_excel(
        uploaded_file,
        sheet_name=sheet_name,
    )

    return dataframe

def aggregate_data(
    dataframe,
    group_by_column,
    value_column,
    aggregation,
):
    """
    Group data by one column and calculate an aggregate value.

    Args:
        dataframe: pandas DataFrame containing the data.
        group_by_column: Column used to group the rows.
        value_column: Numeric column to calculate.
        aggregation: Supported operation: sum, mean, min, max, or count.

    Returns:
        A pandas DataFrame with the grouped result.
    """

    allowed_aggregations = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
    }

    if aggregation not in allowed_aggregations:
        raise ValueError(
            f"Unsupported aggregation: {aggregation}"
        )

    if group_by_column not in dataframe.columns:
        raise ValueError(
            f"Column not found: {group_by_column}"
        )

    if value_column not in dataframe.columns:
        raise ValueError(
            f"Column not found: {value_column}"
        )

    result = (
        dataframe
        .groupby(group_by_column, dropna=False)[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return result

def run_aggregation_tool(
    dataframe,
    group_by_column,
    value_column,
    aggregation,
    sort_order="descending",
):
    """
    Execute a validated aggregation and return a serializable result.

    Args:
        dataframe: pandas DataFrame containing the data.
        group_by_column: Column used to group the rows.
        value_column: Numeric column to calculate.
        aggregation: Supported operation.
        sort_order: descending or ascending.

    Returns:
        A dictionary containing tool metadata and result records.
    """

    allowed_sort_orders = {
        "ascending",
        "descending",
    }

    if sort_order not in allowed_sort_orders:
        raise ValueError(
            f"Unsupported sort order: {sort_order}"
        )

    result = aggregate_data(
        dataframe=dataframe,
        group_by_column=group_by_column,
        value_column=value_column,
        aggregation=aggregation,
    )

    result = result.sort_values(
        by=value_column,
        ascending=sort_order == "ascending",
    )

    raw_results = result.to_dict(orient="records")

    display_results = []

    for record in raw_results:
        formatted_record = {}

        for column_name, value in record.items():
            formatted_record[column_name] = format_business_value(value)

        display_results.append(formatted_record)

    return {
        "tool_name": "aggregate_data",
        "group_by_column": group_by_column,
        "value_column": value_column,
        "aggregation": aggregation,
        "sort_order": sort_order,
        "row_count": len(result),
        "results": raw_results,
        "display_results": display_results,
    }
