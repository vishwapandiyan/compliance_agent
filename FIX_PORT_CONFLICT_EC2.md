# 🔧 Fix: Port 8501 Already in Use

## Problem
Port 8501 is already in use - this happens when:
1. Systemd service is already running
2. Another instance of the app is running
3. Previous instance didn't shut down properly

## Solution 1: Use Systemd Service (Recommended)

Since you already started the systemd service, just use it:

```bash
# Check if service is running
sudo systemctl status devguard

# View logs to see what's happening
sudo journalctl -u devguard -f

# The app should already be accessible at http://<YOUR_IP>:8501
```

**Don't run `./start.sh` manually if systemd service is running!**

---

## Solution 2: Stop Systemd and Run Manually

If you want to run manually instead:

```bash
# Stop the systemd service
sudo systemctl stop devguard

# Verify it's stopped
sudo systemctl status devguard

# Now kill any remaining processes on port 8501
sudo lsof -ti:8501 | xargs sudo kill -9 2>/dev/null || true

# Wait a moment
sleep 2

# Now run manually
./start.sh
```

---

## Solution 3: Check What's Using Port 8501

Find out what's using the port:

```bash
# Check what process is using port 8501
sudo lsof -i:8501

# Or
sudo netstat -tlnp | grep 8501

# Kill it manually if needed
sudo kill -9 <PID>
```

---

## Solution 4: Use Different Port (Temporary)

If you want to run both (not recommended):

```bash
# Edit .env to use different port
nano .env

# Add or change:
STREAMLIT_SERVER_PORT=8502

# Update security group to allow port 8502 if needed
# Then run:
./start.sh
```

---

## Recommended: Use Systemd Service

**For production, use systemd:**

```bash
# Check status
sudo systemctl status devguard

# If running, access at:
http://<YOUR_ELASTIC_IP>:8501

# If not running, start it:
sudo systemctl start devguard

# View logs:
sudo journalctl -u devguard -f

# Restart after pulling code changes:
cd ~/devgaurd
git pull origin main
sudo systemctl restart devguard
```

---

## Quick Fix Right Now

**To run manually (stopping systemd first):**

```bash
# Stop systemd
sudo systemctl stop devguard

# Kill any remaining processes
sudo pkill -f streamlit
sleep 2

# Run manually
cd ~/devgaurd
./start.sh
```

Or just access the app at `http://<YOUR_ELASTIC_IP>:8501` - it's already running via systemd!

