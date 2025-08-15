# DataForSEO App Deployment Guide

This guide explains how to deploy the DataForSEO app to a VM with automated CI/CD.

## Overview

- **Repository**: https://github.com/canaanhowell/dataforseo_app
- **VM IP**: 134.209.206.143
- **Deployment Port**: 8085
- **Deployment URLs**:
  - Webhook: http://134.209.206.143/deploy-dataforseo
  - Health: http://134.209.206.143/health-dataforseo

## Initial VM Setup

1. **Connect to the VM**:
   ```bash
   ssh root@134.209.206.143
   ```

2. **Download and run setup script**:
   ```bash
   wget https://raw.githubusercontent.com/canaanhowell/dataforseo_app/main/deployment/setup_vm.sh
   chmod +x setup_vm.sh
   ./setup_vm.sh
   ```

3. **Note the deployment token** displayed at the end of setup.

4. **Add GitHub PAT to the deployment service**:
   ```bash
   echo "YOUR_GITHUB_PAT" > /root/deployment-service-dataforseo/.github_token
   chmod 600 /root/deployment-service-dataforseo/.github_token
   ```

## Set GitHub Secrets

From your local machine:

```bash
cd /workspace/dataforseo_app
export GITHUB_TOKEN="YOUR_GITHUB_PAT"
python deployment/set_github_secrets.py
```

Enter the deployment token when prompted.

## Deploy Credentials

1. **Copy .env file**:
   ```bash
   scp /workspace/.env root@134.209.206.143:/root/dataforseo_app/
   ```

2. **Copy Firebase service account key**:
   ```bash
   scp /workspace/ai-tracker-*.json root@134.209.206.143:/root/dataforseo_app/
   ```

3. **Copy DataForSEO credentials** (if not in .env):
   ```bash
   ssh root@134.209.206.143
   cd /root/dataforseo_app
   echo "DATAFORSEO_LOGIN=your_login" >> .env
   echo "DATAFORSEO_PASSWORD=your_password" >> .env
   ```

## Trigger Deployment

Deployment happens automatically when you push to the main branch. You can also trigger manually:

1. Go to https://github.com/canaanhowell/dataforseo_app/actions
2. Click on "Deploy to VM" workflow
3. Click "Run workflow"

## Running Scripts on VM

### Using Wrapper Scripts
```bash
ssh root@134.209.206.143
/root/dataforseo_app/deployment/process_keywords_wrapper.sh
/root/dataforseo_app/deployment/update_firestore_wrapper.sh
```

### Direct Python Execution
```bash
ssh root@134.209.206.143
cd /root/dataforseo_app
source venv/bin/activate
python src/scripts/process_master_keywords.py
```

## Setting Up Cron Jobs

Add to crontab for scheduled execution:

```bash
crontab -e

# Process keywords daily at 2 AM
0 2 * * * /root/dataforseo_app/deployment/process_keywords_wrapper.sh

# Update Firestore weekly on Sundays at 3 AM
0 3 * * 0 /root/dataforseo_app/deployment/update_firestore_wrapper.sh
```

## Monitoring

### Check Deployment Service
```bash
systemctl status dataforseo-deploy
```

### View Deployment Logs
```bash
tail -f /root/deployment-service-dataforseo/logs/deployment.log
```

### View Application Logs
```bash
tail -f /root/dataforseo_app/logs/*.log
```

### Check Health
```bash
curl http://localhost:8085/health
```

## Troubleshooting

### Service Won't Start
```bash
journalctl -u dataforseo-deploy -n 50
```

### Missing .env or Firebase Key
```bash
ls -la /root/dataforseo_app/.env
ls -la /root/dataforseo_app/ai-tracker-*.json
```

### Deployment Fails
Check the deployment logs and ensure GitHub secrets are set correctly.

## Protected Files

These files are preserved during deployments:
- `.env`
- `ai-tracker-*.json`
- `logs/*`
- `venv/*`
- `data/firestore_search_volumes.json`

## Security Notes

- The deployment token is stored in `/root/deployment-service-dataforseo/.deploy_token`
- GitHub PAT is stored in `/root/deployment-service-dataforseo/.github_token`
- Never commit these tokens to Git!

## Manual Deployment

If needed, you can manually update without the deployment service:

```bash
cd /root/dataforseo_app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

Note: This bypasses file protection, so be careful not to overwrite .env or credentials.