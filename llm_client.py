# llm_client.py
import requests
import json
from config import LLM_ENDPOINT, MODEL_NAME

def build_system_prompt(filename: str) -> str:
    """Generates a clean string template that won't confuse the JSON parser."""
    return (
        f"You are an expert system administrator analyzing a large batch process log file.\n"
        f"The log file you are analyzing is named: {filename}\n"
        f"The naming convention is: DWH_EBANK_DAY_<JOB_NAME>_YY.MM.DD_TIME.LOG\n\n"
        f"Please parse the filename and the log content to create a professional Markdown email summary matching this template layout:\n\n"
        f"# Batch Summary\n"
        f"**Execution Date:** Extract date from filename\n"
        f"**Execution Time:** Extract time from filename\n\n"
        f"## 1. Summary\n"
        f"Provide a brief, professional summary of the batch process based on the log content.\n\n"
        f"## 2. Warnings & Errors\n"
        f"List any warnings or errors found in the log. If none, explicitly state 'None detected.'\n\n"
        f"## 3. Execution Metrics\n"
        f"* Start Time: Extract from log content\n"
        f"* End Time: Extract from log content\n"
        f"* Total Duration: Extract from log content"
    )

def remove_comments_from_log(log_content: str) -> str:
    """Strips out lines that start with standard comment indicators like # or //."""
    lines = log_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # Skip the line if it is a comment
        if stripped_line.startswith('#') or stripped_line.startswith('//'):
            continue
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def _stream_response(response: requests.Response) -> str:
    """Reads an SSE streaming response and assembles the full text."""
    collected = []
    for raw_line in response.iter_lines():
        # Decode bytes to str if needed
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line or not line.startswith("data: "):
            continue
        data = line[len("data: "):]
        if data.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(data)
            delta = chunk["choices"][0].get("delta", {})
            token = delta.get("content", "")
            if token:
                collected.append(token)
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    return "".join(collected)


def analyze_log_in_chunks(filename: str, log_content: str, chunk_size: int = 8000) -> str:
    """Splits log content into blocks and processes them sequentially with the LLM.
    
    Uses streaming and a strict 'Rolling Draft' history to prevent token limits.
    """
    
    # 1. PURE PYTHON PRE-PROCESSING: Remove comments before chunking
    clean_log_content = remove_comments_from_log(log_content)
    
    # 2. Slicing logic (using the clean text)
    chunks = [clean_log_content[i:i + chunk_size] for i in range(0, len(clean_log_content), chunk_size)]
    total_chunks = len(chunks)
    
    print(f"Original Size: {len(log_content)} chars | Cleaned Size: {len(clean_log_content)} chars")
    print(f"Processing in {total_chunks} chunk(s)...")
    
    # This will hold the text we carry forward
    last_analysis = "No data analyzed yet. This is the first chunk."
    headers = {"Content-Type": "application/json"}

    for index, chunk in enumerate(chunks, start=1):
        print(f" -> Processing chunk {index}/{total_chunks}...")
        
        # FIX: We rebuild the 'messages' list completely from scratch every single loop!
        # It ONLY contains the System Rules, the running Draft, and the New Chunk.
        messages = [
            {"role": "system", "content": build_system_prompt(filename)},
            {"role": "user", "content": (
                f"### CURRENT SUMMARY DRAFT:\n{last_analysis}\n\n"
                f"### NEW LOG PART {index} of {total_chunks}:\n{chunk}\n\n"
                f"Update the Current Summary Draft with any critical info found in this New Log Part."
            )}
        ]
        
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.1,
            "stream": True
        }
        
        response = requests.post(
            LLM_ENDPOINT, 
            headers=headers, 
            data=json.dumps(payload), 
            verify=False,
            timeout=900,
            stream=True
        )
        
        if response.status_code != 200:
            print(f"Server Error Message: {response.text}")
            response.raise_for_status()
        
        # Overwrite the draft with the newly streamed response
        last_analysis = _stream_response(response)
        print(f"    Chunk {index} done ({len(last_analysis)} chars received).\n")
        
    return last_analysis
