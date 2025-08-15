#!/bin/bash
# VM Setup Script for DataForSEO App
# This script sets up the deployment environment on a fresh VM

set -e  # Exit on error

echo "🚀 Starting VM Setup for DataForSEO App..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
apt install -y python3.13-venv python3-pip nginx git curl

# Create app directory
echo "📁 Creating application directories..."
mkdir -p /root/dataforseo_app
mkdir -p /root/deployment-service-dataforseo
mkdir -p /root/dataforseo_app_backups

# Set up deployment service
echo "🔧 Setting up deployment service..."
cd /root/deployment-service-dataforseo

# Generate deployment token
echo "🔑 Generating deployment token..."
openssl rand -hex 32 > .deploy_token
chmod 600 .deploy_token

# Create GitHub token file (will be populated manually)
touch .github_token
chmod 600 .github_token

# Create deployment service Python script
cat > vm_deploy_service.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import json
import shutil
import glob
from flask import Flask, request, jsonify
from datetime import datetime
import requests
import logging
import tempfile

# Configuration
APP_NAME = "dataforseo_app"
APP_DIR = f"/root/{APP_NAME}"
BACKUP_DIR = f"/root/{APP_NAME}_backups"
SERVICE_PORT = 8085
GITHUB_API_URL = "https://api.github.com"
ARTIFACT_NAME = "dataforseo-deployment"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Protected files that should be preserved during deployment
PROTECTED_FILES = [
    '.env',
    'ai-tracker-*.json',
    '.deploy_token',
    '.github_token',
    'logs/*',
    'venv/*',
    'data/firestore_search_volumes.json'
]

def load_tokens():
    """Load deployment and GitHub tokens."""
    tokens = {}
    try:
        with open('.deploy_token', 'r') as f:
            tokens['deploy'] = f.read().strip()
    except FileNotFoundError:
        logger.error(".deploy_token not found")
        
    try:
        with open('.github_token', 'r') as f:
            tokens['github'] = f.read().strip()
    except FileNotFoundError:
        logger.error(".github_token not found")
        
    return tokens

def save_protected_files():
    """Save protected files before deployment."""
    saved_files = {}
    
    for pattern in PROTECTED_FILES:
        full_pattern = os.path.join(APP_DIR, pattern)
        
        # Handle glob patterns
        if '*' in pattern:
            files = glob.glob(full_pattern)
            for file_path in files:
                if os.path.exists(file_path):
                    rel_path = os.path.relpath(file_path, APP_DIR)
                    try:
                        with open(file_path, 'rb') as f:
                            saved_files[rel_path] = f.read()
                        logger.info(f"Saved protected file: {rel_path}")
                    except Exception as e:
                        logger.error(f"Failed to save {rel_path}: {e}")
        else:
            file_path = full_pattern
            if os.path.exists(file_path):
                rel_path = os.path.relpath(file_path, APP_DIR)
                try:
                    with open(file_path, 'rb') as f:
                        saved_files[rel_path] = f.read()
                    logger.info(f"Saved protected file: {rel_path}")
                except Exception as e:
                    logger.error(f"Failed to save {rel_path}: {e}")
    
    return saved_files

def restore_protected_files(saved_files):
    """Restore protected files after deployment."""
    for rel_path, content in saved_files.items():
        file_path = os.path.join(APP_DIR, rel_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"Restored protected file: {rel_path}")
        except Exception as e:
            logger.error(f"Failed to restore {rel_path}: {e}")

