"""LLM-powered tools for code analysis and security scanning."""

import os
import sys
import json
import re
import time
from typing import Dict, List, Optional
from langchain.tools import tool
from openai import OpenAI

# Rate limiting: track last call time
_last_llm_call_time = 0
_min_delay_between_calls = 2  # 2 seconds between calls (NVIDIA API is more lenient)


def find_json_object(text):
    """Find the first complete JSON object in text by matching balanced braces.
    
    Args:
        text: String that may contain JSON mixed with other text
        
    Returns:
        String containing the first complete JSON object, or None if not found
    """
    # Find the first opening brace
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    # Count braces to find the matching closing brace
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_idx, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found complete JSON object
                    return text[start_idx:i+1]
    
    return None


@tool
def read_file_content(filepath: str) -> str:
    """
    Read the full content of a file from the repository.
    
    Args:
        filepath: Path to the file (can be relative to repo root or absolute)
        
    Returns:
        File content as string
    """
    try:
        repo_path = os.environ.get('DEVGUARD_REPO_PATH', '')
        
        # Handle relative paths
        if not os.path.isabs(filepath) and repo_path:
            filepath = os.path.join(repo_path, filepath)
        
        if not os.path.exists(filepath):
            error_msg = f"Error: File not found: {filepath}"
            if 'st' in globals() or 'streamlit' in sys.modules:
                try:
                    import streamlit as st
                    st.warning(f"⚠️ {error_msg}")
                except:
                    pass
            return error_msg
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except Exception as e:
        import sys
        error_msg = f"Error reading file {filepath}: {str(e)}"
        if 'st' in globals() or 'streamlit' in sys.modules:
            try:
                import streamlit as st
                st.error(f"❌ {error_msg}")
                with st.expander("File Read Error Details"):
                    import traceback
                    st.code(traceback.format_exc(), language="python")
            except:
                pass
        return error_msg


