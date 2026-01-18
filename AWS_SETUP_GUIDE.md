# 🚀 AWS EC2 Deployment Guide for DevGuard

Complete step-by-step guide to deploy DevGuard on AWS EC2 with S3, DynamoDB, and Elastic IP.

---

## 📋 Prerequisites

- AWS Account (free tier eligible)
- AWS CLI installed and configured locally
- SSH key pair for EC2 access
- Google Gemini API Key

---

## 🎯 Architecture

```
EC2 Instance (t3.small)
├── Streamlit App (Port 8501)
├── S3 Bucket (Scan Reports)
├── DynamoDB Table (Future: User Scans)
└── Elastic IP (Static IP Address)
```

---

## 📝 Step-by-Step Deployment

### **Step 1: Create S3 Bucket**

1. **Go to AWS Console → S3**
2. **Click "Create bucket"**
3. **Configure:**
   - **Bucket name**: `devguard-reports-<region>-<your-unique-id>`
     - Example: `devguard-reports-us-east-1-123456789`
   - **Region**: Choose your region (e.g., `us-east-1`)
   - **Block Public Access**: ✅ Keep enabled (private bucket)
   - **Versioning**: Optional (recommended)
   - **Encryption**: Enable server-side encryption (SSE-S3)
4. **Click "Create bucket"**
5. **Note the bucket name** for later

---

### **Step 2: Create DynamoDB Table** (Optional - for future use)

1. **Go to AWS Console → DynamoDB**
2. **Click "Create table"**
3. **Configure:**
   - **Table name**: `devguard-scans`
   - **Partition key**: `user_id` (String)
   - **Sort key**: `scan_id` (String)
   - **Table settings**: Use default
   - **Capacity mode**: On-demand (pay-per-use)
4. **Click "Create table"**
5. **Enable TTL** (Time To Live):
   - Go to "Additional settings" → "Time to live (TTL)"
   - **TTL attribute**: `ttl`
   - **Enable**: ✅
6. **Note the table name** for later

---

### **Step 3: Create IAM Role for EC2**

1. **Go to AWS Console → IAM → Roles**
2. **Click "Create role"**
3. **Select "AWS service" → "EC2"**
4. **Click "Next"**
5. **Attach policies:**
   - `AmazonS3FullAccess` (or create custom policy with only your bucket)
   - `AmazonDynamoDBFullAccess` (or create custom policy with only your table)
   - `SecretsManagerReadWrite` (for API keys - optional)
6. **Role name**: `DevGuardEC2Role`
7. **Click "Create role"**
8. **Note the role ARN** for later

---

### **Step 4: Create EC2 Instance**

