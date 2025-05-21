import os
import time
import random
import logging
import json
import pandas as pd
import re
import requests
import uuid
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from langdetect import detect
import networkx as nx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EcommerceCrawler')

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Edge/115.0.1901.188"
]

class EcommerceCrawler:
    """
    A specialized crawler for e-commerce websites that uses advanced techniques to handle JavaScript-heavy pages
    and implements enhanced anti-bot detection strategies.
    """

    def __init__(self, output_dir="ecommerce_data", stealth_mode=True):
        """
        Initialize the e-commerce crawler

        Args:
            output_dir (str): Directory to save output files
            stealth_mode (bool): Whether to use stealth mode to avoid detection
        """
        self.output_dir = output_dir
        self.stealth_mode = stealth_mode
        self.visited_urls = set()
        self.all_products = []
        self.all_links = []
        self.pages_data = []
        self.robots_data = None
        self.sitemaps = []
        self.crawlability_score = 0

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Initialize CSV files
        self.urls_file = os.path.join(output_dir, "_urls.csv")
        self.links_file = os.path.join(output_dir, "_links.csv")
        self.products_file = os.path.join(output_dir, "_products.csv")
        self.robots_file = os.path.join(output_dir, "_robots.json")

        if not os.path.exists(self.urls_file):
            pd.DataFrame(columns=[
                'url', 'response_code', 'content_type', 'level', 'referer', 'latency',
                'crawled_at', 'nb_title', 'title', 'nb_meta_robots', 'meta_robots',
                'meta_description', 'meta_viewport', 'meta_keywords', 'canonical',
                'prev', 'next', 'h1', 'nb_h1', 'nb_h2', 'wordcount', 'content',
                'content_lang', 'XRobotsTag', 'outlinks', 'http_date', 'size',
                'html_lang', 'hreflangs', 'microdata', 'extractors', 'request_headers',
                'response_headers', 'redirect', 'pagerank'
            ]).to_csv(self.urls_file, index=False)

        if not os.path.exists(self.links_file):
            pd.DataFrame(columns=[
                'source', 'target', 'text', 'nofollow', 'disallow', 'priority'
            ]).to_csv(self.links_file, index=False)

        if not os.path.exists(self.products_file):
            pd.DataFrame(columns=[
                'title', 'url', 'price', 'original_price', 'rating', 'reviews_count',
                'availability', 'brand', 'asin', 'image_url'
            ]).to_csv(self.products_file, index=False)

    def analyze_robots_txt(self, domain="www.amazon.com"):
        """
        Analyze robots.txt file for crawlability insights

        Args:
            domain (str): Domain to analyze

        Returns:
            dict: Dictionary containing robots.txt analysis
        """
        robots_url = f"https://{domain}/robots.txt"

        try:
            # Create a stealth session
            session = self.create_stealth_session()

            # Fetch robots.txt
            response = session.get(robots_url, timeout=30)

            if response.status_code == 200:
                content = response.text

                # Parse robots.txt
                crawl_delay = None
                sitemaps = []
                disallowed_paths = []
                allowed_paths = []

                # Process each line
                for line in content.split('\n'):
                    line = line.strip().lower()

                    if line.startswith('crawl-delay:'):
                        try:
                            crawl_delay = float(line.split(':', 1)[1].strip())
                        except:
                            pass

                    elif line.startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemaps.append(sitemap_url)

                    elif line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            disallowed_paths.append(path)

                    elif line.startswith('allow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            allowed_paths.append(path)

                # Calculate crawlability score
                total_paths = len(disallowed_paths) + len(allowed_paths)
                if total_paths > 0:
                    crawlability_score = (len(allowed_paths) / total_paths) * 100
                else:
                    crawlability_score = 100  # No restrictions

                # Adjust for crawl delay
                if crawl_delay:
                    if crawl_delay > 5:
                        crawlability_score *= 0.7  # Significant delay
                    elif crawl_delay > 2:
                        crawlability_score *= 0.9  # Moderate delay

                # Store results
                robots_data = {
                    'url': robots_url,
                    'status': 'success',
                    'crawl_delay': crawl_delay,
                    'sitemaps': sitemaps,
                    'disallowed_paths': disallowed_paths,
                    'allowed_paths': allowed_paths,
                    'crawlability_score': crawlability_score,
                    'content': content
                }

                # Save to file
                with open(self.robots_file, 'w') as f:
                    json.dump(robots_data, f, indent=2)

                # Store in instance
                self.robots_data = robots_data
                self.sitemaps = sitemaps
                self.crawlability_score = crawlability_score

                return robots_data
            else:
                robots_data = {
                    'url': robots_url,
                    'status': 'error',
                    'error': f"Failed to fetch robots.txt: {response.status_code}",
                    'crawlability_score': 100  # No robots.txt = no restrictions
                }

                # Save to file
                with open(self.robots_file, 'w') as f:
                    json.dump(robots_data, f, indent=2)

                # Store in instance
                self.robots_data = robots_data
                self.crawlability_score = 100

                return robots_data

        except Exception as e:
            robots_data = {
                'url': robots_url,
                'status': 'error',
                'error': f"Error analyzing robots.txt: {str(e)}",
                'crawlability_score': 100  # Error = assume no restrictions
            }

            # Save to file
            with open(self.robots_file, 'w') as f:
                json.dump(robots_data, f, indent=2)

            # Store in instance
            self.robots_data = robots_data
            self.crawlability_score = 100

            return robots_data

    def analyze_sitemap(self, sitemap_url=None):
        """
        Analyze sitemap for crawlability insights

        Args:
            sitemap_url (str): URL of the sitemap to analyze

        Returns:
            dict: Dictionary containing sitemap analysis
        """
        if not sitemap_url and self.sitemaps:
            sitemap_url = self.sitemaps[0]
        elif not sitemap_url:
            sitemap_url = "https://www.amazon.com/sitemap.xml"

        try:
            # Create a stealth session
            session = self.create_stealth_session()

            # Fetch sitemap
            response = session.get(sitemap_url, timeout=30)

            if response.status_code == 200:
                content = response.text

                # Parse sitemap
                soup = BeautifulSoup(content, 'xml')

                # Check if it's a sitemap index
                is_index = len(soup.find_all('sitemapindex')) > 0

                if is_index:
                    # Extract child sitemaps
                    child_sitemaps = []
                    for sitemap in soup.find_all('sitemap'):
                        loc = sitemap.find('loc')
                        if loc:
                            child_sitemaps.append(loc.text)

                    return {
                        'url': sitemap_url,
                        'status': 'success',
                        'type': 'index',
                        'child_sitemaps': child_sitemaps,
                        'count': len(child_sitemaps)
                    }
                else:
                    # Extract URLs
                    urls = []
                    for url in soup.find_all('url'):
                        loc = url.find('loc')
                        if loc:
                            urls.append(loc.text)

                    return {
                        'url': sitemap_url,
                        'status': 'success',
                        'type': 'urlset',
                        'urls': urls[:100],  # Limit to 100 URLs for memory
                        'count': len(urls)
                    }
            else:
                return {
                    'url': sitemap_url,
                    'status': 'error',
                    'error': f"Failed to fetch sitemap: {response.status_code}"
                }

        except Exception as e:
            return {
                'url': sitemap_url,
                'status': 'error',
                'error': f"Error analyzing sitemap: {str(e)}"
            }

    def create_stealth_session(self):
        """
        Create a more stealthy browser session to avoid detection

        Returns:
            requests.Session: Session with stealth settings
        """
        # Rotate user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 OPR/78.0.4093.112"
        ]

        # Rotate between different request headers
        header_templates = [
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Pragma": "no-cache"
            }
        ]

        # Select random user agent and headers
        user_agent = random.choice(user_agents)
        headers = random.choice(header_templates)
        headers["User-Agent"] = user_agent

        # Create session with cookies enabled
        session = requests.Session()
        session.headers.update(headers)

        # Add random cookies to appear more like a real browser
        cookies = {
            "session-id": f"{random.randint(100000000, 999999999)}",
            "session-token": f"{uuid.uuid4()}",
            "ubid-main": f"{random.randint(100000000, 999999999)}"
        }
        session.cookies.update(cookies)

        return session

    def fetch_page(self, url, referer=None, level=0, delay_range=(2, 5)):
        """
        Fetch a page using requests with enhanced stealth techniques

        Args:
            url (str): The URL to fetch
            referer (str): The referer URL
            level (int): The crawl depth level
            delay_range (tuple): Range of delay between requests (min, max)

        Returns:
            dict: Dictionary containing HTML content and page metadata
        """
        logger.info(f"Fetching page: {url}")
        start_time = time.time()

        # Add random delay to avoid detection
        delay = random.uniform(delay_range[0], delay_range[1])
        time.sleep(delay)

        # Create a stealth session
        session = self.create_stealth_session()

        # Add referer if provided
        if referer:
            session.headers['Referer'] = referer

        try:
            # Make the request with a timeout and exponential backoff retry
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    # Add random query parameters to avoid caching
                    params = {}
                    if '?' not in url:
                        params = {
                            '_': int(time.time() * 1000),
                            'rand': random.randint(1000, 9999)
                        }

                    # Make the request
                    response = session.get(url, params=params, timeout=60)

                    # Check for CAPTCHA or access denied
                    if "captcha" in response.text.lower() or "robot" in response.text.lower():
                        logger.warning(f"Possible CAPTCHA or access denied on {url}")
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            logger.info(f"Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                            # Create a new session with different fingerprint
                            session = self.create_stealth_session()
                            continue

                    # Break the loop if request was successful
                    break

                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise

            # Get the HTML content
            html = response.text

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title = soup.title.text.strip() if soup.title else ""

            # Extract metadata
            meta_description = ""
            meta_desc_elem = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_elem and meta_desc_elem.get('content'):
                meta_description = meta_desc_elem['content']

            meta_robots = ""
            meta_robots_elem = soup.find('meta', attrs={'name': 'robots'})
            if meta_robots_elem and meta_robots_elem.get('content'):
                meta_robots = meta_robots_elem['content']

            meta_viewport = ""
            meta_viewport_elem = soup.find('meta', attrs={'name': 'viewport'})
            if meta_viewport_elem and meta_viewport_elem.get('content'):
                meta_viewport = meta_viewport_elem['content']

            meta_keywords = ""
            meta_keywords_elem = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords_elem and meta_keywords_elem.get('content'):
                meta_keywords = meta_keywords_elem['content']

            canonical = ""
            canonical_elem = soup.find('link', attrs={'rel': 'canonical'})
            if canonical_elem and canonical_elem.get('href'):
                canonical = canonical_elem['href']

            # Extract h1 tags
            h1_elems = soup.find_all('h1')
            h1_texts = [h1.text.strip() for h1 in h1_elems]

            # Count h2 tags
            h2_count = len(soup.find_all('h2'))

            # Extract content for language detection
            content_text = soup.get_text(separator=' ', strip=True)

            # Detect language
            content_lang = ""
            try:
                if content_text and len(content_text) > 100:
                    content_lang = detect(content_text[:1000])
            except:
                pass

            # Get HTML lang attribute
            html_lang = ""
            html_elem = soup.find('html')
            if html_elem and html_elem.get('lang'):
                html_lang = html_elem['lang']

            # Calculate latency and size
            latency = time.time() - start_time
            size = len(html)

            # Get response headers
            response_headers = response.headers

            # Create page data
            page_data = {
                'url': url,
                'response_code': response.status_code,
                'content_type': response_headers.get('content-type', ''),
                'level': level,
                'referer': referer or '',
                'latency': latency,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'nb_title': 1 if title else 0,
                'title': title,
                'nb_meta_robots': 1 if meta_robots else 0,
                'meta_robots': meta_robots,
                'meta_description': meta_description,
                'meta_viewport': meta_viewport,
                'meta_keywords': meta_keywords,
                'canonical': canonical,
                'prev': '',
                'next': '',
                'h1': h1_texts[0] if h1_texts else '',
                'nb_h1': len(h1_texts),
                'nb_h2': h2_count,
                'wordcount': len(content_text.split()),
                'content': content_text[:1000],  # Truncate for storage
                'content_lang': content_lang,
                'XRobotsTag': response_headers.get('X-Robots-Tag', ''),
                'outlinks': 0,  # Will be updated later
                'http_date': response_headers.get('date', ''),
                'size': size,
                'html_lang': html_lang,
                'hreflangs': [],
                'microdata': {},
                'extractors': {},
                'request_headers': dict(session.headers),
                'response_headers': dict(response_headers),
                'redirect': response.url if response.url != url else '',
                'pagerank': 0.0,  # Will be calculated later
                'html': html,  # Store the full HTML for processing
                'soup': soup  # Store the parsed soup for processing
            }

            return page_data

        except Exception as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return {
                'url': url,
                'response_code': 0,
                'error': str(e),
                'level': level,
                'referer': referer or '',
                'latency': time.time() - start_time,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def extract_products(self, html):
        """
        Extract product information from Amazon search results page

        Args:
            html (str): HTML content of the page

        Returns:
            list: List of product dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Log the extraction attempt
        logger.info(f"Attempting to extract products from page")

        # Try multiple selectors to find product items (Amazon changes their HTML structure frequently)
        selectors = [
            '.s-result-item[data-asin]:not([data-asin=""])',
            '.sg-col-inner .a-section.a-spacing-medium',
            '.s-result-list .s-result-item',
            '.s-search-results .s-result-item',
            '.s-main-slot .s-result-item',
            '[data-component-type="s-search-result"]'
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"Found {len(items)} products using selector: {selector}")
                break

        # If no products found with selectors, try to find any product-like elements
        if not items:
            logger.warning("No products found with standard selectors, trying alternative methods")
            # Look for product titles as a fallback
            title_elements = soup.select('h2 a span, .a-size-medium.a-color-base.a-text-normal, .a-size-base-plus.a-color-base.a-text-normal')
            if title_elements:
                logger.info(f"Found {len(title_elements)} potential products by title elements")
                # Create synthetic items from title elements
                items = [elem.parent.parent for elem in title_elements if elem.parent and elem.parent.parent]

        # If this is a product detail page, create a single product item
        if '/dp/' in str(soup):
            logger.info("Detected product detail page, extracting single product")
            items = [soup]  # Use the entire soup as the item

        for item in items:
            try:
                # Extract ASIN (Amazon Standard Identification Number)
                asin = item.get('data-asin', '')
                if not asin:
                    asin_elem = item.select_one('[data-asin]')
                    if asin_elem:
                        asin = asin_elem.get('data-asin', '')
                    # Try to extract from URL if on product page
                    elif '/dp/' in str(item):
                        asin_match = re.search(r'/dp/([A-Z0-9]{10})', str(item))
                        if asin_match:
                            asin = asin_match.group(1)

                # Extract title - try multiple selectors
                title = None
                title_selectors = [
                    'h2 a span',
                    '.a-size-medium.a-color-base.a-text-normal',
                    '.a-size-base-plus.a-color-base.a-text-normal',
                    '#productTitle',
                    '.product-title-word-break'
                ]

                for selector in title_selectors:
                    title_elem = item.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break

                # Extract link - try multiple selectors
                link = None
                link_selectors = [
                    'h2 a',
                    '.a-link-normal.s-no-outline',
                    '.a-link-normal.s-underline-text',
                    '.a-link-normal.a-text-normal'
                ]

                for selector in link_selectors:
                    link_elem = item.select_one(selector)
                    if link_elem and link_elem.has_attr('href'):
                        link = link_elem['href']
                        break

                # If on product page, use current URL
                if not link and '/dp/' in str(item):
                    link_match = re.search(r'(https://www\.amazon\.com/[^"\']+/dp/[A-Z0-9]{10}[^"\']*)', str(item))
                    if link_match:
                        link = link_match.group(1)

                # Extract price - try multiple selectors
                price = None
                price_selectors = [
                    '.a-price .a-offscreen',
                    '.a-price',
                    '.a-color-price',
                    '#priceblock_ourprice',
                    '#priceblock_dealprice',
                    '.a-price-whole'
                ]

                for selector in price_selectors:
                    price_elem = item.select_one(selector)
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                        break

                # Extract original price (if on sale)
                original_price = None
                original_price_selectors = [
                    '.a-price.a-text-price .a-offscreen',
                    '.a-price.a-text-price',
                    '.a-text-price'
                ]

                for selector in original_price_selectors:
                    original_price_elem = item.select_one(selector)
                    if original_price_elem:
                        original_price = original_price_elem.get_text(strip=True)
                        break

                # Extract rating
                rating = None
                rating_selectors = [
                    'i.a-icon-star-small',
                    'i.a-icon-star',
                    '.a-icon-alt',
                    '#acrPopover'
                ]

                for selector in rating_selectors:
                    rating_elem = item.select_one(selector)
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating_match = re.search(r'(\d+\.\d+|\d+)', rating_text)
                        if rating_match:
                            rating = rating_match.group(1)
                            break

                # Extract reviews count
                reviews_count = None
                reviews_selectors = [
                    'span[aria-label$="stars"] + span',
                    '.a-size-base.s-underline-text',
                    '#acrCustomerReviewText',
                    '.a-link-normal.a-text-normal .a-size-base'
                ]

                for selector in reviews_selectors:
                    reviews_elem = item.select_one(selector)
                    if reviews_elem:
                        reviews_text = reviews_elem.get_text(strip=True).replace(',', '')
                        reviews_match = re.search(r'(\d+)', reviews_text)
                        if reviews_match:
                            reviews_count = reviews_match.group(1)
                            break

                # Extract availability
                availability = None
                availability_selectors = [
                    '.a-color-success',
                    '#availability',
                    '.a-color-price'
                ]

                for selector in availability_selectors:
                    availability_elem = item.select_one(selector)
                    if availability_elem:
                        availability = availability_elem.get_text(strip=True)
                        break

                # Extract image URL
                image_url = None
                image_selectors = [
                    'img.s-image',
                    '#landingImage',
                    '#imgBlkFront',
                    '.a-dynamic-image'
                ]

                for selector in image_selectors:
                    img_elem = item.select_one(selector)
                    if img_elem and img_elem.has_attr('src'):
                        image_url = img_elem['src']
                        break

                if title and link:
                    # Ensure link is absolute
                    if link.startswith('/'):
                        link = "https://www.amazon.com" + link

                    # Extract brand from title (usually the first word)
                    brand = title.split(' ')[0] if title else None

                    # Create product dictionary
                    product = {
                        'title': title,
                        'url': link,
                        'price': price,
                        'original_price': original_price,
                        'rating': rating,
                        'reviews_count': reviews_count,
                        'availability': availability,
                        'image_url': image_url,
                        'asin': asin,
                        'brand': brand
                    }

                    results.append(product)
            except Exception as e:
                logger.error(f"Error extracting product: {str(e)}")

        return results

    def extract_links(self, html, base_url):
        """
        Extract all links from a page

        Args:
            html (str): HTML content of the page
            base_url (str): Base URL for resolving relative links

        Returns:
            list: List of link dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)

            # Skip empty links, javascript links, and anchors
            if not href or href.startswith('javascript:') or href == '#':
                continue

            # Resolve relative URLs
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)

            # Only include Amazon links
            if 'amazon.com' in href:
                links.append({
                    'url': href,
                    'text': text if text else '',
                    'nofollow': 'nofollow' in a_tag.get('rel', []),
                    'disallow': False  # Will be updated based on robots.txt
                })

        return links

    def crawl(self, query, max_pages=5, max_depth=2, delay_range=(2, 5)):
        """
        Intelligent crawl of e-commerce search results and product pages with adaptive depth control

        Args:
            query (str): Search query
            max_pages (int): Maximum number of pages to crawl
            max_depth (int): Maximum depth to crawl
            delay_range (tuple): Range of delay between requests (min, max)

        Returns:
            dict: Dictionary containing crawl results
        """
        # Reset data structures
        self.visited_urls = set()
        self.all_products = []
        self.all_links = []
        self.pages_data = []

        # Track page scores to prioritize high-value pages
        page_scores = {}

        # Start with search URL
        search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"

        # Priority queue: (priority, (url, referer, level))
        # Higher priority = more important to crawl
        urls_to_visit = [(100, (search_url, None, 0))]  # Start with high priority

        # Crawl progress tracking
        page_count = 0
        start_time = time.time()
        crawl_progress = []

        # Log crawl start
        logger.info(f"Starting intelligent crawl for query: {query}")
        logger.info(f"Max pages: {max_pages}, Max depth: {max_depth}")

        while urls_to_visit and page_count < max_pages:
            # Get highest priority URL
            _, (current_url, referer, level) = max(urls_to_visit, key=lambda x: x[0])
            urls_to_visit.remove((_, (current_url, referer, level)))

            # Skip if already visited or exceeds max depth
            if current_url in self.visited_urls or level > max_depth:
                continue

            # Add to visited set
            self.visited_urls.add(current_url)

            try:
                # Fetch page with adaptive delay based on importance
                current_priority = _ if _ else 50
                adaptive_delay = (
                    (delay_range[1] - delay_range[0]) * (current_priority / 100) + delay_range[0]
                )

                page_data = self.fetch_page(
                    current_url,
                    referer=referer,
                    level=level,
                    delay_range=(adaptive_delay, adaptive_delay + 1)
                )

                html = page_data.pop('html', '')  # Remove HTML from page_data to save memory
                soup = page_data.pop('soup', None)  # Remove soup from page_data to save memory

                # Extract products if it's a search or product page
                products = []
                # More comprehensive check for product pages
                is_product_page = any(pattern in current_url for pattern in [
                    's?k=', '/dp/', '/gp/product/', '/gp/aw/d/', '/product/', '/slp/product/'
                ])

                if is_product_page:
                    logger.info(f"Extracting products from {current_url}")
                    products = self.extract_products(html)
                    logger.info(f"Found {len(products)} products on page")

                    # Only add unique products based on ASIN
                    existing_asins = {p.get('asin', '') for p in self.all_products}
                    new_products = [p for p in products if p.get('asin', '') and p.get('asin', '') not in existing_asins]

                    if new_products:
                        logger.info(f"Adding {len(new_products)} new unique products")
                        self.all_products.extend(new_products)
                    else:
                        logger.info("No new unique products found")

                # Calculate page score based on content value
                page_score = 0

                # Higher score for pages with products
                page_score += len(products) * 10

                # Higher score for pages with good titles and descriptions
                if page_data.get('title'):
                    page_score += min(len(page_data['title']), 100) / 10

                if page_data.get('meta_description'):
                    page_score += min(len(page_data['meta_description']), 200) / 20

                # Store page score
                page_scores[current_url] = page_score

                # Extract all links
                links = self.extract_links(html, current_url)
                page_data['outlinks'] = len(links)

                # Prioritize links based on URL patterns and parent page score
                prioritized_links = []
                for link in links:
                    # Base priority
                    priority = 0

                    # URL pattern priorities
                    if '/dp/' in link['url']:  # Product page
                        priority += 80
                    elif 's?k=' in link['url']:  # Search results
                        priority += 70
                    elif '/gp/bestsellers/' in link['url']:  # Best sellers
                        priority += 60
                    elif '/gp/new-releases/' in link['url']:  # New releases
                        priority += 50
                    elif '/gp/goldbox/' in link['url']:  # Deals
                        priority += 40
                    else:
                        priority += 10

                    # Adjust priority based on parent page score
                    priority += min(page_scores.get(current_url, 0) * 0.2, 20)

                    # Reduce priority based on depth
                    priority -= level * 10

                    # Reduce priority for nofollow or disallowed links
                    if link['nofollow'] or link['disallow']:
                        priority -= 30

                    # Add to prioritized links
                    prioritized_links.append((priority, (link['url'], current_url, level + 1)))

                    # Add to all links for visualization
                    self.all_links.append({
                        'source': current_url,
                        'target': link['url'],
                        'text': link['text'],
                        'nofollow': link['nofollow'],
                        'disallow': link['disallow'],
                        'priority': priority
                    })

                # Add prioritized links to visit queue if they meet criteria
                for priority, (url, ref, lvl) in prioritized_links:
                    if (url not in self.visited_urls and
                        lvl <= max_depth and
                        len(urls_to_visit) < max_pages * 2):  # Allow queue to be larger than max_pages
                        urls_to_visit.append((priority, (url, ref, lvl)))

                # Add page data
                self.pages_data.append(page_data)

                # Append to CSV files
                urls_df = pd.DataFrame([page_data])
                urls_df.to_csv(self.urls_file, mode='a', header=False, index=False)

                # Update links file
                links_df = pd.DataFrame(self.all_links)
                if not links_df.empty:
                    links_df.to_csv(self.links_file, mode='w', header=True, index=False)

                # Update products file
                if self.all_products:
                    try:
                        logger.info(f"Saving {len(self.all_products)} products to {self.products_file}")
                        products_df = pd.DataFrame(self.all_products)

                        # Ensure the output directory exists
                        os.makedirs(os.path.dirname(self.products_file), exist_ok=True)

                        # Save the products to CSV
                        products_df.to_csv(self.products_file, mode='w', header=True, index=False)
                        logger.info(f"Successfully saved products to {self.products_file}")
                    except Exception as e:
                        logger.error(f"Error saving products to CSV: {str(e)}")

                # Increment page count
                page_count += 1

                # Log progress
                logger.info(f"Crawled {page_count}/{max_pages} pages, found {len(self.all_products)} products")

            except Exception as e:
                logger.error(f"Error crawling {current_url}: {str(e)}")

        # Calculate PageRank
        self._calculate_pagerank()

        # Create sitemap and graph data
        sitemap = [{
            "page": url,
            "links": [link['target'] for link in self.all_links if link['source'] == url],
            "title": next((page['title'] for page in self.pages_data if page['url'] == url), ""),
            "score": page_scores.get(url, 0)
        } for url in self.visited_urls]

        graph = {
            "nodes": [{"id": url, "group": 1 if 's?k=' in url else 2} for url in self.visited_urls],
            "links": [{"source": link['source'], "target": link['target'], "value": 1} for link in self.all_links
                     if link['source'] in self.visited_urls and link['target'] in self.visited_urls]
        }

        # Save sitemap and graph data
        with open(os.path.join(self.output_dir, "sitemap.json"), "w") as f:
            json.dump(sitemap, f, indent=2)

        with open(os.path.join(self.output_dir, "network_graph.json"), "w") as f:
            json.dump(graph, f, indent=2)

        logger.info(f"Crawl completed. Visited {len(self.visited_urls)} pages, found {len(self.all_products)} products.")

        # Log the paths to the saved files
        logger.info(f"Products saved to: {self.products_file}")
        logger.info(f"URLs saved to: {self.urls_file}")
        logger.info(f"Links saved to: {self.links_file}")

        # Check if files were created successfully
        products_file_exists = os.path.exists(self.products_file)
        urls_file_exists = os.path.exists(self.urls_file)
        links_file_exists = os.path.exists(self.links_file)

        logger.info(f"Products file exists: {products_file_exists}")
        logger.info(f"URLs file exists: {urls_file_exists}")
        logger.info(f"Links file exists: {links_file_exists}")

        # Get file sizes
        products_file_size = os.path.getsize(self.products_file) if products_file_exists else 0
        urls_file_size = os.path.getsize(self.urls_file) if urls_file_exists else 0
        links_file_size = os.path.getsize(self.links_file) if links_file_exists else 0

        logger.info(f"Products file size: {products_file_size} bytes")
        logger.info(f"URLs file size: {urls_file_size} bytes")
        logger.info(f"Links file size: {links_file_size} bytes")

        return {
            'visited_urls': list(self.visited_urls),
            'products': self.all_products,
            'links': self.all_links,
            'pages': self.pages_data,
            'sitemap': sitemap,
            'graph': graph,
            'files': {
                'products_file': self.products_file,
                'urls_file': self.urls_file,
                'links_file': self.links_file,
                'products_file_exists': products_file_exists,
                'products_file_size': products_file_size,
                'products_count': len(self.all_products)
            }
        }

    def _calculate_pagerank(self):
        """Calculate PageRank for the crawled pages and update the URLs file"""
        if not self.all_links:
            return

        # Create a directed graph
        G = nx.DiGraph()

        # Add edges from the links
        for link in self.all_links:
            G.add_edge(link['source'], link['target'])

        # Calculate PageRank
        pagerank = nx.pagerank(G, alpha=0.85)

        # Read the URLs file
        urls_df = pd.read_csv(self.urls_file)

        # Update the PageRank values
        urls_df['pagerank'] = urls_df['url'].map(pagerank).fillna(0)

        # Save the updated URLs file
        urls_df.to_csv(self.urls_file, index=False)

        logger.info(f"Updated PageRank values in {self.urls_file}")

# Example usage
def main():
    crawler = EcommerceCrawler(output_dir="ecommerce_data")
    results = crawler.crawl("laptop", max_pages=5, max_depth=2)
    print(f"Crawled {len(results['visited_urls'])} pages")
    print(f"Found {len(results['products'])} products")

if __name__ == "__main__":
    main()