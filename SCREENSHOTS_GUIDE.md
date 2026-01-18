# 📸 Screenshots Guide for DevGuard

This document describes the key screenshots to capture for documentation and presentation.

---

## **Screenshot 1: Main Application Interface**

**Location**: `app.py` - Main page
**When to capture**: After application starts, before uploading files

**What to show:**
- Streamlit application header: "🛡️ DevGuard - LLM-Powered Compliance Risk Monitoring Agent"
- API Configuration section (Gemini API Key input field)
- File Upload section (empty file uploader)
- "Start LLM-Powered Scan" button (disabled)
- Rate limit information expander

**How to capture:**
1. Start application: `streamlit run app.py`
2. Open browser at `http://localhost:8501`
3. Screenshot the main page

---

## **Screenshot 2: File Upload**

**Location**: After uploading files
**When to capture**: Files selected but before clicking scan

**What to show:**
- File uploader showing selected files
- File names and sizes visible
- "X file(s) selected for scanning" message
- Expanded file list (if applicable)

**How to capture:**
1. Upload 3-5 files (include test_repo files)
2. Screenshot showing file list

---

## **Screenshot 3: Scanning in Progress**

**Location**: During scan execution
**When to capture**: Mid-scan, showing real-time logs

**What to show:**
- Progress bar showing percentage
- Status messages: "🤖 LLM Agent is analyzing uploaded files..."
- Execution log expander showing:
  - File processing messages
  - Chunk extraction counts
  - Batch creation
  - LLM analysis progress
  - Rate limiting waits

**How to capture:**
1. Start a scan with multiple files
2. Wait until scan is in progress (not completed)
3. Expand "Real-Time Execution Log"
4. Screenshot showing active scanning

---

## **Screenshot 4: Scan Results - Findings List**

**Location**: After scan completes
**When to capture**: Results displayed

**What to show:**
- Summary statistics (Total Issues, High/Medium/Low counts)
- Multiple finding cards displayed
- Each finding showing:
  - Severity indicator (🔴🟡🟢)
  - Risk type
  - File name and line number
  - Brief description

**How to capture:**
1. Complete a scan with security issues
2. Scroll to results section
3. Screenshot showing multiple findings

---

## **Screenshot 5: Detailed Finding View**

**Location**: Expanded finding card
**When to capture**: One finding fully expanded

**What to show:**
- Complete finding card with:
  - Severity indicator and risk type
  - File name and line number
  - Issue overview/description
  - "Agent Analysis: Why This Is a Security Risk" section
    - Detailed explanation
    - Attack scenarios
    - Impact analysis
  - "How to Overcome This Security Difficulty" section
    - Step-by-step remediation
  - "Specific Code/Configuration Changes Required" section
    - Before/after code examples

**How to capture:**
1. Expand a high-severity finding
2. Scroll to show all sections
3. Screenshot complete view

---

## **Screenshot 6: AWS Storage Status**

**Location**: AWS Storage Status expander
**When to capture**: After configuring AWS credentials

**What to show:**
- S3 Storage: ✅ Connected status with bucket name
- DynamoDB Storage: ✅ Connected status with table name
- Session ID displayed
- Both storage systems showing green success indicators

**How to capture:**
1. Configure `.env` with AWS credentials
2. Restart application
3. Expand "💾 AWS Storage Status"
4. Screenshot showing both connected

---

## **Screenshot 7: Scan History**

**Location**: Scan History section
**When to capture**: After multiple scans completed

**What to show:**
- "📜 Scan History (from DynamoDB)" expander
- List of previous scans with:
  - Scan ID
  - Timestamp
  - Issue count metrics
  - "View Details" buttons
- At least 2-3 historical scans displayed

**How to capture:**
1. Complete 2-3 scans
2. Expand "Scan History" section
3. Screenshot showing historical scans

---

## **Screenshot 8: Scan History - Details**

**Location**: Expanded scan details
**When to capture**: After clicking "View Details" on a historical scan

**What to show:**
- Scan metadata (ID, timestamp)
- Findings list from that scan
- Issue breakdown
- Link to S3 report (if available)

**How to capture:**
1. Click "View Details" on a historical scan
2. Screenshot showing scan details

---

## **Screenshot 9: S3 Upload Success**

**Location**: After scan with S3 upload
**When to capture**: Showing S3 upload confirmation

**What to show:**
- Success message: "✅ CSV report uploaded to S3: `reports/2024/01/18/report_20240118_123456.csv`"
- S3 report URL (if displayed)
- Download button for local CSV

**How to capture:**
1. Complete scan with S3 configured
2. Scroll to download section
3. Screenshot showing S3 upload confirmation

---

## **Screenshot 10: Clean Scan Result**

