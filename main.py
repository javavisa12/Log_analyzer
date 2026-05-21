'''Main script for analyzing log files and 
generating email-ready summaries using a local LLM.'''


import sys
import os
import requests
from config import LLM_ENDPOINT
from llm_client import build_system_prompt, send_to_local_llm

def get_output_filenames(log_filepath: str) -> tuple[str, str]:
    """Extracts base filename metrics and sets the destination .md filename."""
    filename = os.path.basename(log_filepath)
    base_name = os.path.splitext(filename)[0]
    md_filename = f"{base_name}_summary.md"
    return filename, md_filename

def analyze_log(log_filepath: str):
    """Orchestrates the retrieval, transformation, and storage of log analytics."""
    if not os.path.exists(log_filepath):
        print(f"Error: Log file '{log_filepath}' not found.")
        sys.exit(1)

    filename, md_filename = get_output_filenames(log_filepath)

    print(f"Reading log: {filename}")
    print(f"Sending to LLM at {LLM_ENDPOINT}...\n")
    
    try:
        with open(log_filepath, 'r') as file:
            log_content = file.read()
            
        # Call the functions imported from llm_client.py
        system_prompt = build_system_prompt(filename)
        extracted_text = send_to_local_llm(system_prompt, log_content)
        
        with open(md_filename, 'w') as md_file:
            md_file.write(extracted_text)
            
        print(f"✅ Success! Email-ready summary saved to: {md_filename}")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the LLM at {LLM_ENDPOINT}. Is the port open and the server running?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_log_file>")
        sys.exit(1)
        
    target_log = sys.argv[1]
    analyze_log(target_log)