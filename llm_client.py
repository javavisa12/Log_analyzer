'''system_prompt and send_to_local_llm functions 
for LLM interaction'''


import requests
import json
from config import LLM_ENDPOINT, MODEL_NAME

def build_system_prompt(filename: str) -> str:
    """Generates the prompt configuration detailing strict email guidelines."""
    return f"""
    You are an expert system administrator analyzing batch process logs. 
    The log file you are analyzing is named: {filename}
    The naming convention is: DWH_EBANK_DAY_<JOB_NAME>_YY.MM.DD_TIME.LOG

    Please parse the filename and the log content to create a professional Markdown email summary exactly matching this template:

    # Batch Summary: [Extract <JOB_NAME> from filename]
    **Execution Date:** [Extract YY.MM.DD from filename]
    **Execution Time:** [Extract TIME from filename]

    ## 1. Summary
    [Provide a brief, professional summary of the batch process based on the log content.]

    ## 2. Warnings & Errors
    [List any warnings or errors found in the log. If none, explicitly state "None detected."]

    ## 3. Execution Metrics
    * **Start Time:** [Extract from log content]
    * **End Time:** [Extract from log content]
    * **Total Duration:** [Extract from log content]
    """

def send_to_local_llm(system_prompt: str, log_content: str) -> str:
    """Handles the HTTP network execution out to your local loader port."""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the log content:\n\n{log_content}"}
        ],
        "temperature": 0.1
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']