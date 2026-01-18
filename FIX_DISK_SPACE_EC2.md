# 🔧 Fix: EC2 Disk Space Issue

## Problem
EC2 instance ran out of disk space while installing dependencies, especially NVIDIA CUDA packages (~700MB).

## Solution 1: Check and Free Up Space (Run on EC2)

```bash
# Check disk space
df -h

# Check what's using space
du -sh /home/ubuntu/* | sort -h

# Clean apt cache (can free 100-500MB)
sudo apt-get clean
sudo apt-get autoremove -y

# Clean pip cache (can free 200-500MB)
pip cache purge

# Clean temporary files
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Check space again
df -h
```

## Solution 2: Remove sentence-transformers (If Not Using Embeddings)

The `sentence-transformers` package downloads large CUDA packages (700MB+) but is optional. If you're using regex-based filtering (default), you can skip it.

**On EC2:**

```bash
cd ~/devgaurd

# Edit requirements.txt to comment out sentence-transformers
nano requirements.txt
```

**Comment out this line:**
```bash
# sentence-transformers>=2.2.0
```

**Save and continue installation:**
```bash
pip install -r requirements.txt
```

The app will work fine without it - it will use regex-based filtering instead of embeddings.

## Solution 3: Install Only Essential Dependencies

**Create minimal requirements file on EC2:**

```bash
cd ~/devgaurd

cat > requirements_minimal.txt << 'EOF'
streamlit>=1.28.0
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.10
langchain-google-genai>=1.0.0
google-genai>=0.2.0
pandas>=2.0.0
chardet>=5.0.0
boto3>=1.28.0
python-dotenv>=1.0.0
EOF

pip install -r requirements_minimal.txt
```

This skips:
- `GitPython` (not needed for file uploads)
- `sentence-transformers` (optional embeddings)

## Solution 4: Increase EC2 Storage (AWS Console)

1. **Stop EC2 instance** (not terminate!)
2. **Go to EC2 → Volumes**
3. **Select the volume attached to your instance**
4. **Actions → Modify Volume**
5. **Increase size** (e.g., 20GB → 30GB)
6. **Start instance**
7. **Extend filesystem on EC2:**
   ```bash
   sudo growpart /dev/nvme0n1 1
   sudo resize2fs /dev/nvme0n1p1
   df -h  # Verify
   ```

## Solution 5: Quick Fix - Install Without Cache

```bash
cd ~/devgaurd
source venv/bin/activate

# Clean pip cache first
pip cache purge

# Install without cache (saves temporary space)
pip install --no-cache-dir -r requirements.txt
```

## Recommended: Solution 2 + Clean Up

**On EC2, run these commands:**

```bash
cd ~/devgaurd

# 1. Clean up space
sudo apt-get clean
pip cache purge

# 2. Remove sentence-transformers from requirements (it's optional)
sed -i 's/^sentence-transformers/# sentence-transformers/' requirements.txt

# 3. Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Verify streamlit is installed
streamlit --version

# 5. Start application
./start.sh
```

The app will work perfectly fine without `sentence-transformers` - it uses regex-based code chunk filtering which is already implemented.

