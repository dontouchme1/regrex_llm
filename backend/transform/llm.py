import os
import re
import requests
import json
from typing import Optional


def nl_to_regex(instruction: str) -> str:
    """Return a regex pattern string by processing all input through LLM.
    
    All instructions (natural language or direct regex) are sent to Ollama,
    then cleaned with _strip_code_wrappers.
    """
    if not instruction or not isinstance(instruction, str):
        raise ValueError("Instruction must be a non-empty string")

    text = instruction.strip()
    
    # Send everything to LLM, then clean the output
    llm_pat = _ollama_regex(text)
    if llm_pat:
        return llm_pat
    
    raise ValueError("LLM processing failed. Please ensure Ollama is running.")


def _ollama_regex(instruction: str) -> Optional[str]:
    """Call Ollama to convert NL to regex. Return None if not available or failure."""
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            return None
    except requests.exceptions.RequestException:
        return None

    model = os.environ.get("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"
    
    system_msg = (
        "You convert natural-language descriptions into exactly one regex pattern. "
        "Match only the value to be replaced, not any surrounding context. "
        "For numbers, match the exact literal value only with word boundaries (e.g., 1 -> \\b1\\b). "
        "Do NOT infer comparisons or ranges for numbers unless explicitly stated. "
        "Examples: 'change Tom to John' -> match Tom; 'change 1 to 0' -> match \\b1\\b. "
        "Use word boundaries (\\b) when appropriate to avoid partial matches. "
        "Output only the regex pattern (no code, no explanations, no slashes, no flags). "
        "The regex must compile with Python's re module."
    )
    user_msg = f"Instruction: {instruction}\nReturn only the regex pattern."

    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 200
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("message", {}).get("content", "").strip()
            # Clean common wrappers like ```regex ... ``` or /.../
            text = _strip_code_wrappers(text)
            if not text:
                return None
            # Validate compiles
            re.compile(text)
            return text
        return None
    except Exception:
        return None


def _strip_code_wrappers(s: str) -> str:
    s = s.strip()
    
    # Remove fenced code blocks
    if s.startswith("```"):
        s = s.strip("`")
        # After stripping backticks, remove potential leading language tag
        lines = s.split("\n")
        if len(lines) > 1 and lines[0].strip() in ["regex", "python", "text"]:
            s = "\n".join(lines[1:])
        s = s.strip()
    
    # Remove surrounding slashes /.../i
    if len(s) >= 2 and s[0] == "/" and s.rfind("/") > 0:
        last = s.rfind("/")
        s = s[1:last]
    
    # Remove any remaining markdown formatting
    s = s.replace("`", "").strip()
    
    # Extract just the regex pattern from complex responses
    lines = s.split("\n")
    for line in lines:
        line = line.strip()
        # Look for lines that look like regex patterns
        if line and not line.startswith("#") and not line.startswith("//") and not line.startswith("/*"):
            # Check if it's a valid regex pattern
            try:
                re.compile(line)
                return line
            except re.error:
                continue
    
    # If no valid regex found in lines, try the whole string
    try:
        re.compile(s)
        return s
    except re.error:
        return s.strip()