**Location**: After scan with no issues found
**When to capture**: Showing success message

**What to show:**
- "🎉 No security issues found! Your repository looks secure."
- Summary showing 0 issues
- Success indicators

**How to capture:**
1. Scan a clean repository
2. Screenshot showing success message

---

## **Screenshot 11: Error Handling**

**Location**: Error display
**When to capture**: Showing graceful error handling

**What to show:**
- Error message displayed
- Error details in expander
- Clear error description
- Application still functional

**How to capture:**
1. Trigger an error (e.g., invalid API key, network error)
2. Screenshot error display

---

## **Screenshot 12: System Architecture**

**Location**: Documentation or architecture diagram
**What to show:**
- System components diagram
- Data flow arrows
- AWS services (EC2, S3, DynamoDB)
- External API (Gemini)
- User browser

**How to create:**
- Use diagramming tool (Draw.io, Lucidchart, etc.)
- Reference architecture diagram from DOCUMENTATION.md

---

## **Screenshot 13: Code Examples**

**Location**: Documentation or presentation
**What to show:**
1. **Chunk Filtering Code**
   ```python
   # scanner/filter.py
   risky_chunks = filter_risky_chunks(chunks)
   ```
2. **LLM Analysis Code**
   ```python
   # scanner/tools/llm_scan_tool.py
   response = llm.invoke(prompt)
   ```
3. **Storage Integration Code**
   ```python
   # scanner/storage.py
   s3_storage.upload_report(findings)
   ```

---

## **Screenshot 14: AWS Console Views**

### **14a: S3 Bucket Contents**
- Navigate to S3 bucket in AWS Console
- Show folder structure: `reports/2024/01/18/`
- Show JSON and CSV files
- Screenshot bucket contents

### **14b: DynamoDB Table**
- Navigate to DynamoDB table
- Show table items with:
  - user_id
  - scan_id
  - timestamp
  - total_findings
- Screenshot table view

### **14c: EC2 Instance**
- EC2 console showing running instance
- Instance details (type, status, Elastic IP)
- Security group rules
- Screenshot instance view

---

## **Screenshot 15: Deployment Scripts**

**Location**: Terminal/Command Line
**What to show:**
1. **Deployment Output**
   ```bash
   $ ./deploy.sh
   [1/8] Updating system packages...
   [2/8] Installing system dependencies...
   ...
   ✅ Deployment complete!
   ```
2. **Service Status**
   ```bash
   $ sudo systemctl status devguard
   Active: active (running)
   ```
3. **Update Script**
   ```bash
   $ ./update-devguard.sh
   ✅ Already up to date
   ```

---

## 📝 Screenshot Capturing Tips

### **Tools:**
- **macOS**: `Cmd + Shift + 4` (select area), `Cmd + Shift + 3` (full screen)
- **Windows**: `Win + Shift + S` (Snipping Tool), `Print Screen`
- **Linux**: `Shift + Print Screen` (GNOME), or `scrot`

### **Best Practices:**
1. **High Resolution**: Use full browser window
2. **Consistent Size**: Maintain same window size
3. **Clear Labels**: Add annotations if needed
4. **Hide Sensitive Data**: Blur API keys, IP addresses
5. **Multiple Views**: Show different states (empty, processing, results)

### **Post-Processing:**
- Crop to relevant sections
- Add arrows/annotations (if needed)
- Ensure text is readable
- Maintain aspect ratio

---

## 🎨 Screenshot Sequence for Demo

1. **Start**: Main application interface
2. **Upload**: Files selected
3. **Progress**: Scanning in progress with logs
4. **Results**: Findings list
5. **Detail**: One finding expanded
6. **Storage**: AWS status
7. **History**: Scan history
8. **S3**: S3 bucket contents (AWS Console)
9. **DynamoDB**: DynamoDB table (AWS Console)

---

## 📋 Checklist

- [ ] Screenshot 1: Main Interface
- [ ] Screenshot 2: File Upload
- [ ] Screenshot 3: Scanning Progress
- [ ] Screenshot 4: Results List
- [ ] Screenshot 5: Detailed Finding
- [ ] Screenshot 6: AWS Storage Status
- [ ] Screenshot 7: Scan History
- [ ] Screenshot 8: History Details
- [ ] Screenshot 9: S3 Upload Success
- [ ] Screenshot 10: Clean Scan
- [ ] Screenshot 11: Error Handling
- [ ] Screenshot 12: Architecture Diagram
- [ ] Screenshot 13: Code Examples
- [ ] Screenshot 14: AWS Console Views
- [ ] Screenshot 15: Deployment Scripts

---

**Note**: Actual screenshots should be captured from the running application. The descriptions above guide what each screenshot should contain.

