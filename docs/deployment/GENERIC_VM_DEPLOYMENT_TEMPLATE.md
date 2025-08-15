# Generic VM Deployment Template

This template provides a complete CI/CD deployment architecture for any application to a VM using webhook-based automation. It includes automatic file preservation, GitHub Actions integration, and comprehensive monitoring.

## Table of Contents
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Detailed Setup](#detailed-setup)
- [Deployment Process](#deployment-process)
- [Running Scripts Manually](#running-scripts-manually)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Security](#security)
- [Maintenance](#maintenance)

## Quick Start

### 1. Initial VM Setup (as root)
```bash
# First, install python3.13-venv if using Python 3.13+
apt update && apt install -y python3.13-venv

# Download and run the setup script
wget https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deployment/setup_vm.sh
chmod +x setup_vm.sh
./setup_vm.sh
```

### 2. Configure GitHub Secrets
Use the GitHub CLI with your PAT to set secrets:
```bash
# Export your GitHub PAT from .env
export GITHUB_TOKEN=$(grep '^GITHUB_PAT=' /workspace/.env | cut -d'=' -f2)

# Set the required secrets
gh secret set YOUR_APP_VM_DEPLOY_TOKEN --body "$(cat /root/deployment-service-YOUR_APP/.deploy_token)"
gh secret set YOUR_APP_VM_DEPLOY_WEBHOOK_URL --body "http://YOUR_VM_IP/deploy-YOUR_APP"
gh secret set YOUR_APP_VM_HEALTH_CHECK_URL --body "http://YOUR_VM_IP/health-YOUR_APP"
```

### 3. Deploy Credentials and Environment
```bash
# Copy your Firebase service account key to the VM
scp ai-tracker-*.json root@YOUR_VM_IP:/root/YOUR_APP/

# Copy your .env file to the VM
scp .env root@YOUR_VM_IP:/root/YOUR_APP/
```

### 4. Deploy Application
Push to main branch or manually trigger the GitHub Action.

### 5. Verify Deployment
```bash
# On the VM
cd /root/YOUR_APP

# Check that protected files exist
ls -la .env ai-tracker-*.json

# Test a script
source venv/bin/activate
python src/scripts/test_script.py
```

## Architecture Overview

The VM runs **TWO separate applications**:

### 1. Main Application (`/root/YOUR_APP/`)
- **Purpose**: Your application code and scripts
- **Updates**: AUTOMATICALLY replaced on every GitHub push
- **Protected files**: .env, Firebase credentials, and custom files are preserved
- **Virtual env**: Preserved between deployments

### 2. Deployment Service (`/root/deployment-service-YOUR_APP/`)
- **Purpose**: Flask webhook service that handles deployments
- **Updates**: NEVER updated by GitHub - this is permanent infrastructure
- **Changes**: Must be updated manually on the VM
- **Includes**: Deployment tokens, GitHub PAT, deployment logic
- **File Preservation**: Automatically preserves protected files during deployment

```
VM Structure:
/root/
├── deployment-service-YOUR_APP/           # PERMANENT - Never updated by GitHub
│   ├── vm_deploy_service.py              # Contains file preservation logic
│   ├── start_deploy_service.sh
│   ├── .deploy_token
│   ├── .github_token
│   └── logs/
├── YOUR_APP/                             # REPLACED - Updated on every push
│   ├── src/
│   ├── deployment/
│   ├── logs/                            # Preserved
│   ├── venv/                           # Preserved
│   ├── .env                            # Preserved (CRITICAL)
│   ├── ai-tracker-*.json               # Preserved (Firebase key)
│   └── [any custom files]              # Add to protected_files list
└── YOUR_APP_backups/                   # Auto-created during deployments
```

## Configuration

### Application Configuration
```bash
# Example for PH App
APP_NAME="ph_app"
APP_SLUG="ph"
SERVICE_PORT="8081"
VM_IP="YOUR_VM_IP"
GITHUB_REPO="YOUR_USER/YOUR_REPO"

# Example for Firestore Management
APP_NAME="firestore_management"
APP_SLUG="firestore-management"
SERVICE_PORT="8082"
VM_IP="YOUR_VM_IP"
GITHUB_REPO="YOUR_USER/YOUR_REPO"
```

### Port Assignment Strategy
- Base deployment services start at **8081**
- Each app gets a unique port:
  - PH App: 8081
  - Firestore Management: 8082
  - Reddit App: 8083
  - YouTube App: 8084
  - etc.
- Port Range: 8081-8099 (supports up to 19 applications)

### Protected Files
These files are automatically preserved during deployments:

#### Default Protected Files:
- `.env` - Environment variables with API keys (CRITICAL)
- `ai-tracker-*.json` - Firebase service account key
- `.deploy_token` - Deployment authentication token
- `.github_token` - GitHub PAT for artifact downloads

#### How File Protection Works:
1. Before deployment, the service saves protected files to memory
2. The app directory is completely replaced with new code
3. The tar archive is extracted (which may contain outdated versions)
4. Protected files are restored AFTER extraction, overwriting any old versions
5. This ensures secrets are never lost during deployment

**CRITICAL**: The restoration must happen AFTER tar extraction, not before!

#### Adding Custom Protected Files:
Edit the deployment service on the VM:
```python
# In /root/deployment-service-YOUR_APP/vm_deploy_service.py
protected_files = ['.env', 'ai-tracker-*.json', '.deploy_token', '.github_token', 'your_custom_file.txt']
```

#### Common Issue: Files Not Being Preserved
If protected files are being lost during deployment, check the order of operations:

**WRONG** (files get overwritten by tar extraction):
```python
# Restore protected files
for file, content in saved_files.items():
    with open(os.path.join(APP_DIR, file), 'wb') as f:
        f.write(content)

# Extract application (THIS OVERWRITES THE RESTORED FILES!)
subprocess.run(['tar', '-xzf', tar_path, '-C', APP_DIR])
```

**CORRECT** (files restored after extraction):
```python
# Extract application FIRST
subprocess.run(['tar', '-xzf', tar_path, '-C', APP_DIR])

# THEN restore protected files (overwrites any old versions from tar)
for file, content in saved_files.items():
    with open(os.path.join(APP_DIR, file), 'wb') as f:
        f.write(content)
```

## Detailed Setup

### Files in this Directory

#### Essential Deployment Files

**VM Setup:**
- `setup_vm.sh` - Main VM setup script
- `vm_deploy_service.py` - Deployment service with file preservation
- `start_deploy_service.sh` - Service startup script

**Cron Wrappers:**
- Create wrapper scripts for each scheduled task
- Example: `your_script_wrapper.sh`
```bash
#!/bin/bash
cd /root/YOUR_APP
source venv/bin/activate
python src/scripts/your_script.py
```

**Configuration:**
- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- Cron schedule configuration

## Deployment Process

### What Gets Updated During Deployment

#### Automatically Updated (via GitHub push):
- ✅ All Python scripts in `/src/`
- ✅ All deployment scripts in `/deployment/`
- ✅ Configuration files (except .env)
- ✅ Documentation files
- ✅ Requirements.txt
- ✅ Any new files added to the repository

#### Never Updated (Manual VM access required):
- ❌ Deployment service (`/root/deployment-service-firestore-management/`)
- ❌ Crontab entries
- ❌ Systemd service files
- ❌ Nginx configuration
- ❌ Protected files (.env, Firebase credentials)
- ❌ Python virtual environment packages

### Example Script Organization

#### Data Collection Scripts
- Scheduled data fetching from APIs
- Real-time monitoring and updates
- Batch processing jobs

#### Analytics & Aggregation
- Daily/weekly/monthly aggregations
- Metrics calculation and reporting
- Cross-platform data synthesis

#### Maintenance Scripts
- Log rotation and cleanup
- Database maintenance
- Old data archival

## Running Scripts Manually

### Option 1: Use Wrapper Scripts (Recommended)
All scripts should have wrapper scripts that handle virtual environment activation:

```bash
# Connect to VM
ssh -i /workspace/droplet1 root@YOUR_VM_IP

# Run your scripts via wrappers:
/root/YOUR_APP/deployment/your_script_wrapper.sh

# Or create a simple wrapper:
cat > /root/run_script.sh << 'EOF'
#!/bin/bash
cd /root/YOUR_APP
source venv/bin/activate
python src/scripts/$1
EOF
chmod +x /root/run_script.sh

# Then use it:
./run_script.sh your_script.py
```

### Option 2: Run Python Scripts Directly
For testing with specific parameters:

```bash
# Connect to VM
ssh -i /workspace/droplet1 root@YOUR_VM_IP

# Set up environment
cd /root/YOUR_APP
source venv/bin/activate
export PYTHONPATH="/root/YOUR_APP:/root/YOUR_APP/src"

# Run any script
python src/scripts/your_script.py
python src/scripts/another_script.py --date 2025-08-11
```

### Creating Wrapper Scripts
```bash
# Template for wrapper scripts
cat > /root/YOUR_APP/deployment/wrapper_template.sh << 'EOF'
#!/bin/bash
# Wrapper script for YOUR_SCRIPT

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
cd /root/YOUR_APP

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Create log directory if it doesn't exist
mkdir -p logs

# Run the script with logging
python src/scripts/YOUR_SCRIPT.py 2>&1 | tee -a logs/YOUR_SCRIPT.log
EOF

chmod +x /root/YOUR_APP/deployment/wrapper_template.sh
```

## Monitoring & Troubleshooting

### Check Service Status
```bash
systemctl status YOUR_APP-deploy
```

### View Logs
```bash
# Deployment service logs
tail -f /root/deployment-service-YOUR_APP/logs/deployment.log

# Application logs
tail -f /root/YOUR_APP/logs/*.log

# Cron logs
tail -f /root/YOUR_APP/logs/cron.log

# Check deployment history
grep "Deployment" /root/deployment-service-YOUR_APP/logs/deployment.log
```

### Common Issues

#### Service Won't Start
```bash
journalctl -u firestore-management-deploy -n 50
```

#### Scripts Can't Find .env or Firebase Key
Ensure protected files exist:
```bash
ls -la /root/YOUR_APP/.env
ls -la /root/YOUR_APP/ai-tracker-*.json

# If missing, restore from backup:
cp /root/YOUR_APP_backups/backup_*/.env /root/YOUR_APP/
cp /root/YOUR_APP_backups/backup_*/ai-tracker-*.json /root/YOUR_APP/

# If files keep disappearing after deployment, check the deployment service:
ssh root@YOUR_VM_IP
grep -A10 -B10 "Extract application" /root/deployment-service-YOUR_APP/vm_deploy_service.py

# Make sure file restoration happens AFTER tar extraction!
# Fix if needed and restart service:
systemctl restart YOUR_APP-deploy
```

#### Cron Jobs Not Running
```bash
# Check if cron jobs are installed
crontab -l | grep YOUR_APP

# Check cron service
systemctl status cron

# Test wrapper script manually
/root/YOUR_APP/deployment/your_wrapper.sh
```

#### Deployment Fails
```bash
# Check deployment logs
tail -50 /root/deployment-service-YOUR_APP/logs/deployment.log

# Common issues:
# 1. Wrong artifact name - check GitHub Actions artifact name
# 2. Missing GitHub token - verify .github_token exists
# 3. Protected files not preserved - check vm_deploy_service.py

# Manually trigger deployment:
curl -X POST http://localhost:SERVICE_PORT/deploy \
  -H "Authorization: Bearer $(cat /root/deployment-service-YOUR_APP/.deploy_token)" \
  -H "Content-Type: application/json" \
  -d '{"version": "FULL_SHA", "repository": "USER/REPO", "workflow_run_id": "RUN_ID"}'
```

## Security

### Protected Files
The deployment service preserves these files across deployments:
- `ai-tracker-466821-bc88c21c2489.json` (Firebase credentials)
- `.env` (Environment variables)
- `logs/*` (Log files)

### Sensitive Files
Keep these tokens secure:
- Deployment token: `/root/deployment-service-YOUR_APP/.deploy_token`
- GitHub PAT: `/root/deployment-service-YOUR_APP/.github_token`

**Never commit these files to Git!**

### Firewall
Ensure only necessary ports are open:
- Port 80/443 for nginx (public)
- Port SERVICE_PORT for deployment service (localhost only)
- SSH port 22 (restrict to your IP if possible)

## Maintenance

### Update Scripts Without Full Deployment
```bash
cd /root/YOUR_APP
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Note: This bypasses file protection!
# Consider using the deployment service instead
```

### Backup Before Major Changes
```bash
cp -r /root/YOUR_APP /root/YOUR_APP_backup_$(date +%Y%m%d)

# Or backup specific files:
cp /root/YOUR_APP/.env /root/YOUR_APP/.env.backup
cp /root/YOUR_APP/ai-tracker-*.json /root/YOUR_APP/firebase.backup
```

### Clean Old Logs
```bash
# Clean application logs older than 30 days
find /root/YOUR_APP/logs -name "*.log" -mtime +30 -delete

# Clean deployment logs older than 30 days
find /root/deployment-service-YOUR_APP/logs -name "*.log" -mtime +30 -delete

# Clean old backups (keep last 5)
cd /root/YOUR_APP_backups && ls -t | tail -n +6 | xargs rm -rf
```

### Update Deployment Service (Manual Only)
If you need to update the deployment service itself:
```bash
cd /root/deployment-service-YOUR_APP

# Backup current service
cp vm_deploy_service.py vm_deploy_service.py.bak

# Edit vm_deploy_service.py as needed
# Common edits:
# - Add files to protected_files list
# - Change deployment logic
# - Update error handling

systemctl restart YOUR_APP-deploy
```

### Check Disk Space
```bash
df -h
du -sh /root/YOUR_APP*
du -sh /root/deployment-service-YOUR_APP

# Find large files
find /root/YOUR_APP -type f -size +100M -ls
```

## Testing

### Test Deployment Endpoint
```bash
# Get deployment token
DEPLOY_TOKEN=$(cat /root/deployment-service-YOUR_APP/.deploy_token)

# Get latest commit SHA
LATEST_SHA=$(cd /root/YOUR_APP && git log -1 --format=%H)

# Test deployment endpoint
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEPLOY_TOKEN" \
  -d '{
    "version": "'$LATEST_SHA'",
    "repository": "YOUR_USER/YOUR_REPO",
    "workflow_run_id": "12345"
  }' \
  http://YOUR_VM_IP/deploy-YOUR_APP
```

### Health Check
```bash
# Through nginx (public)
curl http://YOUR_VM_IP/health-YOUR_APP

# Direct to service (from VM)
curl http://localhost:SERVICE_PORT/health

# Expected response:
# {"status": "healthy", "app_name": "YOUR_APP", ...}
```

## Summary

This generic VM deployment template provides:

1. **Automated CI/CD**: Push to GitHub → Automatic deployment via webhooks
2. **Protected Files**: Critical files (.env, credentials) preserved across deployments
3. **Multi-App Support**: Run multiple apps on one VM with different ports
4. **Comprehensive Monitoring**: Deployment logs, application logs, and health checks
5. **Easy Script Execution**: Wrapper scripts handle environment setup
6. **Secure Architecture**: Deployment service isolated from application code

## Key Implementation Steps

1. **Initial Setup**:
   - Install python3.13-venv if needed
   - Run setup script to create deployment service
   - Configure GitHub secrets with PAT

2. **File Protection**:
   - Add `.env` to protected_files list in deployment service
   - Deploy credentials before first deployment
   - Files automatically preserved on updates

3. **Deployment Flow**:
   - GitHub Actions builds and creates artifact
   - Webhook triggers VM deployment service
   - Service downloads artifact using GitHub PAT
   - Protected files saved before update
   - Application code replaced
   - Protected files restored
   - Virtual environment updated if needed

4. **Monitoring**:
   - Check deployment logs for issues
   - Monitor application logs
   - Use health endpoint for status
   - Track deployment history

This template has been proven with multiple production applications and provides a robust, secure deployment pipeline.