1. **Go to AWS Console → EC2 → Instances**
2. **Click "Launch instance"**
3. **Configure:**
   - **Name**: `devguard-app`
   - **AMI**: `Ubuntu Server 22.04 LTS` (free tier eligible)
   - **Instance type**: `t3.small` (2 vCPU, 2 GB RAM)
     - For testing: `t3.micro` (free tier eligible, but may be slow)
   - **Key pair**: Create new or select existing SSH key
     - ⚠️ **Download and save the .pem file securely**
   - **Network settings**: 
     - Create security group (we'll configure next)
   - **Configure storage**: 20 GB GP3 SSD (default)
   - **Advanced details**:
     - **IAM instance profile**: Select `DevGuardEC2Role`
4. **Click "Launch instance"**
5. **Wait for instance to be in "Running" state**

---

### **Step 5: Configure Security Group**

1. **Go to EC2 → Security Groups**
2. **Select the security group for your instance**
3. **Click "Edit inbound rules"**
4. **Add rules:**

   **Rule 1: SSH (for deployment)**
   - **Type**: SSH
   - **Port**: 22
   - **Source**: `My IP` (or your IP for security)

   **Rule 2: Streamlit (for web access)**
   - **Type**: Custom TCP
   - **Port**: 8501
   - **Source**: `0.0.0.0/0` (or restrict to specific IPs)
   - **Description**: Streamlit web app

5. **Click "Save rules"**

---

### **Step 6: Allocate and Associate Elastic IP**

1. **Go to EC2 → Elastic IPs**
2. **Click "Allocate Elastic IP address"**
3. **Configure:**
   - **Network border group**: Match your region
   - **Public IPv4 address pool**: Amazon's pool
4. **Click "Allocate"**
5. **Select the Elastic IP → Actions → Associate Elastic IP address**
6. **Configure:**
   - **Resource type**: Instance
   - **Instance**: Select your `devguard-app` instance
   - **Private IP address**: Auto-select
7. **Click "Associate"**
8. **Note the Elastic IP address** (e.g., `54.123.45.67`)

---

### **Step 7: Connect to EC2 Instance**

**Using SSH:**

```bash
# Change permissions on key file (first time only)
chmod 400 /path/to/your-key.pem

# Connect to EC2
ssh -i /path/to/your-key.pem ubuntu@<YOUR_ELASTIC_IP>
```

**Or using EC2 Instance Connect:**
- Click on instance → "Connect" → "EC2 Instance Connect" → "Connect"

---

### **Step 8: Deploy Application on EC2**

**On EC2 instance (via SSH):**

```bash
# Update system
sudo apt-get update -y

# Install Git
sudo apt-get install -y git

# Clone your repository (or upload files)
# Option 1: Clone from GitHub (recommended)
git clone <YOUR_REPO_URL> devguard
cd devguard

# Option 2: Upload files using SCP (from local machine)
# scp -r -i /path/to/key.pem /path/to/devguard ubuntu@<ELASTIC_IP>:~/devguard

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

---

### **Step 9: Configure Environment Variables**

**On EC2:**

```bash
cd ~/devguard

# Edit .env file
nano .env
```

**Set these values:**

```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key_here

# AWS Configuration
AWS_REGION=us-east-1  # Change to your region
DEVGUARD_S3_BUCKET=devguard-reports-us-east-1-123456789  # Your S3 bucket name
DEVGUARD_DYNAMODB_TABLE=devguard-scans  # Your DynamoDB table name

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Save and exit** (Ctrl+X, Y, Enter)

---

### **Step 10: Configure AWS Credentials** (Optional - if using IAM role)

**If you assigned IAM role to EC2:**
- No need to configure credentials! The instance will use the role automatically.

**If not using IAM role:**

```bash
# Install AWS CLI
sudo apt-get install -y awscli

# Configure AWS credentials
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter region: us-east-1
# Enter output format: json
```

---

### **Step 11: Set Up Systemd Service** (Optional - for auto-start)

**On EC2:**

```bash
cd ~/devguard

# Copy service file
sudo cp devguard.service /etc/systemd/system/

# Edit service file if needed (change paths)
sudo nano /etc/systemd/system/devguard.service

# Update paths in service file:
# WorkingDirectory=/home/ubuntu/devguard
# EnvironmentFile=/home/ubuntu/devguard/.env
# ExecStart=/home/ubuntu/devguard/venv/bin/streamlit run ...

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable devguard

# Start service
sudo systemctl start devguard

# Check status
sudo systemctl status devguard

# View logs
sudo journalctl -u devguard -f
```

---

### **Step 12: Start Application Manually** (Alternative)

**On EC2:**

```bash
cd ~/devguard

# Activate virtual environment
source venv/bin/activate

# Start Streamlit
./start.sh

# Or manually:
streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
```

---

### **Step 13: Access Application**

**Open in browser:**
```
http://<YOUR_ELASTIC_IP>:8501
```

**Example:**
```
http://54.123.45.67:8501
```

---

## 🔧 Troubleshooting

### **Application not accessible**

1. **Check Security Group:**
   - Ensure port 8501 is open
   - Source should be `0.0.0.0/0` (or your IP)

2. **Check if app is running:**
   ```bash
   # On EC2
   sudo netstat -tlnp | grep 8501
   # Or
   curl http://localhost:8501
   ```

3. **Check logs:**
   ```bash
   # If using systemd
   sudo journalctl -u devguard -n 100
   
   # Or check application logs
   tail -f ~/devguard/logs/*.log
   ```

### **S3 upload fails**

1. **Check IAM role:**
   - Ensure EC2 has `DevGuardEC2Role` attached
   - Verify role has S3 permissions

2. **Check bucket name:**
   - Verify bucket name in `.env` matches actual bucket

3. **Test S3 access:**
   ```bash
   # On EC2
   aws s3 ls s3://devguard-reports-us-east-1-123456789
   ```

### **Gemini API errors**

1. **Check API key:**
   - Verify `GEMINI_API_KEY` in `.env`
   - Ensure no extra spaces/quotes

2. **Check rate limits:**
   - Free tier: 20 requests/day, 5 requests/minute
   - Wait if limit reached

---

## 📊 Monitoring

### **CloudWatch Logs** (Optional)

1. **Install CloudWatch agent:**
   ```bash
   wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
   sudo dpkg -i amazon-cloudwatch-agent.deb
   ```

2. **Configure logs:**
   ```bash
   sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
   ```

---

## 🔒 Security Best Practices

1. **Use IAM roles** instead of access keys on EC2
2. **Restrict Security Group** to specific IPs (not `0.0.0.0/0`)
3. **Use Secrets Manager** for API keys (not `.env` file)
4. **Enable CloudWatch** for monitoring
5. **Regular updates:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

---

## 💰 Cost Estimation

**Monthly costs:**
- EC2 t3.small: ~$15/month
- Elastic IP: Free (when attached to running instance)
- S3 storage (10 GB): ~$0.23/month
- S3 requests: ~$0.01/month
- DynamoDB: ~$0.25/month (low usage)

**Total: ~$15-20/month**

---

## ✅ Deployment Checklist

- [ ] S3 bucket created
- [ ] DynamoDB table created (optional)
- [ ] IAM role created and attached to EC2
- [ ] EC2 instance launched
- [ ] Security group configured (port 8501 open)
- [ ] Elastic IP allocated and associated
- [ ] Application deployed on EC2
- [ ] Environment variables configured
- [ ] AWS credentials configured (or IAM role)
- [ ] Systemd service set up (optional)
- [ ] Application accessible via Elastic IP:8501
- [ ] S3 upload tested

---

## 🎉 Success!

Your DevGuard application should now be running at:
```
http://<YOUR_ELASTIC_IP>:8501
```

Scan reports will be automatically uploaded to S3 at:
```
s3://devguard-reports-<region>-<id>/reports/YYYY/MM/DD/report_YYYYMMDD_HHMMSS.csv
```

---

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)

---

**Need help?** Check the troubleshooting section or AWS support forums.

