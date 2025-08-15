# DataForSEO App

Keyword tracking and analysis application using DataForSEO API.

## Project Structure

```
dataforseo_app/
├── config/                 # Configuration files
├── database_management/    # Database scripts and utilities
├── deployment/            # Deployment scripts and configurations
├── docs/                  # Documentation
│   ├── context/          # Context and background information
│   └── deployment/       # Deployment-specific documentation
├── logs/                  # Application logs
└── src/                   # Source code
    ├── config/           # Configuration modules
    ├── scripts/          # Executable scripts
    │   ├── collectors/   # Data collection scripts
    │   └── utilities/    # Utility scripts
    └── utils/            # Shared utility modules
```

## Setup

1. Copy `.env.example` to `.env` and configure your DataForSEO credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Run setup script: `python src/scripts/setup_project.py`

## Development Guidelines

This project follows the guidelines in `/workspace/master_docs/GUIDELINES.md`