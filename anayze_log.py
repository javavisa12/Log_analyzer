import sys
import os
import requests
import json

# ==========================================
# 1. LLM Endpoint Configuration
# ==========================================
LLM_HOST = "http://127.0.0.1"
LLM_PORT = "8000" 
LLM_ENDPOINT = f"{LLM_HOST}:{LLM_PORT}/v1/chat/completions"
MODEL_NAME = "Qwen2.5" 

# ==========================================
# 2. Log Processing & LLM Request
# ==========================================
def analyze_log(log_filepath):
    if not os.path.exists(log_filepath):
        print(f"Error: Log file '{log_filepath}' not found.")
        sys.exit(1)

    # Extract just the filename (e.g., DWH_EBANK_DAY_SYNC_26.05.21_094508.LOG)
    filename = os.path.basename(log_filepath)
    base_name = os.path.splitext(filename)[0]
    md_filename = f"{base_name}_summary.md"

    print(f"Reading log: {filename}")
    print(f"Sending to LLM at {LLM_ENDPOINT}...\n")
    
    try:
        with open(log_filepath, 'r') as file:
            log_content = file.read()
            
        # We give the LLM the filename format and a strict Markdown template
        system_prompt = f"""
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
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the log content:\n\n{log_content}"}
            ],
            "temperature": 0.1 #factual 
        }
        
        headers = {"Content-Type": "application/json"}

        # Send the request
        response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        extracted_text = result['choices'][0]['message']['content']
        
        # Save the structured Markdown to the output file
        with open(md_filename, 'w') as md_file:
            md_file.write(extracted_text)
            
        print(f"✅ Success! Email-ready summary saved to: {md_filename}")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the LLM at {LLM_ENDPOINT}. Is the port open and the server running?")
    except Exception as e:
        print(f"An error occurred: {e}")

# ==========================================
# 3. Command-Line Entry Point
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_log.py <path_to_log_file>")
        sys.exit(1)
        
    target_log = sys.argv[1]
    analyze_log(target_log)
