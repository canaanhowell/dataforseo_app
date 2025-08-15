#!/usr/bin/env python3
"""
Script to set GitHub secrets for DataForSEO app deployment
"""
import os
import subprocess
import sys

def set_github_secret(name, value):
    """Set a GitHub secret using gh CLI."""
    cmd = ['gh', 'secret', 'set', name, '--body', value]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Successfully set secret: {name}")
    else:
        print(f"❌ Failed to set secret {name}: {result.stderr}")
        sys.exit(1)

def main():
    # Check if GITHUB_TOKEN is set
    if not os.environ.get('GITHUB_TOKEN'):
        print("❌ GITHUB_TOKEN environment variable not set")
        print("Run: export GITHUB_TOKEN=your_github_pat")
        sys.exit(1)
    
    # VM Configuration
    VM_IP = "134.209.206.143"
    
    print("🔧 Setting GitHub secrets for DataForSEO app deployment...")
    
    # Prompt for deploy token
    deploy_token = input("Enter deployment token from VM (check /root/deployment-service-dataforseo/.deploy_token): ").strip()
    
    if not deploy_token:
        print("❌ Deployment token cannot be empty")
        sys.exit(1)
    
    # Set secrets
    secrets = {
        'DATAFORSEO_VM_DEPLOY_TOKEN': deploy_token,
        'DATAFORSEO_VM_DEPLOY_WEBHOOK_URL': f'http://{VM_IP}/deploy-dataforseo',
        'DATAFORSEO_VM_HEALTH_CHECK_URL': f'http://{VM_IP}/health-dataforseo'
    }
    
    for name, value in secrets.items():
        set_github_secret(name, value)
    
    print("\n✅ All secrets have been set successfully!")
    print("\nNext steps:")
    print("1. Copy your .env file to the VM: scp .env root@{VM_IP}:/root/dataforseo_app/")
    print("2. Copy Firebase key to the VM: scp ai-tracker-*.json root@{VM_IP}:/root/dataforseo_app/")
    print("3. Push code to trigger deployment or run GitHub Action manually")

if __name__ == '__main__':
    main()