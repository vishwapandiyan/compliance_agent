# 🚀 AWS Deployment Plan for DevGuard

## 📋 Architecture Overview

### Current State
- **Application Type**: Streamlit web app (Python)
- **Data Storage**: In-memory (session state) + local CSV reports
- **No Database**: Currently stateless (no user accounts, no scan history)
- **External API**: Google Gemini API (rate-limited)

### Recommended AWS Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cloud Architecture                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌──────────────────┐
│   EC2 Instance  │────────▶│  Streamlit App   │
│   (Ubuntu 22.04)│         │   (Port 8501)    │
└─────────────────┘         └──────────────────┘
        │                           │
        │                           │
        ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│  Security Group │         │   S3 Bucket      │
│  (Port 8501)    │         │  (Scan Reports)  │
└─────────────────┘         └──────────────────┘
        │                           │
        │                           │
        ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│  Application LB │         │   DynamoDB       │
│  (Optional)     │         │  (Future: Users) │
└─────────────────┘         └──────────────────┘
```

---

## 🗄️ Database Options Analysis

### Option 1: **DynamoDB** (Recommended for Future)
**When to use:** If you plan to add:
- User authentication/accounts
- Scan history per user
- Analytics/metrics
- API for external integrations

**Pros:**
- ✅ Serverless (no management)
- ✅ Auto-scaling
- ✅ Low latency
- ✅ Pay-per-use (cost-effective)
- ✅ NoSQL (flexible schema)

**Cons:**
- ❌ Eventually consistent (not good for real-time sync)
- ❌ Query limitations (need to design keys carefully)

**Cost:** ~$0.25 per million reads, $1.25 per million writes

---

### Option 2: **RDS PostgreSQL** (If you need relational data)
**When to use:** If you need:
- Complex queries
- Transactions
- Relationships (users → scans → findings)
- SQL familiarity

**Pros:**
- ✅ ACID transactions
- ✅ SQL queries
- ✅ Relationships
- ✅ Familiar for SQL devs

**Cons:**
- ❌ More expensive (~$15-30/month minimum)
- ❌ Requires management/backups
- ❌ Fixed instance size

**Cost:** t3.micro: ~$15/month (free tier available for 12 months)

---

### Option 3: **S3 Only** (Current State - No Database)
**When to use:** 
- Stateless application (current state)
- Only need to store scan reports
- No user accounts needed

**Pros:**
- ✅ Super cheap (~$0.023/GB/month)
- ✅ Unlimited storage
- ✅ Simple (just file storage)
- ✅ No database overhead

**Cons:**
- ❌ Not a database (can't query easily)
- ❌ No user management
- ❌ No scan history tracking

**Cost:** ~$0.023 per GB per month

---

## 🎯 Recommendation for DevGuard

### **Phase 1: Initial Deployment (Current)**
- **EC2**: Host Streamlit app
- **S3**: Store scan reports (optional enhancement)
- **No Database**: Keep stateless for now

### **Phase 2: Future Enhancement (Optional)**
- **DynamoDB**: Add if you want:
  - User accounts
  - Scan history
  - Analytics dashboard

---

## 🛠️ Infrastructure Components

### 1. **EC2 Instance**
- **Instance Type**: `t3.small` or `t3.medium` (2 vCPU, 2-4 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 20 GB GP3 SSD
- **Security Group**: Open port 8501 (Streamlit) or 80/443 (with reverse proxy)
- **Cost**: ~$15-30/month

### 2. **S3 Bucket** (Optional)
- **Purpose**: Store CSV scan reports
- **Bucket Name**: `devguard-reports-<region>-<account-id>`
- **Access**: Private (IAM role-based)
- **Cost**: ~$0.023/GB/month + requests

### 3. **DynamoDB Table** (Future - Optional)
- **Table Name**: `devguard-scans`
- **Partition Key**: `user_id` (string)
- **Sort Key**: `scan_id` (string, timestamp-based)
- **TTL**: Enable for automatic cleanup (e.g., 90 days)

### 4. **IAM Role for EC2**
- Allows EC2 to:
  - Write to S3 bucket
  - Read/write DynamoDB (if used)
  - Access Secrets Manager (for API keys)

### 5. **Secrets Manager** (Recommended)
- Store `GEMINI_API_KEY` securely
- EC2 retrieves via IAM role (no hardcoded secrets)

---

## 📝 Step-by-Step Deployment Plan

### **Step 1: Clean Up Local Files**
1. Delete `venv/` (don't deploy virtual environment)
2. Delete `__pycache__/` folders (auto-generated)
3. Delete `test_repo-main/` (test files)
4. Create `.gitignore`
5. Create `.dockerignore` (if using Docker)

### **Step 2: Prepare Application**
1. Update `requirements.txt` (ensure all deps)
2. Create `Dockerfile` (optional but recommended)
3. Create startup script (`start.sh`)
4. Add environment variable handling
5. Configure logging

### **Step 3: Set Up AWS Resources**
1. Create S3 bucket (optional)
2. Create IAM role for EC2
3. Set up Secrets Manager (for API keys)
4. Create EC2 instance
5. Configure Security Group

### **Step 4: Deploy Application**
1. Connect to EC2 via SSH
2. Install dependencies (Python 3.10+, pip)
3. Clone/push code to EC2
4. Set up virtual environment
5. Install requirements
6. Configure environment variables
7. Test application locally
8. Set up systemd service or PM2
9. Configure reverse proxy (Nginx) - optional
10. Set up SSL/TLS (Let's Encrypt) - optional

### **Step 5: Optional Enhancements**
1. Configure CloudWatch for monitoring
2. Set up auto-scaling (if needed)
3. Configure backup for S3/DynamoDB
4. Set up CI/CD (GitHub Actions → EC2)

---

## 💰 Cost Estimation

### Minimal Setup (EC2 Only)
- EC2 t3.small: ~$15/month
- Data transfer: ~$1-5/month
- **Total: ~$16-20/month**

### With S3
- EC2 t3.small: ~$15/month
- S3 storage (10 GB): ~$0.23/month
- S3 requests: ~$0.01/month
- Data transfer: ~$1-5/month
- **Total: ~$16-25/month**

### With S3 + DynamoDB
- EC2 t3.small: ~$15/month
- S3 storage: ~$0.23/month
- DynamoDB (1M reads, 100K writes/month): ~$0.28/month
- Data transfer: ~$1-5/month
- **Total: ~$16-20/month**

---

## 🔒 Security Considerations

1. **Never hardcode API keys** - Use AWS Secrets Manager
2. **Security Group**: Only allow necessary ports
3. **IAM Roles**: Use roles, not access keys on EC2
4. **SSL/TLS**: Use HTTPS (Let's Encrypt free)
5. **Regular Updates**: Keep OS and dependencies updated
6. **Backup**: Backup code and data regularly
7. **Monitoring**: Set up CloudWatch alarms

---

## 📦 Files to Delete/Prepare

### Files to Delete:
- ✅ `venv/` (virtual environment - recreate on EC2)
- ✅ `__pycache__/` folders (auto-generated)
- ✅ `test_repo-main/` (test files - not needed in production)
- ✅ Old CSV reports in `reports/` (or move to S3)
- ✅ `.pyc` files (compiled Python)

### Files to Create:
- ✅ `.gitignore`
- ✅ `.dockerignore` (optional)
- ✅ `Dockerfile` (optional but recommended)
- ✅ `start.sh` (startup script)
- ✅ `deploy.sh` (deployment script)
- ✅ `systemd` service file (optional)
- ✅ `nginx.conf` (if using reverse proxy)

---

## 🤔 Questions to Discuss

1. **Database**: Do you need user accounts or scan history tracking?
   - **Yes** → DynamoDB recommended
   - **No** → Skip database for now

2. **Storage**: Do you want to store scan reports persistently?
   - **Yes** → Use S3
   - **No** → Keep local only (current)

3. **Domain**: Do you have a domain name?
   - **Yes** → Set up SSL/TLS
   - **No** → Use EC2 public IP (or get domain later)

4. **Scaling**: Expected traffic?
   - **Low** (< 100 users/day) → Single EC2 is enough
   - **High** (> 100 users/day) → Consider load balancer + multiple EC2

5. **Budget**: What's your monthly budget?
   - **Minimal** ($20/month) → EC2 only
   - **Standard** ($30-50/month) → EC2 + S3 + optional DynamoDB

---

## ✅ Next Steps

1. **Review this plan** and decide on:
   - Database: DynamoDB or skip?
   - Storage: S3 or local only?
   - Domain: Use domain or IP?

2. **Clean up files** (I'll help with this)

3. **Create deployment scripts** (I'll create these)

4. **Deploy to AWS** (Step-by-step guide will be provided)

---

**Ready to proceed? Let me know your decisions on the questions above!**

