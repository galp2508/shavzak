#!/bin/bash

# Update system
apt-get update
apt-get install -y python3-pip python3-venv nginx git curl

# Install Node.js (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Navigate to project directory (assuming we are in /root/shavzak)
cd /root/shavzak

# Setup Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r back/requirements.txt
pip install gunicorn

# Build Frontend
echo "Building Frontend..."
cd front
npm install
# Create production env for frontend
echo "VITE_API_URL=/api" > .env
# Add Ditto keys to frontend env (using placeholders or passed env vars if needed, 
# but for now we will assume the user might need to edit this or we use the ones from the repo if they were committed - which they are not)
# We need the Ditto keys here!
# I will add a prompt or just write the keys I know into the file.
echo "VITE_DITTO_APP_ID=093a3803-2017-4cdf-b08e-b7612c5acd52" >> .env
echo "VITE_DITTO_TOKEN=wA6ppHxJLvtlf9zS1wh8VFXULDKz4E77OOmWgbcNM3O2hIwLZOPsVqMvkrfM" >> .env

npm run build
cd ..

# Setup Systemd Service
cp deploy/shavzak.service /etc/systemd/system/
systemctl start shavzak
systemctl enable shavzak

# Setup Nginx
cp deploy/nginx_shavzak /etc/nginx/sites-available/shavzak
ln -s /etc/nginx/sites-available/shavzak /etc/nginx/sites-enabled
rm /etc/nginx/sites-enabled/default
systemctl restart nginx

# Allow traffic
ufw allow 'Nginx Full'

echo "✅ Deployment Complete! Server should be running."
