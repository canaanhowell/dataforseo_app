# DataForSEO API Guide - Clickstream Data

## Overview
DataForSEO provides clickstream data through multiple endpoints, allowing you to get search volume and keyword metrics based on real user search behavior.

## Authentication
- **Method**: Basic Authentication (Base64 encoded)
- **Format**: `Authorization: Basic base64(login:password)`
- **Credentials**: Use the base64 string from your `.env` file

## Rate Limits
- **General**: 2000 API calls per minute
- **Clickstream**: 12 requests per minute per account
- **Simultaneous**: Maximum 30 concurrent requests

## Available Endpoints

### 1. Search Volume (with location)
**Endpoint**: `POST https://api.dataforseo.com/v3/keywords_data/clickstream_data/search_volume/live`

**Parameters**:
```json
[{
  "keywords": ["keyword1", "keyword2"],  // Max 1000 keywords
  "location_name": "United States",      // OR use location_code
  "location_code": 2840,                 // Alternative to location_name
  "language_name": "English",            // OR use language_code
  "language_code": "en",                 // Alternative to language_name
  "use_clickstream": true,               // Default: true
  "tag": "my-task-id"                    // Optional identifier
}]
```

**Response Fields**:
- `keyword`: The searched keyword
- `search_volume`: Current search volume
- `monthly_searches`: Array of monthly data (year, month, search_volume)

### 2. Global Search Volume
**Endpoint**: `POST https://api.dataforseo.com/v3/keywords_data/clickstream_data/search_volume_normalized/live`

**Parameters**:
```json
[{
  "keywords": ["keyword1", "keyword2"],  // Max 1000, min 3 chars each
  "tag": "my-task-id"                    // Optional
}]
```

**Response Fields**:
- `keyword`: The searched keyword
- `search_volume`: Global clickstream-based search volume
- `country_distribution`: Array with country breakdowns
  - `country_iso_code`: Country code
  - `search_volume`: Volume in that country
  - `percentage`: Percentage of global volume

### 3. Search Volume by Location
**Endpoint**: `POST https://api.dataforseo.com/v3/keywords_data/clickstream_data/search_volume_by_locaton/live`

**Parameters**:
```json
[{
  "keywords": ["keyword1", "keyword2"],  // Max 1000, min 3 chars each
  "location_name": "United Kingdom",     // OR use location_code
  "location_code": 2826,                 // Alternative to location_name
  "tag": "my-task-id"                    // Optional
}]
```

**Response Fields**:
- `keyword`: The searched keyword
- `search_volume`: Location-specific search volume
- `monthly_searches`: Monthly breakdown for past 12 months

### 4. Get Locations and Languages
**Endpoint**: `GET https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`

No parameters needed - returns all supported locations and languages.

## Important Notes

1. **Keyword Requirements**:
   - Maximum 1000 keywords per request
   - Minimum 3 characters per keyword
   - Keywords converted to lowercase
   - Certain symbols/emojis not allowed

2. **Location/Language**:
   - Must specify either `location_name` OR `location_code`
   - Must specify either `language_name` OR `language_code`
   - Get valid values from locations_and_languages endpoint

3. **Pricing**:
   - Charged per request, not per keyword
   - 1 keyword costs same as 1000 keywords

4. **Data Processing**:
   - All endpoints support Live mode
   - Results include decoded keywords (+ becomes space)
   - Misspelled keywords automatically corrected

## Example Python Implementation

```python
import base64
import requests
from typing import Dict, List, Optional

class DataForSEOClient:
    def __init__(self, login: str, password: str):
        self.base_url = "https://api.dataforseo.com/v3"
        self.auth = base64.b64encode(f"{login}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json"
        }
    
    def get_search_volume(
        self, 
        keywords: List[str], 
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_name: Optional[str] = None,
        language_code: Optional[str] = None,
        use_clickstream: bool = True
    ) -> Dict:
        """Get search volume with location/language settings"""
        
        endpoint = f"{self.base_url}/keywords_data/clickstream_data/search_volume/live"
        
        payload = [{
            "keywords": keywords,
            "use_clickstream": use_clickstream
        }]
        
        if location_name:
            payload[0]["location_name"] = location_name
        elif location_code:
            payload[0]["location_code"] = location_code
            
        if language_name:
            payload[0]["language_name"] = language_name
        elif language_code:
            payload[0]["language_code"] = language_code
            
        response = requests.post(endpoint, json=payload, headers=self.headers)
        return response.json()
```

## Error Handling

Always check the `status_code` in responses:
- `20000`: Success
- `40000`+: Various error conditions

Each task has its own status_code in the tasks array.