def download_artifact(repo, run_id, token):
    """Download deployment artifact from GitHub."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get artifacts for the workflow run
    artifacts_url = f"{GITHUB_API_URL}/repos/{repo}/actions/runs/{run_id}/artifacts"
    response = requests.get(artifacts_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get artifacts: {response.text}")
    
    artifacts = response.json()['artifacts']
    
    # Find our deployment artifact
    artifact = None
    for a in artifacts:
        if a['name'] == ARTIFACT_NAME:
            artifact = a
            break
    
    if not artifact:
        raise Exception(f"Artifact '{ARTIFACT_NAME}' not found")
    
    # Download the artifact
    download_url = f"{GITHUB_API_URL}/repos/{repo}/actions/artifacts/{artifact['id']}/zip"
    response = requests.get(download_url, headers=headers, stream=True)
    
    if response.status_code != 200:
        raise Exception(f"Failed to download artifact: {response.text}")
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    for chunk in response.iter_content(chunk_size=8192):
        temp_file.write(chunk)
    temp_file.close()
    
    logger.info(f"Downloaded artifact to {temp_file.name}")
    return temp_file.name

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'app_name': APP_NAME,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/deploy', methods=['POST'])
def deploy():
    """Handle deployment webhook."""
    tokens = load_tokens()
    
    # Verify authorization
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization'}), 401
    
    provided_token = auth_header.replace('Bearer ', '')
    if provided_token != tokens.get('deploy'):
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get deployment info
    data = request.json
    version = data.get('version', 'unknown')
    repository = data.get('repository')
    run_id = data.get('workflow_run_id')
    
    logger.info(f"Starting deployment - Version: {version}, Repo: {repository}, Run: {run_id}")
    
    try:
        # Create backup
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        if os.path.exists(APP_DIR):
            logger.info(f"Creating backup at {backup_path}")
            shutil.copytree(APP_DIR, backup_path, symlinks=True)
        
        # Save protected files
        saved_files = save_protected_files()
        
        # Download artifact
        logger.info("Downloading deployment artifact...")
        artifact_path = download_artifact(repository, run_id, tokens.get('github'))
        
        # Extract artifact (which contains the tar.gz)
        logger.info("Extracting artifact...")
        subprocess.run(['unzip', '-o', artifact_path, '-d', '/tmp'], check=True)
        tar_path = f"/tmp/{APP_NAME}.tar.gz"
        
        # Clean app directory (preserve venv and logs)
        logger.info("Cleaning application directory...")
        for item in os.listdir(APP_DIR):
            if item not in ['venv', 'logs']:
                item_path = os.path.join(APP_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        # Extract application
        logger.info("Extracting application...")
        subprocess.run(['tar', '-xzf', tar_path, '-C', APP_DIR], check=True)
        
        # CRITICAL: Restore protected files AFTER extraction
        restore_protected_files(saved_files)
        
        # Update virtual environment if needed
        logger.info("Updating virtual environment...")
        subprocess.run([
            f'{APP_DIR}/venv/bin/pip', 'install', '-r', 
            f'{APP_DIR}/requirements.txt'
        ], check=True)
        
        # Clean up
        os.remove(artifact_path)
        os.remove(tar_path)
        
        # Clean old backups (keep last 5)
        backups = sorted(os.listdir(BACKUP_DIR))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                shutil.rmtree(os.path.join(BACKUP_DIR, old_backup))
        
        logger.info(f"Deployment completed successfully - Version: {version}")
        
        return jsonify({
            'status': 'success',
            'version': version,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=SERVICE_PORT)
EOF

# Create startup script
cat > start_deploy_service.sh << 'EOF'
#!/bin/bash
cd /root/deployment-service-dataforseo
source /usr/bin/python3
python3 vm_deploy_service.py
EOF
chmod +x start_deploy_service.sh

# Create systemd service
cat > /etc/systemd/system/dataforseo-deploy.service << 'EOF'
[Unit]
Description=DataForSEO Deployment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/deployment-service-dataforseo
ExecStart=/root/deployment-service-dataforseo/start_deploy_service.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
echo "🌐 Configuring nginx..."
cat > /etc/nginx/sites-available/dataforseo-deploy << 'EOF'
server {
    listen 80;
    server_name _;

    location /deploy-dataforseo {
        proxy_pass http://localhost:8085/deploy;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health-dataforseo {
        proxy_pass http://localhost:8085/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dataforseo-deploy /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Enable and start deployment service
systemctl daemon-reload
systemctl enable dataforseo-deploy
systemctl start dataforseo-deploy

# Create initial app structure
echo "📁 Creating initial app structure..."
cd /root/dataforseo_app
python3 -m venv venv

# Create logs directory
mkdir -p logs

echo "✅ VM Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Add your GitHub PAT to /root/deployment-service-dataforseo/.github_token"
echo "2. Set up GitHub secrets using the deploy token from /root/deployment-service-dataforseo/.deploy_token"
echo "3. Deploy your application"
echo ""
echo "Deployment token:"
cat /root/deployment-service-dataforseo/.deploy_token