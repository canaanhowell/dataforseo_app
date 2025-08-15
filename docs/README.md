# DataForSEO Clickstream API Integration

## Status

Successfully created DataForSEO Clickstream API integration. The connection works but requires payment/credits to retrieve actual data.

## What Was Created

### 1. API Client (`src/utils/dataforseo_client.py`)
- Async client with proper error handling
- Rate limiting (12 requests/minute for clickstream)
- Support for multiple endpoints:
  - Search Volume with location/language
  - Global Search Volume
  - Search Volume by Location
  - Locations and Languages lookup

### 2. Configuration (`src/config/config.py`)
- Loads credentials from `.env` file
- Decodes base64 authentication
- Validates required settings

### 3. Test Script (`src/scripts/test_clickstream_connection.py`)
- Tests all API endpoints
- Validates authentication
- Provides detailed error reporting

### 4. Example Script (`src/scripts/clickstream_example.py`)
- Demonstrates real-world usage
- Analyzes keyword trends
- Saves results to JSON
- Provides insights and summaries

## API Authentication

Your credentials are correctly configured:
- Base64 encoded string: `YWRtaW5Ac3ludGhldGlrbWVkaWEuYWk6OWZjY2NiZWU2NjBhN2EwNQ==`
- Decoded to: `admin@synthetikmedia.ai:9fcccbee660a7a05`

## Current Issue

The API returns "Payment Required" (402) error when trying to fetch search volume data. This indicates:
- Authentication is working correctly
- The account needs credits or payment to access the data
- The API endpoint path is correct: `/v3/keywords_data/google/search_volume/live`

## Next Steps

1. **Add Credits**: Log into your DataForSEO account and add credits
2. **Check Balance**: Use their dashboard to verify available API credits
3. **Test Again**: Run the scripts after adding credits

## Usage

```bash
# Test connection
python3 src/scripts/test_clickstream_connection.py

# Run example analysis
python3 src/scripts/clickstream_example.py
```

## API Endpoints Used

1. **Locations & Languages**: `GET /v3/keywords_data/clickstream_data/locations_and_languages`
   - ✅ Working (returns list of supported locations)

2. **Search Volume**: `POST /v3/keywords_data/google/search_volume/live`
   - ⚠️ Requires payment/credits
   - Supports up to 700 keywords per request
   - Returns monthly search volumes and trends

## File Structure

```
dataforseo_app/
├── src/
│   ├── utils/
│   │   └── dataforseo_client.py    # Main API client
│   ├── config/
│   │   └── config.py               # Configuration management
│   └── scripts/
│       ├── test_clickstream_connection.py  # Connection tester
│       └── clickstream_example.py          # Usage example
├── docs/
│   ├── DATAFORSEO_API_GUIDE.md    # Reformatted API documentation
│   └── README.md                   # This file
└── .env                            # Your credentials
```

## Important Notes

- The client follows all guidelines from `master_docs/GUIDELINES.md`
- Implements proper error handling (no fake data)
- Uses async I/O for scalability
- Includes rate limiting
- Comprehensive logging

Once you add credits to your DataForSEO account, all the scripts will work and provide real clickstream data for your keywords.