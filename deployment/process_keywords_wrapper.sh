#!/bin/bash
# Wrapper script for processing master keywords

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
echo "$(date) - Starting keyword processing..." >> logs/process_keywords.log
python src/scripts/process_master_keywords.py 2>&1 | tee -a logs/process_keywords.log
echo "$(date) - Keyword processing completed" >> logs/process_keywords.log