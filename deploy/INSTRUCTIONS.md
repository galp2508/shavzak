# 🚀 Shavzak Deployment Instructions

## 🌍 1. Server Setup (DigitalOcean Droplet)

**IP:** `159.89.20.150`

### Step 1: Connect to your server
Open a terminal (PowerShell or CMD) and run:
```bash
ssh root@159.89.20.150
```

### Step 2: Install System Dependencies
Run the following commands on the server:
```bash
# Update system
apt update && apt upgrade -y

# Install Python, Node.js, Nginx, and Git
apt install -y python3-pip python3-venv nginx git curl

# Install Node.js (Latest LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

---

## 📂 2. Project Setup

### Step 1: Clone the Repository
```bash
mkdir -p /var/www
cd /var/www
git clone https://github.com/galp2508/shavzak.git
cd shavzak
```

---

## 🐍 3. Backend Setup (Flask)

### Step 1: Set up Python Environment
```bash
cd /var/www/shavzak/back
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure Systemd Service
This keeps your backend running in the background.

```bash
# Copy the service file I created for you
cp /var/www/shavzak/deploy/shavzak-backend.service /etc/systemd/system/

# Start and enable the service
systemctl start shavzak-backend
systemctl enable shavzak-backend
```

### Step 3: Verify Backend
Check if it's running:
```bash
systemctl status shavzak-backend
```

---

## ⚛️ 4. Frontend Setup (React)

### Step 1: Build the Project
```bash
cd /var/www/shavzak/front
npm install
npm run build
```
This will create a `dist` folder with your static files.

### Step 2: Configure Nginx
This serves your React app and connects it to the backend.

```bash
# Copy the nginx config I created for you
cp /var/www/shavzak/deploy/nginx_shavzak.conf /etc/nginx/sites-available/shavzak

# Enable the site
ln -s /etc/nginx/sites-available/shavzak /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Remove default site

# Test and restart Nginx
nginx -t
systemctl restart nginx
```

🎉 **Your site should now be live at http://159.89.20.150**

---

## 📱 5. iOS App Setup (Capacitor)

I have initialized **Capacitor** in the project. This allows you to convert your React site into a native iOS app.

### ⚠️ Requirement: Mac with Xcode
To build the final iOS app (`.ipa` file) or run the simulator, **you must use a Mac**.

### Instructions (On a Mac):

1. **Clone the repo on your Mac.**
2. **Install dependencies:**
   ```bash
   cd front
   npm install
   ```
3. **Build the web assets:**
   ```bash
   npm run build
   ```
4. **Add iOS platform:**
   ```bash
   npx cap add ios
   ```
5. **Open in Xcode:**
   ```bash
   npx cap open ios
   ```
6. **In Xcode:**
   - Select your Team (you need an Apple Developer Account).
   - Press "Play" to run on a Simulator or connected iPhone.
   - To publish: Product -> Archive.

### Alternative (If you don't have a Mac):
You can use **Ionic Appflow** (paid service) to build the iOS app in the cloud, or simply use the website as a **PWA** (Progressive Web App) by adding it to the Home Screen on an iPhone.
