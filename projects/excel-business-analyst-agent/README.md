# Excel Business Analyst Agent

## Overview

A Streamlit application that answers business questions from multi-sheet
Excel workbooks using two AI-agent architecture patterns.

## Features

- Upload `.xlsx` workbooks
- Discover and preview worksheets
- Inspect columns, data types and missing values
- Ask questions in natural language
- Governed analysis using predefined tools
- Flexible analysis using OpenAI Code Interpreter
- Multi-sheet joins
- Visible execution traces
- Business-friendly answers

## Architecture

### Governed mode

User question → LLM tool selection → validated dispatcher →
trusted pandas function → tool result → LLM explanation

### Flexible mode

User question → workbook upload → OpenAI Code Interpreter →
sandboxed Python analysis → result and execution trace

## Key Concepts Learned

- AI agents
- Tool calling
- Tool schemas
- Agent loops
- Tool-result messages
- Deterministic versus model-generated calculations
- Grounding
- Sandboxed code execution
- Traceability
- Multi-sheet Excel analysis
- Separation of responsibilities

## Architecture Trade-offs

| Governed tools | Flexible analysis |
|---|---|
| Predictable | Highly flexible |
| Strong validation | Minimal custom code |
| More development effort | Model may introduce assumptions |
| Best for official KPIs | Best for exploration |
| Easier to audit | Requires execution-trace review |

## Security

The governed mode allows only explicitly approved Python functions.

The flexible mode runs model-generated Python inside an OpenAI-managed
sandbox and never executes generated code directly on the local computer.

Uploaded business data must still be evaluated against organizational
security, privacy and retention policies.

## Lessons Learned

- The LLM should interpret questions, not be trusted to calculate important metrics mentally.
- Controlled tools provide governance but require development effort.
- Code Interpreter provides much broader analytical capability with less code.
- Flexible analysis can introduce assumptions, such as excluding pending orders.
- Enterprise systems often need a hybrid architecture.
- Execution traces improve transparency but do not replace business-rule governance.

## Future Improvements

- Explicit assumption disclosure
- File deletion and lifecycle management
- Usage and cost tracking
- Authentication and authorization
- Approved business-metric definitions
- Better error handling
- Exportable analysis reports