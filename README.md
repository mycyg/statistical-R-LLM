# Statistical Analysis Assistant

## Description

This is a desktop application that allows users to perform complex statistical analysis on their data (CSV or Excel files) using natural language. The tool leverages a Large Language Model (LLM) to interpret user requests, generate R code, and execute it to produce insights and visualizations.

## Features

- **Natural Language Interface**: Ask for analysis in plain English.
- **R Integration**: Executes powerful R scripts for statistical analysis.
- **Multi-turn Conversation**: The assistant remembers the context of your analysis.
- **Three-Pane UI**:
    - **Data Preview**: See a preview of your loaded dataset.
    - **Conversation**: Interact with the LLM assistant, see its reasoning and responses.
    - **Outputs**: View generated plots and R script console output in dedicated panes.
- **Secure API Key Handling**: Uses a `.env` file to keep your API credentials secure and out of the source code.
- **Portable R Environment**: Designed to work with a local copy of the R environment placed in the project directory, minimizing system-wide dependencies.

## Requirements

1.  **Python 3.x**
2.  **R Environment**: It is highly recommended to place a portable version of R in the `R` directory at the project root. The application is configured to find it there first. Otherwise, ensure `Rscript` is in your system's PATH.

## Setup & Installation

1.  **Clone/Download the Repository**.

2.  **Configure the LLM API**:
    - Find the `.env.example` file in the project root.
    - Make a copy of it and rename the copy to `.env`.
    - Open the new `.env` file and replace `YOUR_API_KEY_HERE` with your actual LLM API key.

3.  **Install Python Dependencies**:
    Open a terminal in the project root directory and run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the application, execute the following command from the project root directory:

```bash
python src/gui.py
```

- Use the **File > Open CSV/Excel...** menu to load your dataset.
- Use the chat interface to request your analysis.
