# DevGuard - Agentic Compliance Risk Monitoring Agent

🛡️ **DevGuard** is an intelligent, agentic AI-powered security and compliance scanning agent for GitHub repositories. It autonomously scans repositories, detects security risks, and provides actionable advice to developers.

## Why DevGuard is an Agentic AI System

DevGuard demonstrates true agentic AI characteristics:

### 1. **Autonomous Decision-Making**
The agent autonomously decides:
- Which files to scan and in what order (prioritizing config files first)
- When to perform deep analysis vs quick pattern matching
- How to adapt scanning strategy based on repository structure
- When sufficient scanning has been completed

### 2. **Tool-Based Architecture**
DevGuard uses a LangChain agent framework with multiple specialized tools:
- `clone_repository`: Clones GitHub repos with size validation
- `list_files_to_scan`: Gets prioritized file list for scanning
- `scan_file_for_patterns`: Detects security patterns in files
- `analyze_risk_with_context`: Performs deep risk analysis with context
- `get_file_context_lines`: Extracts surrounding code context

The agent autonomously selects which tools to use to accomplish its goal.

### 3. **Intelligent Reasoning**
Beyond simple pattern matching, the agent:
- Evaluates context (file type, location, surrounding code) to assess risk severity
- Distinguishes between real secrets and test/example data
- Reduces false positives through contextual analysis
- Correlates related risks across multiple files

### 4. **Multi-Step Reasoning**
For each detected risk, the agent performs a multi-step analysis:
1. **Pattern Detection**: Identifies potential security issues
2. **Context Gathering**: Extracts surrounding code and file metadata
3. **Risk Validation**: Determines if the finding is a real risk or false positive
4. **Severity Assessment**: Adjusts severity based on context (test file vs production)
5. **Advice Generation**: Creates comprehensive fix suggestions with explanations

### 5. **Goal-Oriented Behavior**
The agent has a clear goal (find and analyze security risks) and autonomously:
- Plans the sequence of actions needed
- Executes the plan using available tools
- Adapts strategy based on findings

### 6. **Adaptive Strategy**
The agent adapts its approach based on what it discovers:
- If many secrets are found, it prioritizes secret scanning
- Config files are scanned before source code
- Test files receive different severity assessments than production code

## Features

- 🔐 **Hardcoded Secrets Detection**: AWS keys, GitHub tokens, Google API keys
- 🔑 **Password Assignment Detection**: Hardcoded passwords in code
- 🔥 **Firebase Security Rules**: Open read/write rules that expose data
- 🌐 **Network Security**: Public IP ranges in security configurations
- 📄 **Environment Files**: .env files committed to repositories
- 🤖 **Agentic AI**: Autonomous decision-making and intelligent reasoning
- 📊 **Comprehensive Reports**: Detailed findings with actionable advice
- 📥 **CSV Export**: Download scan results for documentation

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (for cloning repositories)
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## How to Run

### Local Development

1. **Start the Streamlit app**:
```bash
streamlit run app.py
```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Enter a GitHub repository URL** (public or private)

4. **If the repository is private**, enter your GitHub personal access token

5. **Click "Start Scan"** and watch the agent work!

### Usage Tips

- **Public Repositories**: Just paste the GitHub URL (no token needed)
- **Private Repositories**: Generate a GitHub personal access token with `repo` scope
- **Repository Size Limit**: Maximum 1GB (checked automatically)
- **Scan Time**: Depends on repository size, typically 30 seconds to 5 minutes

## Detailed AWS EC2 Deployment Guide

Deploy DevGuard on AWS EC2 for production use with the following step-by-step instructions.

### Step 1: Launch EC2 Instance

1. **Login to AWS Console** and navigate to EC2

2. **Launch Instance**:
   - Click "Launch Instance"
   - **Name**: `devguard-server` (optional)
   - **AMI**: Select Ubuntu 22.04 LTS or Amazon Linux 2023
   - **Instance Type**: `t3.medium` or larger (recommended: `t3.large` for better performance)
   - **Key Pair**: Create or select an existing key pair (download the `.pem` file)
   - **Network Settings**: 
     - Create or select a security group (see Step 2)
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) and HTTPS (port 443) from anywhere (0.0.0.0/0)
   - **Storage**: 20 GB minimum (GP3 SSD recommended)
   - Click "Launch Instance"

3. **Wait for instance to be running** and note the **Public IPv4 address**

### Step 2: Configure Security Group

1. **Go to Security Groups** in EC2 console

2. **Select your instance's security group** and click "Edit inbound rules"

