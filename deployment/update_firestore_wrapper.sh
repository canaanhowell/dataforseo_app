#!/bin/bash
# Wrapper script for updating Firestore with search volumes

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
cd /root/dataforseo_app

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Create log directory if it doesn't exist
mkdir -p logs

# Run the script with logging
echo "$(date) - Starting Firestore update..." >> logs/firestore_update.log
python src/scripts/update_firestore_search_volumes_fixed.py 2>&1 | tee -a logs/firestore_update.log
echo "$(date) - Firestore update completed" >> logs/firestore_update.log