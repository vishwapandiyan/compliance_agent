# 🔧 Quick Fix for EC2 - Update start.sh

## Option 1: Pull Latest Changes from GitHub (Recommended)

On your EC2 instance, run:

```bash
cd ~/devguard
git pull origin main
```

This will update `start.sh` to the new version that doesn't require GEMINI_API_KEY.

---

## Option 2: Manual Fix (If Git Pull Fails)

Edit `start.sh` directly on EC2:

```bash
cd ~/devguard
nano start.sh
```

**Find this section (around line 32-36):**
```bash
# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ Error: GEMINI_API_KEY environment variable is not set${NC}"
    echo -e "${YELLOW}   Please set it in .env file or export it as an environment variable${NC}"
    exit 1
fi
```

**Replace it with:**
```bash
# Check if GEMINI_API_KEY is set (optional - can be provided via frontend UI)
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}ℹ️  GEMINI_API_KEY not set in .env - users can enter it via the web UI${NC}"
    echo -e "${YELLOW}   The application will prompt users to enter their API key in the Streamlit interface${NC}"
fi
```

**Save and exit:** Ctrl+X, Y, Enter

---

## Option 3: Quick One-Liner Fix

Run this command on EC2 to fix it automatically:

```bash
cd ~/devguard && sed -i 's/exit 1/# Removed exit - API key optional/' start.sh && sed -i 's/❌ Error: GEMINI_API_KEY environment variable is not set/ℹ️  GEMINI_API_KEY not set in .env - users can enter it via the web UI/' start.sh && sed -i 's/Please set it in .env file or export it as an environment variable/The application will prompt users to enter their API key in the Streamlit interface/' start.sh && sed -i 's/${RED}/${YELLOW}/' start.sh
```

---

After fixing, run:
```bash
./start.sh
```

The application should now start successfully!

