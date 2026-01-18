"""LLM-powered agentic orchestrator for autonomous repository scanning."""

from typing import List, Dict, Optional, Callable
import os
import json
import re
import tempfile
import shutil

# No longer need create_agent - using direct sequential processing instead

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Fallback if langchain_google_genai not available
    try:
        from langchain_community.chat_models import ChatGoogleGenerativeAI
    except ImportError:
        ChatGoogleGenerativeAI = None
        raise ImportError(
            "Could not import ChatGoogleGenerativeAI. Install with: "
            "pip install langchain-google-genai"
        )

try:
    import streamlit as st
except ImportError:
    st = None

from scanner.tools.llm_scan_tool import analyze_code_with_llm, parse_llm_findings
from scanner.filter import CodeChunkFilter


class ScanningAgent:
    """LLM-powered agent that autonomously scans files using AI reasoning."""
    
    def __init__(self, llm_api_key: Optional[str] = None):
        """
        Initialize the LLM-powered scanning agent.
        
        Args:
            llm_api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = llm_api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("LLM API key is required. Set GEMINI_API_KEY environment variable or pass llm_api_key.")
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",  # Google Gemini model
            google_api_key=self.api_key,
            temperature=0.2,  # Lower temperature for more focused analysis
        )
        
        self.collected_findings = []  # Store findings collected from sequential processing
        self.chunk_filter = CodeChunkFilter()  # Initialize code chunk filter
    
    def scan_uploaded_files(self, uploaded_files: List, log_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Scan uploaded files for security risks using LLM-powered analysis.
        Processes files sequentially, storing findings after each file.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            log_callback: Optional function to call with log messages
            
        Returns:
            List of findings with comprehensive LLM-generated advice
        """
        findings = []
        temp_dir = None
        
        try:
            if st:
                st.info(f"📁 Processing {len(uploaded_files)} uploaded file(s)...")
            
            # Create temporary directory to store uploaded files
            temp_dir = tempfile.mkdtemp(prefix='devguard_uploads_')
            
            if log_callback:
                log_callback(f"Created temporary directory for file analysis")
            
            # Prioritize files - only scan most critical ones to avoid rate limits
            # Gemini free tier: 5 requests/minute = max 4-5 files with 15-20 sec delays
            critical_patterns = ['.env', 'config', 'firebase', 'aws', 'app.py', 'main.py', 'main.js', 'settings']
            
            # Separate critical and other files
            critical_files = []
            other_files = []
            for file in uploaded_files:
                filename = file.name.lower()
                if any(pattern in filename for pattern in critical_patterns):
                    critical_files.append(file)
                else:
                    other_files.append(file)
            
            # Process ALL files - batches handle rate limiting efficiently
            # With batch processing, we can analyze all files since chunks are batched (10 chunks per batch)
            # This means: 30 chunks = 3 batches = 3 API calls, regardless of number of files
            files_to_scan = critical_files + other_files  # Process all files
            
            if st:
                st.info(f"📊 **Batch Processing:** All {len(files_to_scan)} files will be analyzed. "
                       f"Risky chunks will be batched (10 chunks per batch) to optimize API usage.")
                st.write(f"   • Files to analyze: {len(files_to_scan)}")
                st.write(f"   • Critical files: {len(critical_files)}")
                st.write(f"   • Other files: {len(other_files)}")
            
            if log_callback:
                log_callback(f"Processing all {len(files_to_scan)} files (all files will be analyzed with batch processing)")
            
            # STEP 1: Extract and filter risky chunks from ALL files first
            import time
            
            if st:
                st.write("🔍 Step 1: Extracting and filtering risky code chunks from all files...")
            if log_callback:
                log_callback(f"Extracting risky chunks from all files...")
            
            all_risky_chunks = []  # Store all risky chunks from all files
            processed_files = []  # Track which files were processed
            
            if st:
                st.write(f"📋 Processing {len(files_to_scan)} file(s) to extract risky chunks...")
            
            for file_idx, uploaded_file in enumerate(files_to_scan, 1):
                try:
                    if st:
                        st.write(f"📄 Processing file {file_idx}/{len(files_to_scan)}: {uploaded_file.name}")
                    if log_callback:
                        log_callback(f"Processing file {file_idx}/{len(files_to_scan)}: {uploaded_file.name}")
                    
                    # Save uploaded file to temp directory
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else temp_dir, exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Read file content
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_content = f.read()
                    except Exception as read_err:
                        if log_callback:
                            log_callback(f"⚠️ Could not read {uploaded_file.name} as text: {str(read_err)[:100]}")
                        continue
                    
                    if not file_content.strip():
                        if log_callback:
                            log_callback(f"ℹ️ File {uploaded_file.name} is empty, skipping")
                        continue
                    
                    if log_callback:
                        log_callback(f"Filtering risky chunks in {uploaded_file.name}...")
                    
                    # Filter risky chunks from this file
                    risky_chunks = self.chunk_filter.get_risky_code_sections(file_content, uploaded_file.name)
                    
                    # Add file reference to each chunk
                    for chunk in risky_chunks:
                        chunk['source_file'] = uploaded_file.name
                    
                    all_risky_chunks.extend(risky_chunks)
                    processed_files.append(uploaded_file.name)
                    
                    if log_callback:
                        log_callback(f"✅ Found {len(risky_chunks)} risky chunk(s) in {uploaded_file.name} (total chunks so far: {len(all_risky_chunks)})")
                        # Debug: Show chunk details
                        if risky_chunks:
                            for idx, chunk in enumerate(risky_chunks[:3], 1):
                                log_callback(f"      Chunk {idx}: Lines {chunk.get('start_line', '?')}-{chunk.get('end_line', '?')} ({len(chunk.get('text', ''))} chars)")
                    
                    if st:
                        st.write(f"   ✅ {uploaded_file.name}: {len(risky_chunks)} risky chunk(s) found")
                        # Show chunk preview
                        if risky_chunks:
                            preview_text = risky_chunks[0].get('text', '')[:100].replace('\n', ' ')
                            st.write(f"      Preview: {preview_text}...")
                    
                except Exception as e:
                    error_msg = str(e)
                    if log_callback:
                        log_callback(f"❌ Error processing {uploaded_file.name}: {error_msg[:200]}")
                    if st:
                        st.warning(f"⚠️ Error processing {uploaded_file.name}: {error_msg[:200]}")
                    continue
            
            if st:
                st.write(f"✅ Processed {len(processed_files)} file(s): {', '.join(processed_files)}")
            
            if log_callback:
                log_callback(f"Completed chunk extraction: {len(processed_files)} files processed, {len(all_risky_chunks)} total risky chunks found")
            
            if not all_risky_chunks:
                if st:
                    st.info("ℹ️ No risky code chunks found in any files. Scan complete.")
                if log_callback:
                    log_callback(f"✅ No risky chunks found - scan complete")
                return []
            
            if st:
                st.success(f"✅ Found {len(all_risky_chunks)} risky chunks across all files")
            if log_callback:
                log_callback(f"Total risky chunks found: {len(all_risky_chunks)}")
            
            # STEP 2: Batch chunks into groups of 10
            batch_size = 10
            batches = []
            for i in range(0, len(all_risky_chunks), batch_size):
                batches.append(all_risky_chunks[i:i + batch_size])
            
            if st:
                st.write(f"📦 Created {len(batches)} batch(es) of chunks (max {batch_size} chunks per batch)")
                # Show batch composition
                for batch_idx, batch in enumerate(batches[:5], 1):  # Show first 5 batches
                    files_in_batch = set(chunk.get('source_file', 'unknown') for chunk in batch)
                    st.write(f"   Batch {batch_idx}: {len(batch)} chunks from {len(files_in_batch)} file(s): {', '.join(files_in_batch)}")
                if len(batches) > 5:
                    st.write(f"   ... and {len(batches) - 5} more batch(es)")
                st.info(f"💡 **Optimization:** Sending {len(batches)} LLM request(s) instead of {len(files_to_scan)} (one per file). "
                       f"This reduces API calls by {(len(files_to_scan) - len(batches)) / max(len(files_to_scan), 1) * 100:.0f}%")
            
            if log_callback:
                log_callback(f"Created {len(batches)} batch(es) for LLM analysis")
                # Debug: Log batch composition
                for batch_idx, batch in enumerate(batches, 1):
                    files_in_batch = set(chunk.get('source_file', 'unknown') for chunk in batch)
                    log_callback(f"   Batch {batch_idx}: {len(batch)} chunks from files: {', '.join(files_in_batch)}")
            
            # Add initial wait for rate limiting
            if st:
                st.write("⏳ Waiting 15 seconds before starting LLM analysis (rate limit protection)...")
            if log_callback:
                log_callback(f"⏳ Initial wait: 15 seconds")
            time.sleep(15)
            
            # STEP 3: Process batches sequentially - each batch = one LLM request
            for batch_idx, batch in enumerate(batches, 1):
                try:
                    if st:
                        with st.status(f"🤖 Analyzing batch {batch_idx}/{len(batches)} ({len(batch)} chunks)", expanded=True) as status:
                            st.write(f"📦 **Batch {batch_idx}:** {len(batch)} code chunk(s)")
                            
                            # Show which files are in this batch
                            files_in_batch = set(chunk.get('source_file', 'unknown') for chunk in batch)
                            st.write(f"📄 **Files:** {', '.join(files_in_batch)}")
                            
                            for i, chunk in enumerate(batch[:3], 1):
                                st.write(f"   {i}. {chunk.get('source_file', 'unknown')} - Lines {chunk['start_line']}-{chunk['end_line']}")
                            
                            if log_callback:
                                log_callback(f"Analyzing batch {batch_idx}/{len(batches)}: {len(batch)} chunks from {len(files_in_batch)} file(s)")
                            
                            # Rate limiting: wait 15 seconds between batches (except first batch after initial wait)
                            if batch_idx > 1:
                                wait_time = 15
                                if st:
                                    st.write(f"⏳ Waiting {wait_time} seconds (rate limit: 5 req/min)...")
                                if log_callback:
                                    log_callback(f"⏳ Rate limit wait: {wait_time} seconds")
                                time.sleep(wait_time)
                            
                            # Combine chunks in this batch into one analysis
                            combined_chunks_text = "\n\n--- CHUNK ---\n\n".join([
                                f"File: {chunk.get('source_file', chunk.get('file_name', 'unknown'))}\n"
                                f"Lines {chunk['start_line']}-{chunk['end_line']}:\n"
                                f"{chunk['text']}"
                                for chunk in batch
                            ])
                            
                            # Analyze with LLM (with retry on rate limit)
                            max_retries = 2
                            result = None
                            
                            for retry in range(max_retries):
                                try:
                                    # Analyze combined chunks instead of full file
                                    result = analyze_code_with_llm.invoke(combined_chunks_text)
                                    
                                    # Check for errors in response
                                    try:
                                        result_data = json.loads(result) if isinstance(result, str) else result
                                        if isinstance(result_data, dict):
                                            # Check for errors in response
                                            if "error" in result_data:
                                                error_msg = result_data.get("error", "Unknown error")
                                                # If it's a JSON parsing error, show debug info
                                                if "Could not parse LLM response" in error_msg:
                                                    raw_output = result_data.get("raw_output_preview", "")
                                                    if st:
                                                        st.error(f"❌ JSON parsing failed. LLM response preview:")
                                                        st.code(raw_output[:500] if raw_output else "No preview available", language="text")
                                                    if log_callback:
                                                        log_callback(f"❌ JSON parsing failed. Response preview: {raw_output[:200] if raw_output else 'No preview'}...")
                                                    result = None
                                                    break  # Don't retry JSON parsing errors
                                                
                                                # Handle other errors
                                                if log_callback:
                                                    log_callback(f"❌ Error in response: {error_msg[:200]}")
                                                if st:
                                                    st.warning(f"⚠️ Analysis error: {error_msg[:200]}")
                                                result = None
                                                break
                                            
                                            # If no error, continue to parse findings
                                            # Success case - no error field, break to proceed
                                            break
                                    except:
                                        pass  # Continue with normal parsing if not error JSON
                                    
                                    # Success - break retry loop
                                    break
                                    
                                except Exception as llm_err:
                                    error_str = str(llm_err)
                                    if ("quota" in error_str.lower() or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and retry < max_retries - 1:
                                        wait_seconds = 60
                                        if st:
                                            st.warning(f"⏳ Rate limit exception. Waiting {wait_seconds} seconds...")
                                        if log_callback:
                                            log_callback(f"⏳ Rate limit exception. Waiting {wait_seconds} seconds...")
                                        time.sleep(wait_seconds)
                                        continue
                                    else:
                                        if log_callback:
                                            log_callback(f"❌ Exception analyzing batch {batch_idx}: {error_str[:200]}")
                                        if st:
                                            st.error(f"❌ Exception: {error_str[:200]}")
                                        result = None
                                        break
                            
                            if result is None:
                                if log_callback:
                                    log_callback(f"⚠️ Skipping batch {batch_idx} - analysis failed")
                                continue  # Skip to next batch if analysis failed
                            
                            st.write(f"📥 LLM returned response ({len(str(result))} chars)")
                            
                            # Parse findings
                            file_findings = parse_llm_findings(result)
                            
                            # Debug: Show parsed findings count
                            if st and file_findings:
                                st.write(f"🔍 Parsed {len(file_findings)} finding(s) from JSON response")
                            
                            if log_callback:
                                log_callback(f"Parsed {len(file_findings)} finding(s) from batch {batch_idx}")
                            
                            # STORE FINDINGS IMMEDIATELY after each batch
                            if file_findings:
                                # Map findings back to source files using batch chunks
                                # IMPROVED: Multi-strategy matching to ensure correct file attribution
                                
                                # Get list of valid file names in this batch
                                valid_files_in_batch = set()
                                for chunk in batch:
                                    source_file = chunk.get('source_file') or chunk.get('file_name')
                                    if source_file:
                                        valid_files_in_batch.add(source_file)
                                
                                for finding in file_findings:
                                    finding_line = finding.get('line_number', 0)
                                    llm_reported_file = finding.get('file_name', '').strip()
                                    source_file = None
                                    
                                    # Strategy 1: Check if LLM reported file name matches a file in this batch
                                    if llm_reported_file and llm_reported_file in valid_files_in_batch:
                                        source_file = llm_reported_file
                                        if log_callback:
                                            log_callback(f"   ✓ File attribution: LLM reported '{llm_reported_file}' (matches batch)")
                                    
                                    # Strategy 2: Try to find matching chunk based on line number
                                    if not source_file and finding_line > 0:
                                        for chunk in batch:
                                            chunk_start = chunk.get('start_line', 0)
                                            chunk_end = chunk.get('end_line', 0)
                                            if chunk_start <= finding_line <= chunk_end:
                                                source_file = chunk.get('source_file') or chunk.get('file_name', 'unknown')
                                                if log_callback:
                                                    log_callback(f"   ✓ File attribution: Line {finding_line} matches {source_file} (lines {chunk_start}-{chunk_end})")
                                                break
                                    
                                    # Strategy 3: If LLM reported a file but it's not in batch, check if it's a close match
                                    if not source_file and llm_reported_file:
                                        # Try fuzzy matching (e.g., "filtered_code_chunks" → first file in batch)
                                        if any(keyword in llm_reported_file.lower() for keyword in ['chunk', 'code', 'filtered']):
                                            source_file = list(valid_files_in_batch)[0] if valid_files_in_batch else None
                                            if log_callback:
                                                log_callback(f"   ⚠ File attribution: LLM reported '{llm_reported_file}' (generic) → using first file in batch: {source_file}")
                                    
                                    # Strategy 4: Fallback to first chunk's file
                                    if not source_file:
                                        source_file = batch[0].get('source_file') or batch[0].get('file_name', 'unknown')
                                        if log_callback:
                                            log_callback(f"   ⚠ File attribution: Fallback to first file in batch: {source_file}")
                                    
                                    finding['file_name'] = source_file
                                    
                                    # Debug: Log file attribution
                                    if log_callback and finding_line:
                                        log_callback(f"   → Finding '{finding.get('risk_type', 'Unknown')}' at line {finding_line} → {source_file}")
                                
                                findings.extend(file_findings)
                                
                                # Update session state immediately (incremental storage)
                                if 'scan_results' in st.session_state:
                                    st.session_state.scan_results = findings.copy()
                                
                                if log_callback:
                                    for finding in file_findings:
                                        log_callback(f"🔴 SECURITY ISSUE: {finding.get('risk_type', 'Unknown')} in {finding.get('file_name', 'unknown')} (Line {finding.get('line_number', '?')}) - {finding.get('severity', 'Unknown')} severity")
                                
                                if st:
                                    st.success(f"✅ **Found {len(file_findings)} security issue(s)** in this batch")
                                    for finding in file_findings[:3]:
                                        st.write(f"   • **{finding.get('risk_type', 'Unknown')}** ({finding.get('severity', '?')}) in {finding.get('file_name', 'unknown')} - Line {finding.get('line_number', '?')}")
                            else:
                                if log_callback:
                                    log_callback(f"ℹ️ No security issues found in batch {batch_idx}")
                                if st:
                                    st.info(f"ℹ️ No security issues detected in batch {batch_idx}")
                            
                            # Store findings in instance variable too
                            self.collected_findings = findings
                            
                except Exception as batch_error:
                    error_str = str(batch_error)
                    if log_callback:
                        log_callback(f"❌ Error processing batch {batch_idx}: {error_str[:200]}")
                    if st:
                        st.error(f"❌ Error processing batch: {error_str[:200]}")
                        import traceback
                        with st.expander("Batch Error Details"):
                            st.code(traceback.format_exc(), language="python")
                    continue
            
            # Final summary
            if st:
                st.markdown("---")
                st.success(f"✅ **Scan Complete!**")
                st.write(f"📊 **Results:**")
                st.write(f"   • Files processed: {len(files_to_scan)}")
                st.write(f"   • Risky chunks found: {len(all_risky_chunks)}")
                st.write(f"   • Batches analyzed: {len(batches)}")
                st.write(f"   • Security issues found: {len(findings)}")
                st.write(f"   • **API calls saved:** {len(files_to_scan)} files → {len(batches)} batches (reduced by {(1 - len(batches)/max(len(files_to_scan), 1)) * 100:.0f}%)")
            
            if log_callback:
                log_callback(f"Scan complete. Processed {len(batches)} batch(es), found {len(findings)} total finding(s)")
            
            return findings
            
        except Exception as e:
            error_msg = f"LLM Agent error: {str(e)}"
            if log_callback:
                log_callback(f"❌ {error_msg}")
            if st:
                st.error(f"❌ {error_msg}")
                with st.expander("🔍 Full Error Traceback", expanded=True):
                    import traceback
                    st.code(traceback.format_exc(), language="python")
            raise Exception(error_msg) from e
        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
