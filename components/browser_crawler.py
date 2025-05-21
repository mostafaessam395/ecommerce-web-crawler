import asyncio
import logging
from playwright.async_api import async_playwright
import pandas as pd
import os
import time
import random
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
from langdetect import detect
import pycountry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BrowserCrawler')

class BrowserCrawler:
    """
    A headless browser-based crawler using Playwright for JavaScript-heavy websites like Amazon.
    This crawler respects robots.txt rules while implementing techniques to avoid being blocked.
    """
    
    def __init__(self, output_dir='crowl/data', project_name=None):
        """
        Initialize the browser crawler
        
        Args:
            output_dir (str): Directory to store crawled data
            project_name (str): Name of the project (used for file naming)
        """
        self.output_dir = output_dir
        self.project_name = project_name or 'browser-crawl'
        self.urls_data = []
        self.links_data = []
        self.visited_urls = set()
        self.robots_rules = {}
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.join(output_dir, self._get_domain_folder()), exist_ok=True)
        
        # Initialize data files
        self._init_data_files()
    
    def _get_domain_folder(self):
        """Get the domain folder name from the project name"""
        if not self.project_name:
            return 'default'
        return self.project_name.replace('.', '-').lower()
    
    def _init_data_files(self):
        """Initialize the data files with headers"""
        # URLs file
        urls_file = os.path.join(self.output_dir, self._get_domain_folder(), '_urls.csv')
        if not os.path.exists(urls_file) or os.path.getsize(urls_file) == 0:
            urls_df = pd.DataFrame(columns=[
                'url', 'response_code', 'content_type', 'level', 'referer', 'latency',
                'crawled_at', 'title', 'meta_description', 'canonical', 'h1', 'wordcount',
                'content_lang', 'pagerank'
            ])
            urls_df.to_csv(urls_file, index=False)
        
        # Links file
        links_file = os.path.join(self.output_dir, self._get_domain_folder(), '_links.csv')
        if not os.path.exists(links_file) or os.path.getsize(links_file) == 0:
            links_df = pd.DataFrame(columns=['source', 'target', 'text', 'nofollow', 'disallow'])
            links_df.to_csv(links_file, index=False)
    
    async def crawl(self, start_url, max_pages=50, max_depth=3, delay_range=(2, 5)):
        """
        Crawl a website using a headless browser
        
        Args:
            start_url (str): URL to start crawling from
            max_pages (int): Maximum number of pages to crawl
            max_depth (int): Maximum depth to crawl
            delay_range (tuple): Range of seconds to delay between requests
            
        Returns:
            tuple: (urls_data, links_data)
        """
        domain = urlparse(start_url).netloc
        self.project_name = domain
        
        # Parse robots.txt
        await self._parse_robots_txt(start_url)
        
        # Initialize the browser
        async with async_playwright() as p:
            # Use a more stealth browser configuration
            browser = await p.chromium.launch(headless=True)
            
            # Create a context with a custom user agent
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1280, 'height': 800},
                device_scale_factor=1,
                java_script_enabled=True,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth mode plugins
            await context.add_init_script("""
                // Overwrite the navigator.webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Overwrite the plugins property
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Overwrite the languages property
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            # Create a new page
            page = await context.new_page()
            
            # Set up request interception to handle cookies and headers
            await page.route("**/*", lambda route: self._handle_route(route))
            
            # Start crawling
            await self._crawl_page(page, start_url, 0, max_pages, max_depth, delay_range, None)
            
            # Close the browser
            await browser.close()
        
        # Save the data
        self._save_data()
        
        return self.urls_data, self.links_data
    
    async def _handle_route(self, route):
        """Handle route interception for adding headers and cookies"""
        # Add custom headers to make the request look more like a real browser
        headers = route.request.headers
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        headers['Accept-Language'] = 'en-US,en;q=0.9'
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'
        headers['Upgrade-Insecure-Requests'] = '1'
        headers['Sec-Fetch-Dest'] = 'document'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-Site'] = 'none'
        headers['Sec-Fetch-User'] = '?1'
        
        # Continue with the modified headers
        await route.continue_(headers=headers)
    
    async def _parse_robots_txt(self, url):
        """Parse robots.txt to respect crawling rules"""
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            # Use a simple request for robots.txt
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    user_agent=random.choice(self.user_agents)
                )
                
                response = await page.goto(robots_url, wait_until="networkidle")
                
                if response.status == 200:
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                    
                    # Parse the robots.txt content
                    self.robots_rules = {
                        'allowed': [],
                        'disallowed': [],
                        'crawl_delay': None
                    }
                    
                    current_agent = None
                    
                    for line in text.split('\n'):
                        line = line.strip()
                        
                        if not line or line.startswith('#'):
                            continue
                        
                        if line.lower().startswith('user-agent:'):
                            agent = line.split(':', 1)[1].strip()
                            current_agent = agent
                        
                        elif line.lower().startswith('allow:') and (current_agent == '*' or current_agent == 'Crowl'):
                            path = line.split(':', 1)[1].strip()
                            self.robots_rules['allowed'].append(path)
                        
                        elif line.lower().startswith('disallow:') and (current_agent == '*' or current_agent == 'Crowl'):
                            path = line.split(':', 1)[1].strip()
                            self.robots_rules['disallowed'].append(path)
                        
                        elif line.lower().startswith('crawl-delay:') and (current_agent == '*' or current_agent == 'Crowl'):
                            delay = line.split(':', 1)[1].strip()
                            try:
                                self.robots_rules['crawl_delay'] = float(delay)
                            except ValueError:
                                pass
                
                await browser.close()
                
                logger.info(f"Parsed robots.txt: {len(self.robots_rules['allowed'])} allowed paths, "
                           f"{len(self.robots_rules['disallowed'])} disallowed paths")
        
        except Exception as e:
            logger.error(f"Error parsing robots.txt: {str(e)}")
    
    def _is_allowed(self, url):
        """Check if a URL is allowed by robots.txt rules"""
        if not self.robots_rules:
            return True
        
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Check if the path is explicitly allowed
        for allowed_path in self.robots_rules.get('allowed', []):
            if allowed_path == '/' or path.startswith(allowed_path.rstrip('*')):
                return True
        
        # Check if the path is explicitly disallowed
        for disallowed_path in self.robots_rules.get('disallowed', []):
            if disallowed_path == '/' or path.startswith(disallowed_path.rstrip('*')):
                return False
        
        # If not explicitly disallowed, it's allowed
        return True
    
    async def _crawl_page(self, page, url, depth, max_pages, max_depth, delay_range, referer):
        """
        Crawl a single page and extract data
        
        Args:
            page: Playwright page object
            url (str): URL to crawl
            depth (int): Current depth
            max_pages (int): Maximum number of pages to crawl
            max_depth (int): Maximum depth to crawl
            delay_range (tuple): Range of seconds to delay between requests
            referer (str): Referer URL
        """
        # Check if we've reached the maximum number of pages
        if len(self.visited_urls) >= max_pages:
            return
        
        # Check if we've reached the maximum depth
        if depth > max_depth:
            return
        
        # Check if we've already visited this URL
        if url in self.visited_urls:
            return
        
        # Check if the URL is allowed by robots.txt
        if not self._is_allowed(url):
            logger.info(f"Skipping disallowed URL: {url}")
            return
        
        # Add to visited URLs
        self.visited_urls.add(url)
        
        try:
            # Navigate to the URL with a timeout
            logger.info(f"Crawling: {url} (depth: {depth})")
            start_time = time.time()
            
            # Add random delay to avoid detection
            delay = random.uniform(delay_range[0], delay_range[1])
            await asyncio.sleep(delay)
            
            # Navigate to the page
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for the page to be fully loaded
            await page.wait_for_load_state("networkidle")
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Extract page data
            page_data = await self._extract_page_data(page, url, response, depth, referer, latency)
            self.urls_data.append(page_data)
            
            # Extract links if we haven't reached the maximum depth
            if depth < max_depth:
                links = await self._extract_links(page, url)
                
                # Add links to the links data
                for link in links:
                    self.links_data.append(link)
                
                # Crawl the extracted links
                for link in links:
                    target_url = link['target']
                    
                    # Only crawl internal links
                    if self._is_internal_link(url, target_url):
                        await self._crawl_page(page, target_url, depth + 1, max_pages, max_depth, delay_range, url)
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
    
    async def _extract_page_data(self, page, url, response, depth, referer, latency):
        """Extract data from a page"""
        # Get the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract basic page data
        title = await page.title()
        
        # Extract meta description
        meta_description = ''
        meta_desc_elem = await page.query_selector('meta[name="description"]')
        if meta_desc_elem:
            meta_description = await meta_desc_elem.get_attribute('content') or ''
        
        # Extract canonical URL
        canonical = ''
        canonical_elem = await page.query_selector('link[rel="canonical"]')
        if canonical_elem:
            canonical = await canonical_elem.get_attribute('href') or ''
        
        # Extract h1
        h1 = ''
        h1_elem = await page.query_selector('h1')
        if h1_elem:
            h1 = await h1_elem.inner_text() or ''
        
        # Extract text content
        text_content = soup.get_text()
        word_count = len(re.findall(r'\w+', text_content))
        
        # Detect language
        content_lang = 'unknown'
        try:
            content_lang = detect(text_content)
        except:
            pass
        
        # Create page data dictionary
        page_data = {
            'url': url,
            'response_code': response.status,
            'content_type': response.headers.get('content-type', ''),
            'level': depth,
            'referer': referer or '',
            'latency': latency,
            'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'title': title,
            'meta_description': meta_description,
            'canonical': canonical,
            'h1': h1,
            'wordcount': word_count,
            'content_lang': content_lang,
            'pagerank': 0  # Will be calculated later
        }
        
        return page_data
    
    async def _extract_links(self, page, source_url):
        """Extract links from a page"""
        links = []
        
        # Get all links on the page
        link_elements = await page.query_selector_all('a[href]')
        
        for link_elem in link_elements:
            try:
                # Get the href attribute
                href = await link_elem.get_attribute('href')
                
                # Skip empty links
                if not href:
                    continue
                
                # Normalize the URL
                target_url = urljoin(source_url, href)
                
                # Skip non-HTTP URLs
                if not target_url.startswith(('http://', 'https://')):
                    continue
                
                # Get the link text
                text = await link_elem.inner_text()
                text = text.strip() if text else ''
                
                # Check if the link has rel="nofollow"
                rel = await link_elem.get_attribute('rel')
                nofollow = rel and 'nofollow' in rel.lower()
                
                # Check if the link is disallowed by robots.txt
                disallow = not self._is_allowed(target_url)
                
                # Add the link to the list
                links.append({
                    'source': source_url,
                    'target': target_url,
                    'text': text,
                    'nofollow': nofollow,
                    'disallow': disallow
                })
            
            except Exception as e:
                logger.error(f"Error extracting link: {str(e)}")
        
        return links
    
    def _is_internal_link(self, source_url, target_url):
        """Check if a link is internal"""
        source_domain = urlparse(source_url).netloc
        target_domain = urlparse(target_url).netloc
        
        return source_domain == target_domain
    
    def _save_data(self):
        """Save the crawled data to CSV files"""
        # Save URLs data
        if self.urls_data:
            urls_df = pd.DataFrame(self.urls_data)
            urls_file = os.path.join(self.output_dir, self._get_domain_folder(), '_urls.csv')
            urls_df.to_csv(urls_file, index=False)
            logger.info(f"Saved {len(self.urls_data)} URLs to {urls_file}")
        
        # Save links data
        if self.links_data:
            links_df = pd.DataFrame(self.links_data)
            links_file = os.path.join(self.output_dir, self._get_domain_folder(), '_links.csv')
            links_df.to_csv(links_file, index=False)
            logger.info(f"Saved {len(self.links_data)} links to {links_file}")
