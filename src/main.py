import pandas as pd
import subprocess
import os
import re
import requests
import json
from dotenv import load_dotenv
from shutil import which

def find_rscript_executable(project_root):
    """
    Find the Rscript executable, prioritizing a local installation.
    """
    local_r_path = os.path.join(project_root, 'R', 'R-4.5.1', 'bin', 'Rscript.exe')
    if os.path.exists(local_r_path):
        return local_r_path
    if which('Rscript'):
        return 'Rscript'
    return None

def _get_llm_response(user_prompt: str, conversation_history: list, data_path: str):
    """
    Calls the LLM API with conversation history and gets a structured JSON response.
    """
    api_key = os.getenv("LLM_API_KEY")
    api_url = os.getenv("LLM_API_URL")
    model_name = os.getenv("LLM_MODEL_NAME")

    if not all([api_key, api_url, model_name]):
        return None, "API configuration is missing in .env file."
    if "YOUR_API_KEY_HERE" in api_key:
        return None, "Please set your API key in the .env file."

    try:
        df_sample = pd.read_csv(data_path, nrows=5)
        sample_data_str = df_sample.to_markdown(index=False)
    except Exception as e:
        return None, f"Failed to read data sample: {e}"

    system_prompt = f"""You are a data analysis assistant. Your primary goal is to help users analyze data by providing R code.

**CRITICAL: Your response MUST be a single, valid JSON object and nothing else.**

The JSON object must have the following exact structure:
{{
  "reasoning_content": "Your detailed thought process on how to handle the user's request.",
  "content": "Your friendly, conversational response to the user.",
  "r_code": "A string containing the complete R code to execute. If no code is needed, this MUST be an empty string."
}}

- The user's data sample is below:\n{sample_data_str}\n
- **R SCRIPT REQUIREMENTS**:
  - Your script will receive TWO command-line arguments: `args[1]` is the input CSV path, and `args[2]` is the **output path for saving a plot**.
  - If you generate a plot, you MUST save it to the path specified in `args[2]`. Example: `png(args[2])`."""

    messages = [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": user_prompt}]
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"model": model_name, "messages": messages}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        try:
            message_obj = response.json()['choices'][0]['message']
            response_content = message_obj.get('content', '')
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return None, f"Failed to parse JSON from API response. Status: {response.status_code}. Error: {e}. Response Body: {response.text}"

        try:
            llm_json_response = json.loads(response_content)
        except json.JSONDecodeError:
            llm_json_response = {
                "reasoning_content": message_obj.get("reasoning_content", "LLM did not provide reasoning."),
                "content": response_content,
                "r_code": ""
            }
            match = re.search(r"```r\n(.*?)\n```", response_content, re.DOTALL)
            if match:
                llm_json_response["r_code"] = match.group(1).strip()
        return llm_json_response, None

    except requests.exceptions.HTTPError as e:
        return None, f"API returned HTTP error: {e}. Response body: {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Network error calling LLM API: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred during API call: {e}"

def process_user_request(user_prompt: str, data_path: str, conversation_history: list):
    """
    Orchestrates the entire process of getting a user request, calling the LLM,
    and executing R code if provided.
    """
    load_dotenv()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)

    llm_response, error = _get_llm_response(user_prompt, conversation_history, data_path)
    if error:
        return {"error": error}

    result = {
        "llm_reasoning": llm_response.get("reasoning_content", ""),
        "llm_response": llm_response.get("content", ""),
        "r_code": llm_response.get("r_code", ""),
        "r_stdout": None,
        "r_stderr": None,
        "artifact_path": None
    }

    if not result["r_code"]:
        return result

    rscript_executable = find_rscript_executable(project_root)
    if not rscript_executable:
        result["error"] = "Rscript executable not found."
        return result

    temp_r_script_path = os.path.join(output_dir, '_temp_generated_script.R')
    temp_data_path = os.path.join(output_dir, '_temp_for_r.csv')

    r_code_template = f"""# --- Auto-generated R script ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {{
  stop("Usage: Rscript <script> <input_csv> [output_plot_path]", call. = FALSE)
}}
input_file <- args[1]
data <- read.csv(input_file)

# --- LLM Generated Analysis ---
{result['r_code']} """

    try:
        with open(temp_r_script_path, 'w', encoding='utf-8') as f:
            f.write(r_code_template)

        df = pd.read_csv(data_path)
        df.to_csv(temp_data_path, index=False)

        plot_output_path = os.path.join(output_dir, 'r_plot.png')
        command = [rscript_executable, temp_r_script_path, temp_data_path, plot_output_path]
        proc = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        
        result["r_stdout"] = proc.stdout
        if os.path.exists(plot_output_path):
            result["artifact_path"] = plot_output_path

    except Exception as e:
        result["r_stderr"] = f"Failed to execute R code: {e}"
    finally:
        if os.path.exists(temp_r_script_path): os.remove(temp_r_script_path)
        if os.path.exists(temp_data_path): os.remove(temp_data_path)
    
    return result

if __name__ == '__main__':
    print("--- Running backend tests ---")
    test_data = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_data.csv')
    history = []
    
    # Turn 1
    print("\n--- Turn 1: summary ---")
    res1 = process_user_request("summarize the data", test_data, history)
    print(res1)
    if not res1.get("error"):
        history.append({"role": "user", "content": "summarize the data"})
        history.append({"role": "assistant", "content": res1['llm_response']})

    # Turn 2
    print("\n--- Turn 2: histogram ---")
    res2 = process_user_request("now make a histogram of age", test_data, history)
    print(res2)