3. **Add rules**:
   - **SSH (22)**: Type: SSH, Source: My IP (or specific IP)
   - **Custom TCP (8501)**: Port 8501, Source: 0.0.0.0/0 (for Streamlit)
   - **HTTP (80)**: Type: HTTP, Source: 0.0.0.0/0
   - **HTTPS (443)**: Type: HTTPS, Source: 0.0.0.0/0

4. **Save rules**

### Step 3: Connect to EC2 Instance

**On macOS/Linux**:
```bash
chmod 400 your-key-pair.pem
ssh -i your-key-pair.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

**On Windows** (using PuTTY or WSL):
```bash
# In WSL or Git Bash
ssh -i your-key-pair.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 4: Install System Dependencies

**For Ubuntu**:
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python, pip, and git
sudo apt install -y python3 python3-pip python3-venv git

# Install other dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

**For Amazon Linux 2023**:
```bash
# Update system
sudo dnf update -y

# Install Python, pip, and git
sudo dnf install -y python3 python3-pip git

# Install development tools
sudo dnf groupinstall -y "Development Tools"
```

### Step 5: Deploy DevGuard Application

1. **Clone the repository** (or upload files via SCP):
```bash
# Option 1: Clone from Git
git clone YOUR_REPO_URL
cd Devgaurd

# Option 2: Upload files via SCP (from your local machine)
# scp -i your-key-pair.pem -r /path/to/Devgaurd ubuntu@YOUR_EC2_PUBLIC_IP:~/
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Python dependencies**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Test the application**:
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

5. **Access the app** in your browser: `http://YOUR_EC2_PUBLIC_IP:8501`

### Step 6: Set Up Nginx Reverse Proxy (Optional but Recommended)

1. **Install Nginx**:
```bash
sudo apt install -y nginx  # Ubuntu
# or
sudo dnf install -y nginx  # Amazon Linux
```

2. **Create Nginx configuration**:
```bash
sudo nano /etc/nginx/sites-available/devguard
```

3. **Add configuration**:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

4. **Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/devguard /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

5. **Access app** via `http://YOUR_EC2_PUBLIC_IP` (port 80)

### Step 7: Set Up Systemd Service (Auto-Start)

1. **Create systemd service file**:
```bash
sudo nano /etc/systemd/system/devguard.service
```

2. **Add service configuration**:
```ini
[Unit]
Description=DevGuard Streamlit Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Devgaurd
Environment="PATH=/home/ubuntu/Devgaurd/venv/bin"
ExecStart=/home/ubuntu/Devgaurd/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note**: Update paths according to your setup.

3. **Enable and start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable devguard
sudo systemctl start devguard
sudo systemctl status devguard  # Check status
```

4. **View logs**:
```bash
sudo journalctl -u devguard -f
```

### Step 8: Set Up HTTPS with Let's Encrypt (Optional but Recommended)

1. **Install Certbot**:
```bash
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu
# or
sudo dnf install -y certbot python3-certbot-nginx  # Amazon Linux
```

2. **Obtain SSL certificate**:
```bash
sudo certbot --nginx -d your-domain.com
```

3. **Certbot automatically configures Nginx** for HTTPS

4. **Auto-renewal** (already set up by Certbot):
```bash
sudo certbot renew --dry-run  # Test renewal
```

### Step 9: Firewall Configuration (Optional)

**Ubuntu (UFW)**:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**Amazon Linux (firewalld)**:
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Security Considerations

1. **GitHub Tokens**: DevGuard does not store tokens - they're only used during cloning
2. **Repository Data**: Cloned repositories are deleted after scanning
3. **Network**: Consider restricting access to your EC2 security group to specific IPs
4. **HTTPS**: Always use HTTPS in production (Let's Encrypt provides free certificates)
5. **Firewall**: Configure firewall rules to restrict unnecessary ports

## Troubleshooting

### Application won't start
- Check if port 8501 is available: `sudo lsof -i :8501`
- Verify virtual environment is activated
- Check logs: `sudo journalctl -u devguard -n 50`

### Can't access from browser
- Verify security group allows inbound traffic on port 8501 (or 80/443)
- Check EC2 instance status is "running"
- Verify Streamlit is listening on 0.0.0.0, not 127.0.0.1

### Permission errors
- Ensure user has correct permissions for the DevGuard directory
- Check file ownership: `sudo chown -R ubuntu:ubuntu /home/ubuntu/Devgaurd`

### Repository clone fails
- Verify GitHub token has correct permissions (`repo` scope for private repos)
- Check repository URL is correct
- Ensure repository size is under 1GB limit

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available for use and modification.

## Support

For issues, questions, or contributions, please open an issue on the repository.

---

**DevGuard** - Autonomous security scanning with intelligent reasoning 🛡️🤖


