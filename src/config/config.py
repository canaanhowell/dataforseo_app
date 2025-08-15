import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Application configuration with validation."""
    
    # DataForSEO Settings
    DATAFORSEO_LOGIN = os.getenv('dataforseo_login_password')  # Base64 encoded string
    DATAFORSEO_API_KEY = os.getenv('dataforseo_api_key')
    
    # Decode base64 credentials if available
    DATAFORSEO_LOGIN_DECODED: Optional[str] = None
    DATAFORSEO_PASSWORD_DECODED: Optional[str] = None
    
    if DATAFORSEO_LOGIN:
        try:
            import base64
            decoded = base64.b64decode(DATAFORSEO_LOGIN).decode('utf-8')
            if ':' in decoded:
                DATAFORSEO_LOGIN_DECODED, DATAFORSEO_PASSWORD_DECODED = decoded.split(':', 1)
        except Exception as e:
            print(f"Error decoding DataForSEO credentials: {e}")
    
    # Rate Limits
    DATAFORSEO_RATE_LIMIT = int(os.getenv('DATAFORSEO_RATE_LIMIT', '12'))  # requests per minute
    
    # Application Settings
    MAX_KEYWORDS_PER_BATCH = int(os.getenv('MAX_KEYWORDS_PER_BATCH', '1000'))
    MAX_TREND_SCORE = int(os.getenv('MAX_TREND_SCORE', '100'))
    
    # Database
    FIRESTORE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID', 'ai-tracker-466821')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration is present."""
        required_vars = [
            'DATAFORSEO_LOGIN_DECODED',
            'DATAFORSEO_PASSWORD_DECODED',
            'FIRESTORE_PROJECT_ID'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required configuration: {missing}")
    
    @classmethod
    def to_dict(cls) -> dict:
        """Return configuration as dictionary (excluding secrets)."""
        return {
            'dataforseo_rate_limit': cls.DATAFORSEO_RATE_LIMIT,
            'max_keywords_per_batch': cls.MAX_KEYWORDS_PER_BATCH,
            'max_trend_score': cls.MAX_TREND_SCORE,
            'firestore_project_id': cls.FIRESTORE_PROJECT_ID,
            'log_level': cls.LOG_LEVEL
        }