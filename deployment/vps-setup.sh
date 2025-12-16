#!/bin/bash
# Amarktai Network - VPS Setup Script
# For Ubuntu 24.04 (Webdock VPS)

set -e  # Exit on error

echo "🚀 Starting Amarktai Network VPS Setup..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running with root privileges${NC}"

# 1. Update System
echo ""
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# 2. Install Required Packages
echo ""
echo "📦 Installing required packages..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nodejs \
    npm \
    nginx \
    mongodb \
    git \
    curl \
    wget \
    supervisor

# 3. Install Yarn
echo ""
echo "📦 Installing Yarn..."
npm install -g yarn

# 4. Start and Enable MongoDB
echo ""
echo "🗄️ Starting MongoDB..."
systemctl start mongodb
systemctl enable mongodb
echo -e "${GREEN}✅ MongoDB started${NC}"

# 5. Create Application Directory
echo ""
echo "📁 Creating application directory..."
mkdir -p /var/amarktai
cd /var/amarktai

# 6. Clone Repository (YOU NEED TO REPLACE WITH YOUR REPO URL)
echo ""
echo "📥 Cloning repository..."
echo -e "${YELLOW}⚠️ Manual step: You need to clone your repository here${NC}"
echo "Example: git clone YOUR_REPO_URL /var/amarktai"
read -p "Press Enter after you've cloned the repository..."

# 7. Backend Setup
echo ""
echo "🐍 Setting up Python backend..."
cd /var/amarktai/backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy env file
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}⚠️ Creating .env file from example${NC}"
    cp .env.example .env
    echo -e "${RED}❌ CRITICAL: Edit /var/amarktai/backend/.env with your API keys!${NC}"
    read -p "Press Enter after you've edited the .env file..."
fi

echo -e "${GREEN}✅ Backend setup complete${NC}"

# 8. Frontend Setup
echo ""
echo "⚛️ Setting up React frontend..."
cd /var/amarktai/frontend

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️ Update REACT_APP_BACKEND_URL in /var/amarktai/frontend/.env${NC}"
fi

# Install dependencies and build
yarn install
yarn build

echo -e "${GREEN}✅ Frontend build complete${NC}"

# 9. Setup Systemd Service
echo ""
echo "🔧 Setting up systemd service..."
cp /var/amarktai/deployment/amarktai-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable amarktai-api
systemctl start amarktai-api
echo -e "${GREEN}✅ API service started${NC}"

# 10. Setup Nginx
echo ""
echo "🌐 Setting up Nginx..."
cp /var/amarktai/deployment/nginx-amarktai.conf /etc/nginx/sites-available/amarktai

# Update server_name (replace with actual domain/IP)
echo -e "${YELLOW}⚠️ Update server_name in /etc/nginx/sites-available/amarktai${NC}"
read -p "Press Enter after editing the nginx config..."

# Enable site
ln -sf /etc/nginx/sites-available/amarktai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test nginx config
nginx -t
systemctl reload nginx
echo -e "${GREEN}✅ Nginx configured${NC}"

# 11. Set Permissions
echo ""
echo "🔐 Setting permissions..."
chown -R www-data:www-data /var/amarktai
chmod -R 755 /var/amarktai

# 12. Setup Firewall (UFW)
echo ""
echo "🔥 Configuring firewall..."
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw --force enable
echo -e "${GREEN}✅ Firewall configured${NC}"

# 13. Final Status Check
echo ""
echo "📊 Checking service status..."
echo ""
systemctl status amarktai-api --no-pager
echo ""
systemctl status mongodb --no-pager
echo ""
systemctl status nginx --no-pager

echo ""
echo -e "${GREEN}🎉 Amarktai Network VPS Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit /var/amarktai/backend/.env with your API keys"
echo "2. Edit /etc/nginx/sites-available/amarktai with your domain/IP"
echo "3. Restart services:"
echo "   sudo systemctl restart amarktai-api"
echo "   sudo systemctl reload nginx"
echo "4. Optional: Setup SSL with certbot"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d yourdomain.com"
echo ""
echo "Access your app at: http://YOUR_SERVER_IP"
