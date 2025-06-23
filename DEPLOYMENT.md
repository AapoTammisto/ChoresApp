# Raspberry Pi Deployment Guide

## Quick Setup (Recommended)

1. **Download the project to your Raspberry Pi**
   ```bash
   git clone <your-repo-url>
   cd ChoresApp
   ```

2. **Run the automated setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the service**
   ```bash
   sudo systemctl start chores-app
   ```

4. **Access the app**
   - Find your Pi's IP: `hostname -I`
   - Open browser: `http://[PI_IP]:8080`
   - Login: `parent` / `parent123`

## Manual Setup

### Step 1: Install Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### Step 2: Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Initialize Database
```bash
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 4: Configure Systemd Service
```bash
sudo cp chores-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chores-app
sudo systemctl start chores-app
```

## Network Access

### Find Your Pi's IP Address
```bash
hostname -I
```

### Access from Other Devices
- **Local Network**: `http://[PI_IP]:8080`
- **Mobile Devices**: Same URL, works great on tablets and phones
- **Computers**: Any device on your WiFi network

## Management Commands

### Service Control
```bash
# Start the app
sudo systemctl start chores-app

# Stop the app
sudo systemctl stop chores-app

# Restart the app
sudo systemctl restart chores-app

# Check status
sudo systemctl status chores-app

# View logs
sudo journalctl -u chores-app -f
```

### Database Backup
```bash
# Create backup
cp chores.db chores_backup_$(date +%Y%m%d).db

# Restore from backup
cp chores_backup_20241201.db chores.db
```

## Security Recommendations

1. **Change default password** after first login
2. **Use strong passwords** for child accounts
3. **Keep on local network** only
4. **Regular backups** of the database file
5. **Update secret key** in app.py for production

## Troubleshooting

### App Won't Start
```bash
# Check service status
sudo systemctl status chores-app

# View detailed logs
sudo journalctl -u chores-app -n 50

# Check if port is in use
sudo lsof -i :8080
```

### Can't Access from Other Devices
```bash
# Check firewall
sudo ufw status

# Allow port 8080 (if using ufw)
sudo ufw allow 8080

# Check Pi's IP address
hostname -I
```

### Database Issues
```bash
# Reset database (WARNING: loses all data)
rm chores.db
sudo systemctl restart chores-app
```

## Performance Tips

1. **Use SSD** instead of SD card for better performance
2. **Close other apps** to free up memory
3. **Regular reboots** to keep system fresh
4. **Monitor temperature** with `vcgencmd measure_temp`

## Mobile Optimization

The app is designed to work perfectly on:
- ✅ Tablets (iPad, Android tablets)
- ✅ Phones (iPhone, Android phones)
- ✅ Touch screens
- ✅ Small screens

Features optimized for mobile:
- Large touch-friendly buttons
- Responsive design
- Simple navigation
- Easy-to-read text
- Swipe-friendly interface

## Support

If you encounter issues:
1. Check the logs: `sudo journalctl -u chores-app -f`
2. Verify Python version: `python3 --version`
3. Check dependencies: `pip3 list`
4. Restart the service: `sudo systemctl restart chores-app`

---

**Your family chores app is now ready! 🎉** 