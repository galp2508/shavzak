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

# Run migrations
echo "🔧 Running database migrations..."
export SECRET_KEY='7f8a9d1c2b3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9'
export DEBUG=False
python back/migrate.py



# Update Frontend
echo "⚛️  Updating Frontend..."
cd front
npm install
npm run build
cd ..

# Restart Services
echo "🔄 Updating Systemd Services..."
cp deploy/shavzak.service /etc/systemd/system/shavzak.service
systemctl daemon-reload
systemctl restart shavzak
systemctl restart nginx

echo "✅ Update Complete!"
