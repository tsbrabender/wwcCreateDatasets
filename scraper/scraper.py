"""
Web Scraping Module

Handles extraction of content from various web sources including HTML pages,
PDFs, and APIs. Supports concurrent scraping with configurable workers.

Features:
    - HTML content extraction using BeautifulSoup
    - Recursive website crawling with same-domain filtering
    - PDF text extraction
    - API endpoint queries
    - Rate limiting and retry logic
    - Content validation and cleaning
"""

import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from io import BytesIO
import json
import hashlib

import requests
from bs4 import BeautifulSoup
import PyPDF2


logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper-related errors."""
    pass


class WebScraper:
    """
    Scrapes content from various web sources with automatic PDF detection.
    
    High-Level Logic:
    1. Accepts multiple data sources (HTML pages, PDFs, APIs)
    2. Automatically detects if HTML URLs are actually PDFs
    3. Performs concurrent scraping with configurable workers
    4. For HTML: Supports single-page or recursive multi-page crawling
    5. For PDFs: Extracts text from all pages
    6. For APIs: Fetches and parses JSON responses
    7. Saves all content with metadata to disk
    
    Features:
        - Single page or recursive multi-page scraping
        - Automatic PDF detection (even when served as HTML URLs)
        - Same-domain URL filtering to prevent external crawling
        - Configurable crawl depth and rate limiting
        - URL deduplication and link extraction
        - Retry logic with exponential backoff
        - Concurrent worker pool for parallel scraping
    """
    
    DEFAULT_TIMEOUT = 15
    DEFAULT_RETRIES = 3
    DEFAULT_BACKOFF = 2
    DEFAULT_CRAWL_DEPTH = 3  # How many link levels to follow
    DEFAULT_CRAWL_DELAY = 0.5  # Seconds between requests to same domain
    DEFAULT_MAX_PAGES = None  # None = unlimited (value of -1 or None)
    
    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: Path,
        workers: int = 2,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        crawl_depth: int = DEFAULT_CRAWL_DEPTH,
        crawl_delay: float = DEFAULT_CRAWL_DELAY,
        max_pages: Optional[int] = DEFAULT_MAX_PAGES
    ):
        """
        Initialize web scraper.
        
        Args:
            config: Configuration dictionary containing 'sources' list
            output_dir: Directory to save raw content
            workers: Number of concurrent worker threads
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
            crawl_depth: Maximum depth for recursive crawling (0 = single page only)
            crawl_delay: Delay in seconds between requests to same domain
            max_pages: Maximum total pages to crawl per source (None or -1 = unlimited)
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.workers = workers
        self.timeout = timeout
        self.retries = retries
        self.crawl_depth = crawl_depth
        self.crawl_delay = crawl_delay
        # Normalize max_pages: "max", -1, or None all mean unlimited
        self.max_pages = None if (max_pages is None or max_pages == -1 or max_pages == "max") else max_pages
        self.sessions = {}
        
        # Create session for connection pooling
        self.session = requests.Session()
        
        logger.info(f"WebScraper initialized with {workers} workers, crawl_depth={crawl_depth}")
    
    def scrape_all(self) -> None:
        """
        Scrape all configured sources concurrently.
        
        High-Level Logic:
        1. Retrieves all sources from configuration
        2. Creates thread pool with configured number of workers
        3. Submits each source to thread pool for parallel processing
        4. Tracks completion and handles errors per source
        5. Logs results (success/failure) for each source
        
        Uses ThreadPoolExecutor to scrape multiple sources in parallel.
        Results are saved directly to disk.
        """
        sources = self.config.get('sources', [])
        
        if not sources:
            logger.warning("No sources configured for scraping")
            return
        
        logger.info(f"Starting to scrape {len(sources)} sources")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.scrape_source, source): source['name']
                for source in sources
            }
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    result = future.result()
                    logger.info(f"Successfully scraped: {source_name}")
                except Exception as e:
                    logger.error(f"Failed to scrape {source_name}: {e}")
        
        logger.info("Web scraping completed")
    
    def scrape_source(self, source: Dict[str, Any]) -> None:
        """
        Scrape a single source based on its type, with automatic PDF detection.
        
        High-Level Logic:
        1. Extracts scrape_type from source config
        2. For 'web' type: Checks if URL actually serves PDF content
        3. Routes to appropriate scraper method:
           - _scrape_web: For HTML pages (single or recursive)
           - _scrape_pdf: For PDF documents
           - _scrape_api: For JSON API endpoints
        4. Handles setup and teardown for each scrape type
        
        Args:
            source: Source configuration dictionary with keys:
                    'name': Display name
                    'url': URL to scrape
                    'scrape_type': 'web', 'pdf', or 'api'
                    'content_selector': CSS selector (for web, optional)
                    'recursive': Whether to follow links (for web, optional)
            
        Raises:
            ScraperError: If scraping fails or invalid scrape_type
        """
        source_type = source.get('scrape_type', 'web')
        
        if source_type == 'web':
            self._scrape_web(source)
        elif source_type == 'pdf':
            self._scrape_pdf(source)
        elif source_type == 'api':
            self._scrape_api(source)
        else:
            raise ScraperError(f"Unknown scrape type: {source_type}")
    
    def _scrape_web(self, source: Dict[str, Any]) -> None:
        """
        Scrape HTML content with automatic PDF detection and recursive crawling.
        
        High-Level Logic:
        1. Attempts to fetch URL and check content-type headers
        2. If content is PDF (detected by MIME type), routes to _scrape_pdf
        3. If HTML and recursive mode enabled, uses _crawl_recursive
        4. If HTML and recursive disabled, uses _scrape_single_page
        5. Handles errors gracefully with fallback to HTML parsing
        
        Args:
            source: Source configuration with:
                    'url': URL to fetch
                    'content_selector': CSS selector for content extraction
                    'recursive': Enable/disable recursive link following (default: True)
                    'crawl_depth': Maximum depth for recursive crawling (overrides class default)
                    'max_pages': Maximum pages to crawl (overrides class default, "max"/-1/None = unlimited)
        """
        url = source['url']
        content_selector = source.get('content_selector', 'body')
        recursive = source.get('recursive', True)  # Default to recursive
        crawl_depth = source.get('crawl_depth', self.crawl_depth)
        max_pages = source.get('max_pages', self.max_pages)  # Per-source override
        
        # Auto-detect if this is actually a PDF file
        if self._is_pdf_url(url):
            logger.info(f"Detected PDF content at {url}, switching to PDF parser")
            self._scrape_pdf(source)
            return
        
        if recursive and crawl_depth > 0:
            # Recursive crawling
            logger.info(f"Starting recursive crawl of {url} (depth={crawl_depth})")
            visited_urls: Set[str] = set()
            page_count = [0]  # Use list to track count across recursion
            self._crawl_recursive(
                source=source,
                current_url=url,
                content_selector=content_selector,
                depth=crawl_depth,
                visited_urls=visited_urls,
                page_count=page_count,
                max_pages=max_pages
            )
            logger.info(f"Recursive crawl completed: {page_count[0]} pages scraped")
        else:
            # Single page scraping
            self._scrape_single_page(source, url, content_selector)
    
    def _crawl_recursive(
        self,
        source: Dict[str, Any],
        current_url: str,
        content_selector: str,
        depth: int,
        visited_urls: Set[str],
        page_count: List[int],
        parent_domain: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> None:
        """
        Recursively crawl website following internal links with depth and page count controls.
        
        High-Level Logic:
        1. Validates URL hasn't been visited (deduplication)
        2. Checks if max_pages limit already reached (stops crawling if so)
        3. Checks URL belongs to same domain (no external crawling)
        4. Fetches and extracts content using CSS selector
        5. Saves extracted content with URL-based unique filename
        6. If depth > 1 and pages < max_pages: Extracts all internal links
        7. For each new link: Recursively calls itself with depth-1
        8. Applies rate limiting between requests
        9. Logs progress and handles errors gracefully
        
        Args:
            source: Source configuration dict
            current_url: URL to scrape (may be relative)
            content_selector: CSS selector for extracting content
            depth: Remaining levels to crawl (1=current page only)
            visited_urls: Set of processed URLs for deduplication
            page_count: List[int] for tracking pages (mutable reference)
            parent_domain: Base domain for filtering (auto-detected on first call)
            max_pages: Maximum pages to scrape (None = unlimited)
        """
        # Normalize URL
        current_url = current_url.strip()
        if current_url in visited_urls:
            return
        
        visited_urls.add(current_url)
        
        # Check if we've reached max_pages limit
        if max_pages is not None and page_count[0] >= max_pages:
            logger.debug(f"Max pages limit ({max_pages}) reached, stopping crawl")
            return
        
        # Set parent domain on first call
        if parent_domain is None:
            parent_domain = urlparse(current_url).netloc
        
        # Check if URL is same domain
        if not self._is_same_domain(current_url, parent_domain):
            logger.debug(f"Skipping external link: {current_url}")
            return
        
        try:
            # Check if this is a PDF before attempting HTML parsing
            if self._is_pdf_url(current_url):
                logger.debug(f"Detected PDF in recursive crawl: {current_url}")
                try:
                    response = self._fetch_url_raw(current_url)
                    pdf_reader = PyPDF2.PdfReader(BytesIO(response))
                    text_content = []
                    
                    for page_num in range(len(pdf_reader.pages)):
                        try:
                            text_content.append(pdf_reader.pages[page_num].extract_text())
                        except Exception as e:
                            logger.warning(f"Failed to extract PDF page {page_num + 1} from {current_url}: {e}")
                    
                    text_content = '\n'.join(text_content)
                    text_content = self._clean_text(text_content)
                    self._save_source_content(source, text_content, 'pdf', current_url)
                    page_count[0] += 1
                    
                    # Rate limiting
                    time.sleep(self.crawl_delay)
                    return  # PDFs don't have links to crawl
                
                except Exception as e:
                    logger.warning(f"Error processing PDF {current_url}: {e}")
                    return
            
            # Scrape current page
            logger.debug(f"Scraping: {current_url} (depth remaining: {depth})")
            content = self._fetch_url(current_url)
            
            # Extract and save content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove excluded elements before extracting target content
            exclude_selectors = source.get('exclude_selectors', [])
            soup = self._remove_excluded_elements(soup, exclude_selectors)
            
            target_element = soup.select_one(content_selector)
            
            if not target_element:
                logger.debug(f"Content selector not found in {current_url}, using full page")
                text_content = soup.get_text()
            else:
                text_content = target_element.get_text()
            
            text_content = self._clean_text(text_content)
            self._save_source_content(source, text_content, 'html', current_url)
            page_count[0] += 1
            
            # Rate limiting - be respectful to servers
            time.sleep(self.crawl_delay)
            
            # Follow links if depth remains and not at max_pages limit
            if depth > 1 and (max_pages is None or page_count[0] < max_pages):
                links = self._extract_links(soup, current_url, parent_domain)
                for link_url in links:
                    # Stop if we've hit max_pages limit
                    if max_pages is not None and page_count[0] >= max_pages:
                        logger.info(f"Max pages limit ({max_pages}) reached, stopping link crawl")
                        break
                    
                    if link_url not in visited_urls:
                        self._crawl_recursive(
                            source=source,
                            current_url=link_url,
                            content_selector=content_selector,
                            depth=depth - 1,
                            visited_urls=visited_urls,
                            page_count=page_count,
                            parent_domain=parent_domain,
                            max_pages=max_pages
                        )
        
        except Exception as e:
            logger.warning(f"Error scraping {current_url}: {e}")
    
    def _scrape_single_page(
        self,
        source: Dict[str, Any],
        url: str,
        content_selector: str
    ) -> None:
        """
        Scrape a single HTML page without following links.
        
        High-Level Logic:
        1. Fetches HTML content from URL
        2. Parses HTML with BeautifulSoup
        3. Removes excluded elements (headers, footers, etc.)
        4. Extracts content using provided CSS selector
        5. Falls back to full page text if selector not found
        6. Cleans and normalizes text formatting
        7. Saves to disk with metadata
        
        Args:
            source: Source configuration dict with 'name', 'url'
            url: URL to fetch and parse
            content_selector: CSS selector for extracting relevant content
        """
        try:
            content = self._fetch_url(url)
            
            # Parse HTML and extract content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove excluded elements before extracting target content
            exclude_selectors = source.get('exclude_selectors', [])
            soup = self._remove_excluded_elements(soup, exclude_selectors)
            
            target_element = soup.select_one(content_selector)
            
            if not target_element:
                logger.warning(f"Content selector '{content_selector}' not found in {url}")
                text_content = soup.get_text()
            else:
                text_content = target_element.get_text()
            
            # Clean whitespace
            text_content = self._clean_text(text_content)
            
            # Save content
            self._save_source_content(source, text_content, 'html', url)
        
        except Exception as e:
            logger.error(f"Failed to scrape single page {url}: {e}")
            raise
    
    def _extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        parent_domain: str
    ) -> List[str]:
        """
        Extract all internal links from HTML matching same domain.
        
        High-Level Logic:
        1. Finds all <a> tags with href attributes
        2. Filters out anchors (#), javascript:, and other non-HTTP links
        3. Converts relative URLs to absolute using base URL
        4. Removes URL fragments (everything after #)
        5. Filters links to only those on same domain
        6. Returns deduplicated list of valid internal links
        
        Args:
            soup: BeautifulSoup object of parsed HTML page
            base_url: Base URL for resolving relative links
            parent_domain: Parent domain to filter internal links only
            
        Returns:
            List[str]: Absolute URLs of all same-domain links found
        """
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip anchors and javascript
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Remove fragments
            absolute_url = absolute_url.split('#')[0]
            
            # Check if same domain
            if self._is_same_domain(absolute_url, parent_domain):
                links.append(absolute_url)
        
        logger.debug(f"Found {len(links)} internal links on {base_url}")
        return links
    
    def _is_same_domain(self, url: str, parent_domain: str) -> bool:
        """
        Check if URL belongs to same domain, ignoring www. variations.
        
        High-Level Logic:
        1. Parses URL to extract domain (netloc)
        2. Normalizes domain names to lowercase
        3. Removes www. prefix from both domains for comparison
        4. Returns true only if domains exactly match
        5. Handles exceptions by returning False (invalid URLs)
        
        Args:
            url: Full URL to check (e.g., 'https://docs.example.com/page')
            parent_domain: Parent domain to compare (e.g., 'example.com')
            
        Returns:
            bool: True if URL is on same domain, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            url_domain = parsed_url.netloc.lower()
            parent_domain = parent_domain.lower()
            
            # Remove www. for comparison
            url_domain_clean = url_domain.replace('www.', '')
            parent_domain_clean = parent_domain.replace('www.', '')
            
            return url_domain_clean == parent_domain_clean
        except Exception:
            return False
    
    def _is_pdf_url(self, url: str) -> bool:
        """
        Check if URL points to PDF content (even if served as HTML).
        
        High-Level Logic:
        1. Makes HEAD request to URL (efficient, no body download)
        2. Checks Content-Type header for 'application/pdf'
        3. Falls back to checking URL extension (.pdf)
        4. Returns True if either indicator suggests PDF
        5. Handles network errors gracefully (returns False)
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL appears to serve PDF content
        """
        try:
            # Try HEAD request first (efficient, no body download)
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            if 'application/pdf' in content_type:
                logger.info(f"Detected PDF from Content-Type header: {url}")
                return True
        except Exception as e:
            logger.debug(f"HEAD request failed for {url}: {e}")
        
        # Fallback: Check URL extension
        if url.lower().endswith('.pdf'):
            logger.info(f"Detected PDF from URL extension: {url}")
            return True
        
        return False
    
    def _scrape_pdf(self, source: Dict[str, Any]) -> None:
        """
        Extract text from PDF files (downloaded from URL or detected as PDF).
        
        High-Level Logic:
        1. Retrieves URL from source configuration
        2. Downloads PDF file with retry logic
        3. Creates PyPDF2 reader from downloaded bytes
        4. Iterates through all pages in PDF
        5. Extracts text from each page
        6. Joins all page text with newlines
        7. Cleans and normalizes extracted text
        8. Saves content with PDF metadata
        
        Args:
            source: Source configuration dict with 'name' and 'url'
                    URL should point to PDF file or be detected as PDF
        """
        url = source['url']
        
        try:
            logger.info(f"Scraping PDF from: {url}")
            
            # Download PDF
            response = self._fetch_url_raw(url)
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(response))
            text_content = []
            
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
            
            text_content = '\n'.join(text_content)
            text_content = self._clean_text(text_content)
            
            # Save content
            self._save_source_content(source, text_content, 'pdf')
            logger.info(f"Successfully extracted {len(pdf_reader.pages)} pages from PDF")
        
        except Exception as e:
            logger.error(f"Failed to scrape PDF {url}: {e}")
            raise ScraperError(f"PDF parsing failed for {url}: {e}")
    
    def _scrape_api(self, source: Dict[str, Any]) -> None:
        """
        Fetch JSON content from RESTful API endpoint.
        
        High-Level Logic:
        1. Retrieves API URL from source configuration
        2. Fetches URL content with retry logic
        3. Parses JSON response
        4. Formats JSON with indentation for readability
        5. Saves API response with metadata
        
        Args:
            source: Source configuration dict with 'name' and 'url'
                    URL should be JSON API endpoint
        """
        url = source['url']
        
        response = self._fetch_url_json(url)
        
        # Save as JSON
        self._save_source_content(source, json.dumps(response, indent=2), 'api')
    
    def _fetch_url(self, url: str) -> str:
        """
        Fetch HTML content from URL with exponential backoff retry.
        
        High-Level Logic:
        1. Attempts fetch up to self.retries times
        2. Uses requests.get with timeout and User-Agent headers
        3. On success: Returns response text
        4. On failure: Waits (2^attempt seconds) and retries
        5. After all retries exhausted: Raises ScraperError
        6. Includes random 1-3 second delay before each request to prevent blocking
        
        Args:
            url: URL to fetch
            
        Returns:
            str: HTML response content as string
            
        Raises:
            ScraperError: If all retry attempts fail
        """
        for attempt in range(self.retries):
            try:
                # Random delay between 1-3 seconds to prevent blocking
                delay = random.uniform(1, 3)
                time.sleep(delay)
                
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                response.raise_for_status()
                return response.text
            
            except requests.RequestException as e:
                if attempt < self.retries - 1:
                    wait_time = self.DEFAULT_BACKOFF ** attempt
                    logger.warning(f"Retry {attempt + 1}/{self.retries} for {url} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise ScraperError(f"Failed to fetch {url} after {self.retries} attempts: {e}")
    
    def _fetch_url_raw(self, url: str) -> bytes:
        """
        Fetch URL and return raw bytes for binary content (PDFs).
        
        High-Level Logic:
        1. Attempts fetch up to self.retries times
        2. Uses requests.get with timeout
        3. On success: Returns response.content (raw bytes)
        4. On failure: Waits (2^attempt seconds) and retries
        5. Suitable for binary files (PDFs, images, etc.)
        6. Includes random 1-3 second delay before each request to prevent blocking
        
        Args:
            url: URL to fetch
            
        Returns:
            bytes: Raw response content (not decoded)
        """
        for attempt in range(self.retries):
            try:
                # Random delay between 1-3 seconds to prevent blocking
                delay = random.uniform(1, 3)
                time.sleep(delay)
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                if attempt < self.retries - 1:
                    time.sleep(self.DEFAULT_BACKOFF ** attempt)
                else:
                    raise ScraperError(f"Failed to fetch {url}: {e}")
    
    def _fetch_url_json(self, url: str) -> Dict[str, Any]:
        """
        Fetch URL content and parse as JSON.
        
        High-Level Logic:
        1. Calls _fetch_url to get content with retry logic
        2. Attempts JSON parsing with json.loads
        3. On success: Returns parsed dict/list
        4. On parse failure: Raises ScraperError with details
        
        Args:
            url: API endpoint URL
            
        Returns:
            Dict[str, Any]: Parsed JSON response
        """
        content = self._fetch_url(url)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ScraperError(f"Failed to parse JSON from {url}: {e}")
    
    def _remove_excluded_elements(
        self,
        soup: BeautifulSoup,
        exclude_selectors: Optional[List[str]] = None
    ) -> BeautifulSoup:
        """
        Remove elements matching exclusion selectors from HTML.
        
        High-Level Logic:
        1. Takes list of CSS selectors to exclude (e.g., "header", "footer", ".nav")
        2. For each selector: Finds all matching elements in soup
        3. Removes each matched element from the DOM tree
        4. Returns modified soup object (with unwanted elements gone)
        5. Logs excluded element count for debugging
        
        Args:
            soup: BeautifulSoup object of parsed HTML
            exclude_selectors: List of CSS selectors to remove.
                             Common patterns: "header", "footer", "nav", ".sidebar"
                             
        Returns:
            BeautifulSoup: Modified soup with excluded elements removed
        """
        if not exclude_selectors:
            return soup
        
        total_removed = 0
        for selector in exclude_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    element.decompose()  # Remove from tree
                if elements:
                    logger.debug(f"Removed {len(elements)} elements matching '{selector}'")
                    total_removed += len(elements)
            except Exception as e:
                logger.warning(f"Failed to remove selector '{selector}': {e}")
        
        if total_removed > 0:
            logger.info(f"Excluded {total_removed} total elements from page content")
        
        return soup
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content for processing.
        
        High-Level Logic:
        1. Normalizes Windows and Unix line endings to \n
        2. Splits text into lines
        3. Strips whitespace from each line
        4. Removes empty lines
        5. Rejoins lines with single newline
        
        Args:
            text: Raw text content (may have excess whitespace)
            
        Returns:
            str: Cleaned text with normalized formatting
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        return '\n'.join(lines)
    
    def _save_source_content(
        self,
        source: Dict[str, Any],
        content: str,
        content_type: str,
        url: Optional[str] = None
    ) -> None:
        """
        Save source content to disk as JSON with metadata.
        
        High-Level Logic:
        1. Derives safe filename from source name
        2. If URL provided: Creates URL hash for unique filename per page
        3. If no URL: Uses standard source_type filename (single page)
        4. Creates metadata dict with source, URL, type, timestamp
        5. Wraps content and metadata in JSON structure
        6. Writes JSON file with UTF-8 encoding
        7. Logs save location
        
        Args:
            source: Source configuration dict with 'name', 'url'
            content: Extracted/processed content text
            content_type: Content category ('html', 'pdf', or 'api')
            url: Optional URL for recursive crawling (generates unique filename)
        """
        source_name = source['name'].replace(' ', '_').lower()
        
        # Generate filename - unique per URL if URL provided (for recursive crawling)
        if url:
            # Create hash of URL for unique filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{source_name}_{content_type}_{url_hash}.json"
        else:
            # Single page filename (backward compatible)
            filename = f"{source_name}_{content_type}.json"
        
        filepath = self.output_dir / filename
        
        # Create metadata
        metadata = {
            'name': source['name'],
            'url': url or source['url'],
            'scrape_type': content_type,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'content_length': len(content)
        }
        
        # Save as JSON
        output_data = {
            'metadata': metadata,
            'content': content
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved content to: {filepath}")
