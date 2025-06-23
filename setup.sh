#!/bin/bash

# Family Chores App Setup Script for Raspberry Pi
# This script will install and configure the app

echo "🏠 Family Chores App Setup"
echo "=========================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This script is designed for Raspberry Pi, but you can continue anyway."
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create database
echo "🗄️  Initializing database..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')"

# Set up systemd service
echo "🔧 Setting up systemd service..."
sudo cp chores-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chores-app

# Set permissions
echo "🔐 Setting file permissions..."
chmod +x app.py
chmod 644 *.py
chmod 644 templates/*
chmod 644 static/*

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Start the service: sudo systemctl start chores-app"
echo "2. Check status: sudo systemctl status chores-app"
echo "3. Find your Pi's IP: hostname -I"
echo "4. Access the app: http://[YOUR_PI_IP]:8080"
echo ""
echo "🔑 Default login:"
echo "   Username: parent"
echo "   Password: parent123"
echo ""
echo "📱 The app is mobile-friendly and works great on tablets and phones!"
echo ""
echo "🔄 To restart the app: sudo systemctl restart chores-app"
echo "📋 To view logs: sudo journalctl -u chores-app -f" 