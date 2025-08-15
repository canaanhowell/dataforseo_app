# DataForSEO App Overview

## Purpose
The DataForSEO app is a keyword analysis and tracking system that leverages DataForSEO's APIs to provide search volume data, trend analysis, and keyword insights for AI products and emerging technologies.

## Key Features

### 1. Search Volume Data Collection
- Retrieves real Google search volume data for up to 1000 keywords per request
- Provides monthly search volumes with 12-month historical data
- Supports location and language-specific data (currently configured for US/English)
- Processes 486 keywords from the master list with automated batching

### 2. Trend Analysis
- Integrates with Google Trends API for up-to-date popularity metrics
- Provides daily trend data up to the current date
- Calculates trend direction (rising, declining, stable) based on historical data
- Offers relative popularity scores (0-100 scale) for recent time periods

### 3. Data Processing & Storage
- Automatically sorts keywords by search volume (descending)
- Saves results in JSON format with keyword, volume, and date
- Handles null values and API errors gracefully
- Implements rate limiting to comply with API restrictions

## API Endpoints Used

### Search Volume API
- **Endpoint**: `/v3/keywords_data/google/search_volume/live`
- **Cost**: $0.075 per request (up to 700 keywords)
- **Rate Limit**: 2000 requests/minute general, 12 requests/minute for this endpoint
- **Data Lag**: ~2 months (latest data from June 2025 as of August 2025)

### Google Trends API
- **Endpoint**: `/v3/keywords_data/google_trends/explore/live`
- **Cost**: $0.009 per request
- **Data**: Real-time up to current date
- **Scale**: Relative popularity (0-100)

## Key Files

### Configuration
- `config/master_keywords.json` - List of 486 products/keywords to track
- `config/keyword_volumes.json` - Sorted search volume results
- `.env` - API credentials (Base64 encoded)

### Core Scripts
- `src/utils/dataforseo_client.py` - Async API client with error handling
- `src/scripts/process_master_keywords.py` - Batch processes all keywords
- `src/scripts/test_single_keyword.py` - Tests individual keywords
- `src/scripts/test_google_trends.py` - Gets recent trend data
- `src/scripts/sort_keyword_volumes.py` - Sorts results by volume

### Documentation
- `docs/DATAFORSEO_API_GUIDE.md` - Reformatted API documentation
- `docs/dataforseo_official.md` - Original API documentation
- `docs/README.md` - Implementation status and notes

## Key Findings from Data

### Top 10 Keywords by Search Volume (US)
1. **character ai** - 5,000,000 searches/month
2. **deepseek** - 1,830,000 searches/month
3. **copilot** - 1,500,000 searches/month
4. **oura ring** - 1,220,000 searches/month
5. **grok** - 673,000 searches/month
6. **meta quest 3** - 550,000 searches/month
7. **happy hr** - 368,000 searches/month
8. **perplexity ai** - 368,000 searches/month
9. **meta glasses** - 301,000 searches/month
10. **liquid death** - 246,000 searches/month

### Summary Statistics
- **Total keywords analyzed**: 486
- **Keywords with search volume**: 384 (79%)
- **Total monthly searches**: 17,936,880
- **API cost**: ~$0.38 for full analysis

## Usage Examples

### Process All Keywords
```bash
python3 src/scripts/process_master_keywords.py
```

### Test Single Keyword
```bash
python3 src/scripts/test_single_keyword.py "chatgpt"
```

### Get Recent Trends
```bash
python3 src/scripts/test_google_trends.py "chatgpt"
```

### Analyze Results
```bash
python3 src/scripts/analyze_keyword_volumes.py
```

## Data Accuracy
- Search volume data is from Google's official advertising API
- Enhanced with clickstream data for improved accuracy
- Automatically corrects misspelled keywords
- Returns real data only - errors are raised rather than returning fake data

## Integration Points
The sorted keyword volume data in `config/keyword_volumes.json` can be:
- Imported into the exploding_topics_app for trend analysis
- Used to prioritize which products to track more closely
- Cross-referenced with other data sources for validation
- Updated periodically to track growth trends

## Future Enhancements
1. Automated weekly/monthly data updates
2. Integration with Firestore for historical tracking
3. Trend alerts for rapidly growing keywords
4. Competitive analysis features
5. Multi-location support for global insights
6. Cost optimization through intelligent batching