@tool
def analyze_code_with_llm(input_data: str) -> str:
    """
    Analyze code content using LLM to detect security risks and provide advice.
    Input can be:
    - File path (string) - will read file
    - Code content directly (string) - will analyze directly
    - JSON string with "filepath" and "file_content" keys
    
    Args:
        input_data: File path, code content, or JSON string
        
    Returns:
        JSON string with structured findings
    """
    import json
    
    # Parse input - check if it's a file path or direct code content
    filepath = "code_chunks"
    file_content = ""
    
    # Ensure input_data is a string, not a list
    if isinstance(input_data, list):
        # If it's a list, join it into a string
        file_content = "\n\n".join(str(item) for item in input_data)
        filepath = "filtered_code_chunks"
    elif isinstance(input_data, dict):
        # If it's a dict, convert to JSON string
        file_content = json.dumps(input_data)
        filepath = "code_chunks"
    else:
        # It should be a string
        input_str = str(input_data) if not isinstance(input_data, str) else input_data
        
        try:
            if input_str.startswith('{'):
                # JSON format
                data = json.loads(input_str)
                filepath = data.get("filepath", "code_chunks")
                file_content = data.get("file_content", "")
            elif os.path.exists(input_str):
                # File path - read the content
                filepath = input_str
                file_content = read_file_content.invoke({"filepath": filepath})
            else:
                # Direct code content (from filtered chunks)
                file_content = input_str
                filepath = "filtered_code_chunks"
        except Exception:
            # Fallback: treat as direct code content
            file_content = input_str
            filepath = "code_chunks"
    
    # Get NVIDIA API key and configuration
    api_key = os.environ.get("NVIDIA_API_KEY")
    base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model_name = os.environ.get("NVIDIA_MODEL", "meta/llama-3.2-3b-instruct")
    
    if not api_key:
        return json.dumps({"error": "NVIDIA_API_KEY not set. Please set NVIDIA_API_KEY environment variable."})
    
    # Initialize OpenAI client for NVIDIA API
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
    except Exception as init_error:
        return json.dumps({
            "error": f"Failed to initialize NVIDIA API client: {str(init_error)}",
            "filepath": filepath,
            "findings": []
        })
    
    # Create analysis prompt - ALL reasoning generated by LLM, no hardcoded rules
    # Check if this is filtered chunks or full file
    is_chunks = "chunk" in filepath.lower() or "--- CHUNK ---" in file_content
    
    if is_chunks:
        prompt_intro = f"""You are analyzing FILTERED RISKY CODE SECTIONS that were pre-identified as potentially containing security issues.

These code chunks have been filtered using pattern matching for security risks. Each chunk is from a different file, indicated by "File: <filename>" at the start of each chunk.

CRITICAL: Use the exact file name from the chunk header (e.g., "File: app.py" → use "app.py" as file_name).

Code Chunks:
```
{file_content[:8000]}
```
"""
    else:
        prompt_intro = f"""You are an expert security analyst with deep knowledge of code security, vulnerabilities, and best practices.

Analyze this file for security risks, vulnerabilities, and compliance issues:

File: {filepath}

Code Content:
```
{file_content[:8000]}
```
"""
    
    analysis_prompt = prompt_intro + """

You are an expert security analyst and AI agent with deep knowledge of code security, vulnerabilities, attack vectors, and remediation strategies.

YOUR AGENTIC MISSION - Act as an autonomous security expert:

1. **AUTONOMOUS ANALYSIS**: Examine the code chunks systematically, reasoning about each potential risk
2. **CONTEXT-AWARE DETECTION**: Consider the broader security implications, not just surface-level issues
3. **ATTACK VECTOR ANALYSIS**: Think like an attacker - how could this vulnerability be exploited?
4. **COMPREHENSIVE EXPLANATION**: Provide detailed, agent-like reasoning for each finding

FOR EACH SECURITY ISSUE YOU FIND, PROVIDE:

**1. DETAILED EXPLANATION** (`why_problem`):
   - Explain what the vulnerability is in detail
   - Describe the attack scenarios (step-by-step: how an attacker would exploit this)
   - Analyze the potential impact (what data/systems could be compromised)
   - Explain why this is a security risk (what makes it dangerous)
   - Discuss compliance implications (GDPR, PCI-DSS, HIPAA, OWASP Top 10)
   - Provide real-world examples of similar vulnerabilities that caused breaches

**2. SPECIFIC REMEDIATION STRATEGY** (`fix_suggestion`):
   - Provide step-by-step instructions on how to fix the issue
   - Include best practices and security standards to follow
   - Explain the correct secure implementation approach
   - Mention relevant security frameworks/guidelines (OWASP, CWE, NIST)

**3. DETAILED CODE CHANGES** (`what_to_change`):
   - Show the exact problematic code/configuration (copy it)
   - Provide the secure replacement code/configuration (with full context)
   - Explain why the new approach is secure
   - Include additional security measures to implement

**4. PRIORITY & SEVERITY ASSESSMENT**:
   - Assess severity (High/Medium/Low) based on:
     * Exploitability (how easy is it to exploit?)
     * Impact (what's at stake if exploited?)
     * Prevalence (how common is this vulnerability?)
   - Explain your severity reasoning

THINK DEEPLY ABOUT:
- Secrets and credentials (API keys, passwords, tokens) - where they're stored, how they're exposed, attack vectors
- Authentication and authorization vulnerabilities - broken access controls, privilege escalation
- Injection vulnerabilities (SQL, XSS, command injection, LDAP, NoSQL) - how they work, how to prevent them
- Insecure configurations - misconfigurations, default passwords, exposed services
- Data exposure risks - sensitive data in code, logs, responses, error messages
- Cryptographic weaknesses - weak encryption, improper key management, deprecated algorithms
- Code execution vulnerabilities - RCE, deserialization attacks, unsafe eval/exec
- Compliance violations - GDPR (data protection), PCI-DSS (payment data), HIPAA (health data)
- Supply chain risks - vulnerable dependencies, typosquatting
- API security - insecure endpoints, missing rate limiting, broken authentication

CRITICAL AGENT REQUIREMENTS:
- You MUST identify ALL security issues - be thorough and systematic
- Use your security expertise to reason deeply about WHY each issue matters
- Provide actionable, specific guidance - developers should know exactly what to do
- Think like both a defender (how to protect) and an attacker (how this could be exploited)
- Return ONLY valid JSON with findings array (even if empty, but analyze thoroughly)

EXAMINE THOROUGHLY FOR:
- Hardcoded secrets (API keys, passwords, tokens, certificates)
- SQL injection (unsafe string concatenation, missing parameterization)
- XSS vulnerabilities (unvalidated user input, unsafe DOM manipulation)
- Insecure configurations (open permissions, 0.0.0.0/0 in security groups, debug mode in production)
- Code execution vulnerabilities (eval with user input, unsafe deserialization)
- Authentication/authorization flaws (missing authentication, broken access controls)
- Sensitive data exposure (secrets in logs, error messages, API responses)
- Cryptographic weaknesses (weak keys, deprecated algorithms, improper usage)

**CRITICAL: You MUST return ONLY valid JSON. Do NOT include any explanatory text, markdown formatting, or comments before or after the JSON.**

OUTPUT FORMAT (Return ONLY this JSON structure, nothing else):
{{
  "findings": [
    {{
      "file_name": "<EXACT file name from the chunk header>",
      "line_number": <line number where issue appears>,
      "risk_type": "<risk classification>",
      "severity": "<High|Medium|Low>",
      "description": "<brief 1-2 sentence summary>",
      "fix_suggestion": "<COMPREHENSIVE remediation strategy with OWASP/CWE/NIST references, best practices, and implementation guidance (200-400 words)>",
      "what_to_change": "<DETAILED code/configuration changes with before/after examples and security explanations (150-300 words)>",
      "why_problem": "<COMPREHENSIVE explanation: vulnerability details, attack scenarios, impact analysis, compliance implications, real-world examples (300-500 words)>"
    }}
  ]
}}

IMPORTANT FILE NAMING:
- Each chunk starts with "File: <filename>"
- Use that EXACT filename in "file_name" field
- Examples: "app.py", "config.py", "aws_config.yml"
- DO NOT use generic names like "filtered_code_chunks" or "code_chunks"

**REMEMBER: Return ONLY the JSON object. No text before or after. Start your response with { and end with }**"""
    
    try:
        # Rate limiting: wait if needed to avoid quota errors
        global _last_llm_call_time
        current_time = time.time()
        time_since_last_call = current_time - _last_llm_call_time
        if time_since_last_call < _min_delay_between_calls:
            wait_time = _min_delay_between_calls - time_since_last_call
            time.sleep(wait_time)
        _last_llm_call_time = time.time()
        
        # Get LLM analysis using NVIDIA API
        try:
            # Call NVIDIA API using OpenAI-compatible interface
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=4096,  # Increased for comprehensive analysis
                stream=False  # Get complete response at once
            )
            
            # Extract content from OpenAI response format
            if completion and completion.choices:
                response_content = completion.choices[0].message.content
                if response_content:
                    response = response_content
                else:
                    raise ValueError("LLM returned empty content in response")
            else:
                raise ValueError("LLM returned invalid response structure")
            
        except Exception as api_error:
            error_str = str(api_error)
            # Check for rate limit errors
            if "429" in error_str or "rate limit" in error_str.lower() or "quota" in error_str.lower():
                raise  # Re-raise to be handled below
            else:
                raise api_error
        
        # Extract content from response - OpenAI returns string directly
        output_text = None
        
        # Debug: Log response type and structure
        response_type = type(response).__name__
        response_repr = repr(response)[:500] if response else "None"
        
        # OpenAI/NVIDIA API returns string content directly
        if response is not None:
            if isinstance(response, str):
                output_text = response
            else:
                # Fallback: convert to string
                output_text = str(response) if response else None
        
        # Handle LangChain message objects - extract content from message parts
        # First, try the most common LangChain pattern: AIMessage with content attribute
        # OpenAI/NVIDIA API returns string directly, so output_text should already be set
        # If not, ensure we have a string
        if output_text is None:
            output_text = str(response) if response else None
        
        # Ensure output_text is a string
        if output_text is None:
            output_text = ""
        elif not isinstance(output_text, str):
            output_text = str(output_text)
        
        # Handle None or empty response with better debugging
        if not output_text or output_text.strip() == "" or output_text == "None":
            # Try one more time with direct string conversion
            if response is not None:
                try:
                    # Try to get string representation and extract any text
                    response_str = str(response)
                    # Look for JSON-like content in the string representation
                    if "{" in response_str and "findings" in response_str:
                        # Try to extract JSON from string representation
                        json_match = re.search(r'\{.*"findings".*\}', response_str, re.DOTALL)
                        if json_match:
                            output_text = json_match.group(0)
                    elif len(response_str) > 50:  # If it's a substantial string, use it
                        output_text = response_str
                except:
                    pass
            
            # If still empty, return error with debug info
            if not output_text or output_text.strip() == "":
                debug_info = {
                    "error": "LLM returned empty response",
                    "filepath": filepath,
                    "response_type": response_type,
                    "response_preview": response_repr,
                    "findings": []
                }
                # Log debug info if possible
                if 'st' in globals() or 'streamlit' in sys.modules:
                    try:
                        import streamlit as st
                        with st.expander("🔍 Debug: LLM Response Structure"):
                            st.write(f"**Response Type:** `{response_type}`")
                            st.write(f"**Response Preview:**")
                            st.code(response_repr, language="text")
                            st.write(f"**Full Response:**")
                            st.code(str(response), language="text")
                    except:
                        pass
                return json.dumps(debug_info)
        
        # Extract JSON from response (LLM might add markdown formatting or extra text)
        # The LLM often adds explanatory text before/after the JSON, so we need robust extraction
        
        # Pattern 1: Look for JSON in markdown code blocks (```json ... ``` or ``` ... ```)
        markdown_json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output_text, re.DOTALL)
        if markdown_json_match:
            json_str = markdown_json_match.group(1)
            try:
                findings_data = json.loads(json_str)
                return json.dumps(findings_data, indent=2)
            except json.JSONDecodeError:
                pass
        
        # Pattern 2: Use balanced brace matching to find complete JSON object (most robust)
        json_str = find_json_object(output_text)
        if json_str:
            try:
                findings_data = json.loads(json_str)
                return json.dumps(findings_data, indent=2)
            except json.JSONDecodeError:
                # Try to find JSON starting with "findings" key
                findings_start = output_text.find('"findings"')
                if findings_start != -1:
                    # Find the opening brace before "findings"
                    brace_before = output_text.rfind('{', 0, findings_start)
                    if brace_before != -1:
                        json_str = find_json_object(output_text[brace_before:])
                        if json_str:
                            try:
                                findings_data = json.loads(json_str)
                                return json.dumps(findings_data, indent=2)
                            except json.JSONDecodeError:
                                pass
        
        # Pattern 3: Try parsing entire output as JSON (might work if LLM returned pure JSON)
        try:
            findings_data = json.loads(output_text.strip())
            return json.dumps(findings_data, indent=2)
        except json.JSONDecodeError:
            pass
        
        # Pattern 4: Look for JSON with "findings" key using regex (fallback)
        findings_match = re.search(r'(\{\s*"findings"\s*:\s*\[.*?\]\s*\})', output_text, re.DOTALL)
        if findings_match:
            try:
                findings_data = json.loads(findings_match.group(1))
                return json.dumps(findings_data, indent=2)
            except json.JSONDecodeError:
                pass
        
        # If all parsing fails, return error with debug info
        # Debug: Log what we received (show more for debugging)
        debug_info = output_text[:2000] if len(output_text) > 2000 else output_text
        
        # Log to console for debugging
        print(f"\n{'='*80}")
        print(f"FAILED TO PARSE LLM RESPONSE")
        print(f"{'='*80}")
        print(f"Response length: {len(output_text)} chars")
        print(f"First 500 chars: {output_text[:500]}")
        print(f"{'='*80}\n")
        
        return json.dumps({
            "error": "Could not parse LLM response as JSON",
            "raw_output_preview": debug_info,
            "filepath": filepath,
            "findings": []
        })
    
    except Exception as llm_error:
        import sys
        error_str = str(llm_error)
        
        # Check if it's a quota/rate limit error
        if "429" in error_str or "rate limit" in error_str.lower() or "quota" in error_str.lower():
            error_msg = (
                "⚠️ **NVIDIA API rate limit exceeded.** "
                "Please wait a moment and try again, or check your API quota."
            )
            
            # Extract retry delay if available
            if "retry in" in error_str.lower():
                # re is already imported at top of file
                retry_match = re.search(r'retry in ([\d.]+)s', error_str.lower())
                if retry_match:
                    wait_seconds = float(retry_match.group(1))
                    error_msg += f"\n\nSuggested wait time: {wait_seconds:.0f} seconds."
        else:
            error_msg = f"LLM API call failed: {error_str}"
        
        if 'st' in globals() or 'streamlit' in sys.modules:
            try:
                import streamlit as st
                st.warning(f"⚠️ {error_msg}")
                with st.expander("LLM API Error Details"):
                    import traceback
                    st.code(traceback.format_exc(), language="python")
            except:
                pass
        return json.dumps({
            "error": error_msg,
            "filepath": filepath,
            "findings": []
        })


def parse_llm_findings(llm_output: str) -> List[Dict]:
    """
    Parse LLM output into structured findings list.
    
    Args:
        llm_output: JSON string from analyze_code_with_llm (can be None)
        
    Returns:
        List of finding dictionaries
    """
    # Handle None or empty input
    if not llm_output or llm_output is None:
        return []
    
    try:
        data = json.loads(llm_output)
        if "findings" in data:
            return data["findings"]
        elif isinstance(data, list):
            return data
        else:
            return []
    except (json.JSONDecodeError, TypeError) as e:
        # Return empty list if parsing fails
        return []

