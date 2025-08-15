import asyncio
import aiohttp
import base64
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchVolumeResult:
    """Represents search volume data for a keyword"""
    keyword: str
    search_volume: int
    monthly_searches: List[Dict[str, int]]
    location_code: Optional[int] = None
    language_code: Optional[str] = None
    use_clickstream: bool = True


@dataclass
class GlobalSearchVolumeResult:
    """Represents global search volume with country distribution"""
    keyword: str
    search_volume: int
    country_distribution: List[Dict[str, Any]]


class DataForSEOError(Exception):
    """Custom exception for DataForSEO API errors"""
    pass


class DataForSEOClient:
    """
    Async client for DataForSEO Clickstream API with proper error handling and rate limiting.
    
    Follows the guidelines from master_docs/GUIDELINES.md:
    - Real data or error (no fake data)
    - Proper error handling and logging
    - Rate limiting for external APIs
    - Async I/O for scalability
    """
    
    def __init__(self, login: str, password: str, rate_limit: int = 12):
        """
        Initialize DataForSEO client.
        
        Args:
            login: DataForSEO login email
            password: DataForSEO API password
            rate_limit: Requests per minute (default: 12 for clickstream)
        """
        self.base_url = "https://api.dataforseo.com/v3"
        self.auth = base64.b64encode(f"{login}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json"
        }
        self.rate_limiter = asyncio.Semaphore(rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with proper error handling and rate limiting.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            DataForSEOError: If API returns an error
        """
        if not self.session:
            raise DataForSEOError("Client not initialized. Use async context manager.")
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        async with self.rate_limiter:
            try:
                logger.info(f"{method} {url}")
                
                if method == "POST":
                    async with self.session.post(url, json=data) as response:
                        duration = time.time() - start_time
                        logger.info(f"{method} {url} - {response.status} - {duration:.2f}s")
                        
                        response_data = await response.json()
                        
                        # Check for API errors
                        if response_data.get("status_code") != 20000:
                            error_msg = response_data.get("status_message", "Unknown error")
                            raise DataForSEOError(f"API error {response_data.get('status_code')}: {error_msg}")
                            
                        return response_data
                else:
                    async with self.session.get(url) as response:
                        duration = time.time() - start_time
                        logger.info(f"{method} {url} - {response.status} - {duration:.2f}s")
                        
                        response_data = await response.json()
                        
                        if response_data.get("status_code") != 20000:
                            error_msg = response_data.get("status_message", "Unknown error")
                            raise DataForSEOError(f"API error {response_data.get('status_code')}: {error_msg}")
                            
                        return response_data
                        
            except aiohttp.ClientError as e:
                duration = time.time() - start_time
                logger.error(f"{method} {url} - FAILED - {duration:.2f}s - {e}")
                raise DataForSEOError(f"Request failed: {e}")
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{method} {url} - ERROR - {duration:.2f}s - {e}")
                raise
                
    async def get_locations_and_languages(self) -> Dict[str, Any]:
        """
        Get all supported locations and languages.
        
        Returns:
            Dictionary with locations and languages data
        """
        endpoint = "keywords_data/clickstream_data/locations_and_languages"
        return await self._make_request("GET", endpoint)
        
    async def get_search_volume(
        self,
        keywords: List[str],
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_name: Optional[str] = None,
        language_code: Optional[str] = None,
        use_clickstream: bool = True,
        tag: Optional[str] = None
    ) -> List[SearchVolumeResult]:
        """
        Get search volume data for keywords with location/language settings.
        
        Args:
            keywords: List of keywords (max 1000)
            location_name: Full location name (e.g., "United States")
            location_code: Location code (e.g., 2840)
            language_name: Full language name (e.g., "English")
            language_code: Language code (e.g., "en")
            use_clickstream: Use clickstream data (default: True)
            tag: Optional task identifier
            
        Returns:
            List of SearchVolumeResult objects
            
        Raises:
            ValueError: If required parameters are missing
            DataForSEOError: If API returns an error
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")
            
        if len(keywords) > 1000:
            raise ValueError("Maximum 1000 keywords allowed per request")
            
        if not (location_name or location_code):
            raise ValueError("Either location_name or location_code is required")
            
        if not (language_name or language_code):
            raise ValueError("Either language_name or language_code is required")
            
        # Build payload
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
            
        if tag:
            payload[0]["tag"] = tag
            
        # Make request
        endpoint = "keywords_data/google/search_volume/live"
        response = await self._make_request("POST", endpoint, payload)
        
        # Parse results
        results = []
        for task in response.get("tasks", []):
            if task.get("status_code") != 20000:
                logger.error(f"Task error: {task.get('status_message')}")
                logger.error(f"Task data: {task.get('data')}")
                continue
                
            # Results are directly in the result array, not in items
            for result in task.get("result", []):
                # Each result is a keyword data object
                if "keyword" in result and "search_volume" in result:
                    results.append(SearchVolumeResult(
                        keyword=result["keyword"],
                        search_volume=result["search_volume"],
                        monthly_searches=result.get("monthly_searches", []),
                        location_code=result.get("location_code"),
                        language_code=result.get("language_code"),
                        use_clickstream=result.get("use_clickstream", True)
                    ))
                    logger.info(f"Processed keyword: {result['keyword']} - Volume: {result['search_volume']}")
                    
        return results
        
    async def get_global_search_volume(
        self,
        keywords: List[str],
        tag: Optional[str] = None
    ) -> List[GlobalSearchVolumeResult]:
        """
        Get global search volume with country distribution.
        
        Args:
            keywords: List of keywords (max 1000, min 3 chars each)
            tag: Optional task identifier
            
        Returns:
            List of GlobalSearchVolumeResult objects
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")
            
        if len(keywords) > 1000:
            raise ValueError("Maximum 1000 keywords allowed per request")
            
        for keyword in keywords:
            if len(keyword) < 3:
                raise ValueError(f"Keyword '{keyword}' must be at least 3 characters")
                
        # Build payload
        payload = [{
            "keywords": keywords
        }]
        
        if tag:
            payload[0]["tag"] = tag
            
        # Make request
        endpoint = "keywords_data/clickstream_data/search_volume_normalized/live"
        response = await self._make_request("POST", endpoint, payload)
        
        # Parse results
        results = []
        for task in response.get("tasks", []):
            if task.get("status_code") != 20000:
                logger.error(f"Task error: {task.get('status_message')}")
                continue
                
            for result in task.get("result", []):
                for item in result.get("items", []):
                    results.append(GlobalSearchVolumeResult(
                        keyword=item["keyword"],
                        search_volume=item["search_volume"],
                        country_distribution=item.get("country_distribution", [])
                    ))
                    
        return results
        
    async def get_search_volume_by_location(
        self,
        keywords: List[str],
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        tag: Optional[str] = None
    ) -> List[SearchVolumeResult]:
        """
        Get search volume data for specific location.
        
        Args:
            keywords: List of keywords (max 1000, min 3 chars each)
            location_name: Full location name
            location_code: Location code
            tag: Optional task identifier
            
        Returns:
            List of SearchVolumeResult objects
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")
            
        if not (location_name or location_code):
            raise ValueError("Either location_name or location_code is required")
            
        # Build payload
        payload = [{
            "keywords": keywords
        }]
        
        if location_name:
            payload[0]["location_name"] = location_name
        elif location_code:
            payload[0]["location_code"] = location_code
            
        if tag:
            payload[0]["tag"] = tag
            
        # Make request
        endpoint = "keywords_data/clickstream_data/search_volume_by_location/live"
        response = await self._make_request("POST", endpoint, payload)
        
        # Parse results
        results = []
        for task in response.get("tasks", []):
            if task.get("status_code") != 20000:
                logger.error(f"Task error: {task.get('status_message')}")
                continue
                
            for result in task.get("result", []):
                for item in result.get("items", []):
                    results.append(SearchVolumeResult(
                        keyword=item["keyword"],
                        search_volume=item["search_volume"],
                        monthly_searches=item.get("monthly_searches", []),
                        location_code=result.get("location_code")
                    ))
                    
        return results