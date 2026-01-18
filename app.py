"""DevGuard - Agentic Compliance Risk Monitoring Agent."""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from scanner.agent import ScanningAgent
from scanner.utils import export_findings_to_csv
from scanner.storage import S3Storage, DynamoDBStorage
import uuid


st.set_page_config(
    page_title="DevGuard - Compliance Risk Monitor",
    page_icon="🛡️",
    layout="wide"
)

# Initialize session state
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []
if 'scan_in_progress' not in st.session_state:
    st.session_state.scan_in_progress = False
if 'scan_errors' not in st.session_state:
    st.session_state.scan_errors = []
if 'scan_logs' not in st.session_state:
    st.session_state.scan_logs = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())  # Generate unique session ID
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []
if 's3_storage' not in st.session_state:
    st.session_state.s3_storage = S3Storage()
if 'dynamodb_storage' not in st.session_state:
    st.session_state.dynamodb_storage = DynamoDBStorage()


def main():
    st.title("🛡️ DevGuard - LLM-Powered Compliance Risk Monitoring Agent")
    st.markdown("**Autonomous AI agent with advanced reasoning for security and compliance scanning**")
    st.info("🤖 This agent uses LLM (Google Gemini) to autonomously reason about code security, detect risks, and provide intelligent advice.")
    
    # Important: Show rate limit info
    with st.expander("⚠️ **Important: Gemini API Limits (Free Tier)**", expanded=False):
        st.warning("""
        **Gemini Free Tier Limits:**
        - 📊 **Daily Quota:** 20 requests per day (resets at midnight Pacific Time)
        - ⏱️ **Rate Limit:** 5 requests per minute
        
        **Recommendations:**
        - Scan small projects (3-5 files) to stay within limits
        - Wait between scans if you hit the daily quota
        - Upgrade to paid tier for higher limits: https://ai.google.dev/pricing
        """)
    
    st.markdown("---")
    
    # Input section
    st.subheader("🔑 API Configuration")
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key for LLM-powered analysis",
        placeholder="AIza...",
        value=os.environ.get("GEMINI_API_KEY", "")
    )
    
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    st.markdown("---")
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📁 Upload Project Files")
    uploaded_files = st.file_uploader(
        "Upload your project files for security scanning",
        type=['py', 'js', 'ts', 'json', 'yml', 'yaml', 'env', 'txt', 'md', 'java', 'go', 'rs', 'php', 'rb'],
        accept_multiple_files=True,
        help="Select one or more files to scan. Common file types: .py, .js, .json, .yml, .env, etc."
    )
    
    if uploaded_files:
        st.info(f"📎 **{len(uploaded_files)} file(s) selected** for scanning")
        with st.expander("📋 View uploaded files", expanded=False):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size} bytes)")
    
    st.markdown("---")
    
    # Scan button
    scan_button = st.button("🔍 Start LLM-Powered Scan", type="primary", disabled=st.session_state.scan_in_progress)
    
    if scan_button and uploaded_files:
        if not gemini_api_key:
            st.error("⚠️ Please enter your Gemini API key to enable LLM-powered analysis")
            return
        
        if not uploaded_files or len(uploaded_files) == 0:
            st.error("⚠️ Please upload at least one file to scan")
            return
        
        st.session_state.scan_in_progress = True
        st.session_state.scan_results = []
        st.session_state.scan_errors = []  # Clear previous errors
        st.session_state.scan_logs = []  # Clear previous logs
        
        # Create status/log container (persistent)
        status_container = st.container()
        with status_container:
            st.subheader("📊 Execution Status")
            
            # Show persistent logs with real-time updates
            log_container = st.container()
            with log_container:
                if st.session_state.scan_logs:
                    with st.expander("📋 **Real-Time Execution Log** (Findings shown here as discovered)", expanded=True):
                        # Show logs with highlighting for findings
                        for log_msg in st.session_state.scan_logs[-50:]:
                            if "SECURITY ISSUE" in log_msg or "🔴" in log_msg:
                                st.warning(f"🚨 {log_msg}")
                            elif "✅" in log_msg or "Found" in log_msg:
                                st.success(log_msg)
                            elif "❌" in log_msg or "Error" in log_msg:
                                st.error(log_msg)
                            elif "⚠️" in log_msg:
                                st.warning(log_msg)
                            else:
                                st.text(log_msg)
            
            # Show persistent errors (always visible if they exist)
            if st.session_state.scan_errors:
                st.error("❌ Errors occurred during scan:")
                for error in st.session_state.scan_errors:
                    with st.expander(f"❌ {error.get('title', 'Error')}", expanded=True):
                        st.error(error.get('message', ''))
                        if error.get('traceback'):
                            st.code(error['traceback'], language="python")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Log/error tracking functions that persist to session state
        def add_log(message: str):
            log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {message}"
            st.session_state.scan_logs.append(log_msg)
            if len(st.session_state.scan_logs) > 50:
                st.session_state.scan_logs = st.session_state.scan_logs[-50:]
        
        def add_error(title: str, message: str, exception=None):
            error_entry = {
                'title': title,
                'message': message,
                'traceback': None
            }
            if exception:
                import traceback
                error_entry['traceback'] = traceback.format_exc()
            st.session_state.scan_errors.append(error_entry)
            # Keep last 10 errors
            if len(st.session_state.scan_errors) > 10:
                st.session_state.scan_errors = st.session_state.scan_errors[-10:]
        
        try:
            add_log("Initializing LLM-powered agent...")
            status_text.info("🚀 Starting scan...")
            progress_bar.progress(10)
            
            # Initialize LLM-powered agent
            agent = ScanningAgent(llm_api_key=gemini_api_key)
            add_log("Agent initialized successfully")
            progress_bar.progress(20)
            
            # Run LLM-powered scan on uploaded files
            add_log(f"Starting file scan... {len(uploaded_files)} file(s) to analyze")
            status_text.info("🤖 LLM Agent is analyzing uploaded files...")
            
            # Process files and get findings (stored incrementally in session state)
            findings = agent.scan_uploaded_files(uploaded_files, add_log)
            
            add_log(f"Scan completed! Found {len(findings)} security issues")
            st.session_state.scan_results = findings
            
            # Generate scan ID and metadata
            scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_metadata = {
                'file_count': len(uploaded_files),
                'file_names': [f.name for f in uploaded_files],
                'scan_duration': None,  # Could track this if needed
                'timestamp': datetime.now().isoformat()
            }
            
            # Upload JSON report to S3 first (so we can reference it in DynamoDB)
            s3_json_key = None
            if st.session_state.s3_storage and st.session_state.s3_storage.s3_client and findings:
                try:
                    s3_json_key = st.session_state.s3_storage.upload_report(findings, report_id=scan_id)
                    if s3_json_key:
                        add_log(f"✅ JSON report uploaded to S3: {s3_json_key}")
                except Exception as e:
                    add_log(f"⚠️ Could not upload JSON to S3: {str(e)[:200]}")
            
            # Save to DynamoDB (including S3 key reference)
            dynamodb_saved = False
            if st.session_state.dynamodb_storage and st.session_state.dynamodb_storage.table:
                try:
                    dynamodb_saved = st.session_state.dynamodb_storage.save_scan(
                        user_id=st.session_state.user_id,
                        scan_id=scan_id,
                        findings=findings,
                        metadata=scan_metadata,
                        s3_key=s3_json_key
                    )
                    if dynamodb_saved:
                        add_log(f"✅ Scan history saved to DynamoDB (Scan ID: {scan_id})")
                except Exception as e:
                    add_log(f"⚠️ Could not save to DynamoDB: {str(e)[:200]}")
            
            progress_bar.progress(100)
            
            # Success message with storage status
            success_msg = f"✅ LLM-powered scan completed! Found {len(findings)} issues."
            if dynamodb_saved:
                success_msg += " | 💾 Saved to DynamoDB"
            if s3_json_key:
                success_msg += " | 📦 Uploaded to S3"
            status_text.success(success_msg)
        
        except ValueError as e:
            error_msg = f"Configuration error: {str(e)}"
            add_error("Configuration Error", error_msg, e)
            status_text.error("❌ Configuration Error")
            progress_bar.progress(0)
        
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            add_error("Scan Failed", error_msg, e)
            status_text.error("❌ Scan Failed")
            progress_bar.progress(0)
        
        finally:
            st.session_state.scan_in_progress = False
            st.rerun()
    
    elif scan_button and not uploaded_files:
        st.warning("⚠️ Please upload at least one file to scan")
    
    # Always show persistent errors/logs section even if no scan in progress
    if st.session_state.scan_errors or (st.session_state.scan_logs and len(st.session_state.scan_logs) > 0):
        st.markdown("---")
        st.subheader("📊 Scan History")
        
        # Show persistent errors (always visible)
        if st.session_state.scan_errors:
            st.error(f"❌ {len(st.session_state.scan_errors)} error(s) occurred:")
            for idx, error in enumerate(st.session_state.scan_errors):
                with st.expander(f"❌ Error {idx + 1}: {error.get('title', 'Error')}", expanded=True):
                    st.error(error.get('message', ''))
                    if error.get('traceback'):
                        st.code(error['traceback'], language="python")
            if st.button("🗑️ Clear Errors"):
                st.session_state.scan_errors = []
                st.rerun()
        
        # Show persistent logs
        if st.session_state.scan_logs:
            with st.expander("📋 Execution Logs", expanded=False):
                st.code("\n".join(st.session_state.scan_logs[-50:]), language=None)
                if st.button("🗑️ Clear Logs"):
                    st.session_state.scan_logs = []
                    st.rerun()
    
    # Display results
    if st.session_state.scan_results:
        st.markdown("---")
        st.header("📊 Scan Results")
        
        findings = st.session_state.scan_results
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Issues", len(findings))
        
        high_count = len([f for f in findings if f.get('severity') == 'High'])
        medium_count = len([f for f in findings if f.get('severity') == 'Medium'])
        low_count = len([f for f in findings if f.get('severity') == 'Low'])
        
        with col2:
            st.metric("🔴 High", high_count)
        with col3:
            st.metric("🟡 Medium", medium_count)
        with col4:
            st.metric("🟢 Low", low_count)
        
        st.markdown("---")
        
        # Display findings with detailed agent-like explanations
        if findings:
            st.markdown("### 🤖 **Detailed Security Analysis** (Agent-Generated Explanations)")
            st.info("💡 Each finding below includes comprehensive LLM-generated analysis, attack scenarios, and step-by-step remediation guidance.")
            
            # Prepare dataframe for table view (optional)
            df_data = []
            for finding in findings:
                df_data.append({
                    'File Name': finding.get('file_name', ''),
                    'Line #': finding.get('line_number', ''),
                    'Risk Type': finding.get('risk_type', ''),
                    'Severity': finding.get('severity', ''),
                    'Description': finding.get('description', '')[:100] + '...' if len(finding.get('description', '')) > 100 else finding.get('description', ''),
                })
            df = pd.DataFrame(df_data)
            
            # Display each finding with comprehensive agent-like explanation
            for idx, finding in enumerate(findings, 1):
                # Severity color coding
                severity = finding.get('severity', 'Unknown').lower()
                if severity == 'high' or severity == 'critical':
                    severity_icon = "🔴"
                    severity_color = "red"
                elif severity == 'medium':
                    severity_icon = "🟡"
                    severity_color = "orange"
                else:
                    severity_icon = "🟢"
                    severity_color = "green"
                
                # Main finding card
                st.markdown("---")
                with st.container():
                    # Header with severity indicator
                    st.markdown(f"""
                    <div style='background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-left: 5px solid {severity_color}; margin-bottom: 10px;'>
                        <h3 style='margin: 0;'>
                            {severity_icon} <strong>Finding #{idx}:</strong> {finding.get('risk_type', 'Unknown Risk')}
                            <span style='color: {severity_color}; font-size: 0.9em;'>[{finding.get('severity', 'Unknown')} Severity]</span>
                        </h3>
                        <p style='margin: 5px 0 0 0; color: #aaa;'>
                            📄 <code>{os.path.basename(finding.get('file_name', ''))}</code> 
                            | 📍 Line {finding.get('line_number', '?')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Quick description
                    description = finding.get('description', '')
                    if description:
                        st.markdown(f"**📋 Issue Overview:** {description}")
                    
                    # Detailed explanation (agent reasoning)
                    st.markdown("---")
                    st.markdown("### 🤖 **Agent Analysis: Why This Is a Security Risk**")
                    why_problem = finding.get('why_problem', '')
                    if why_problem:
                        # Convert markdown-style formatting to display properly
                        why_problem_formatted = why_problem.replace('\n\n', '\n').replace('\n', '  \n')
                        st.markdown(f"""
                        <div style='background-color: rgba(255,0,0,0.08); padding: 20px; border-radius: 8px; border-left: 5px solid #ff4444; margin: 10px 0; line-height: 1.6;'>
                            {why_problem_formatted}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Detailed reasoning not available. This should be generated by the LLM agent.")
                    
                    # Remediation strategy
                    st.markdown("---")
                    st.markdown("### 🛡️ **How to Overcome This Security Difficulty**")
                    
                    fix_suggestion = finding.get('fix_suggestion', '')
                    if fix_suggestion:
                        fix_suggestion_formatted = fix_suggestion.replace('\n\n', '\n').replace('\n', '  \n')
                        st.markdown(f"""
                        <div style='background-color: rgba(0,200,100,0.08); padding: 20px; border-radius: 8px; border-left: 5px solid #00c864; margin: 10px 0; line-height: 1.6;'>
                            {fix_suggestion_formatted}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("ℹ️ Fix suggestion not available.")
                    
                    # Specific code changes
                    what_to_change = finding.get('what_to_change', '')
                    if what_to_change:
                        st.markdown("---")
                        st.markdown("### 🔧 **Specific Code/Configuration Changes Required**")
                        what_to_change_formatted = what_to_change.replace('\n\n', '\n').replace('\n', '  \n')
                        st.markdown(f"""
                        <div style='background-color: rgba(255,200,0,0.08); padding: 20px; border-radius: 8px; border-left: 5px solid #ffc800; margin: 10px 0; line-height: 1.6;'>
                            {what_to_change_formatted}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Additional info in expandable section
                    with st.expander("📊 **Additional Details**", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**File Information**")
                            st.text(f"Full Path: {finding.get('file_name', 'N/A')}")
                            st.text(f"Line Number: {finding.get('line_number', 'N/A')}")
                        with col2:
                            st.markdown("**Risk Classification**")
                            st.text(f"Risk Type: {finding.get('risk_type', 'N/A')}")
                            st.text(f"Severity: {finding.get('severity', 'N/A')}")
            
            # Optional table view (collapsed by default)
            with st.expander("📋 **Summary Table View** (Quick Reference)", expanded=False):
                st.dataframe(df, use_container_width=True, height=400)
                st.caption("💡 Expand each finding above for detailed agent-generated analysis and remediation steps.")
            
            # Download CSV and upload to S3
            st.markdown("---")
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = os.path.join('reports', f'devguard_scan_{report_id}.csv')
            os.makedirs('reports', exist_ok=True)
            
            # Try to export to local CSV first
            csv_exported = export_findings_to_csv(findings, csv_file)
            
            # Upload CSV to S3 (if configured)
            s3_key = None
            s3_url = None
            
            if csv_exported and st.session_state.s3_storage and st.session_state.s3_storage.s3_client:
                # Upload CSV to S3
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        csv_content = f.read()
                    s3_key = st.session_state.s3_storage.upload_csv_report(csv_content, report_id)
                    if s3_key:
                        s3_url = st.session_state.s3_storage.get_report_url(s3_key, expires_in=86400)  # 24 hours
                        st.success(f"✅ CSV report uploaded to S3: `{s3_key}`")
                except Exception as e:
                    st.warning(f"⚠️ Could not upload CSV to S3: {str(e)[:200]}")
            
            # Show download button
            if csv_exported:
                with open(csv_file, 'rb') as f:
                    st.download_button(
                        label="📥 Download CSV Report",
                        data=f.read(),
                        file_name=os.path.basename(csv_file),
                        mime="text/csv"
                    )
                
                # Show S3 URL if available
                if s3_url:
                    st.info(f"🔗 **S3 Report URL** (valid for 24 hours): [Download from S3]({s3_url})")
        else:
            st.success("🎉 No security issues found! Your repository looks secure.")
    
    # Info section
    st.markdown("---")
    with st.expander("ℹ️ About DevGuard", expanded=False):
        st.markdown("""
        **DevGuard** is an agentic AI compliance risk monitoring agent that autonomously scans GitHub repositories 
        for security and configuration risks.
        
        ### Agentic AI Features:
        - **Autonomous Decision-Making**: The agent decides what files to scan and in what order
        - **Intelligent Reasoning**: Context-aware risk assessment beyond simple pattern matching
        - **Multi-Step Analysis**: Chains tool calls to fully understand each risk
        - **Actionable Advice**: Provides specific guidance on what to change and why it matters
        
        ### What DevGuard Scans For:
        - 🔐 Hardcoded secrets (AWS keys, GitHub tokens, API keys)
        - 🔑 Password assignments in code
        - 🔥 Firebase open security rules
        - 🌐 Public IP open ports in security configs
        - 📄 .env files in repository
        
        ### How It Works:
        1. Agent clones the repository (supports private repos with token)
        2. Agent autonomously prioritizes files for scanning
        3. Agent scans files using pattern detection
        4. Agent analyzes each finding with context to validate risks
        5. Agent generates comprehensive advice for each issue
        6. Results are displayed with actionable recommendations
        
        **Note**: DevGuard does not store any GitHub tokens or repository data. All scanning happens locally.
        """)


if __name__ == "__main__":
    main()

