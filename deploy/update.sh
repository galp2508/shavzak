#!/bin/bash

# Navigate to project directory
cd /root/shavzak

# Get latest code
echo "📥 Pulling latest code..."
git pull

# Update Backend
echo "🐍 Updating Backend..."
source venv/bin/activate
pip install -r back/requirements.txt

# Update Frontend
echo "⚛️  Updating Frontend..."
cd front
npm install
npm run build
cd ..

# Restart Services
echo "🔄 Restarting Server..."
systemctl restart shavzak
systemctl restart nginx

echo "✅ Update Complete!"
