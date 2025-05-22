"""
Simplified Amazon crawler for Streamlit Cloud that uses requests instead of Playwright.
This crawler is designed to work in environments where browser automation is not available.
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os
import pandas as pd
import uuid
import logging
from urllib.parse import urlparse, urljoin
import json
from datetime import datetime
import networkx as nx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CloudCrawler')

class CloudCrawler:
    """
    A simplified crawler for Streamlit Cloud that uses requests instead of Playwright.
    """

    def __init__(self, output_dir='ecommerce_data', base_url='https://www.amazon.com'):
        """
        Initialize the cloud crawler

        Args:
            output_dir (str): Directory to save output files
            base_url (str): Base URL for the crawler
        """
        self.output_dir = output_dir
        self.base_url = base_url
        self.visited_urls = set()
        self.all_products = []
        self.all_links = []
        self.pages_data = []

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # File paths
        self.urls_file = os.path.join(output_dir, "_urls.csv")
        self.links_file = os.path.join(output_dir, "_links.csv")
        self.products_file = os.path.join(output_dir, "_products.csv")

        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]

        # Proxies for rotation (add your own proxies here)
        self.proxies = [
            # Format: 'http://username:password@ip:port'
            # Free proxies can be found at: https://free-proxy-list.net/
            # For production use, consider a paid proxy service
        ]

    def create_stealth_session(self):
        """
        Create a requests session with stealth settings to avoid detection

        Returns:
            requests.Session: Session with stealth settings
        """
        # Create session
        session = requests.Session()

        # Set random user agent
        user_agent = random.choice(self.user_agents)

        # Set headers to mimic a real browser
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
            'DNT': '1'  # Do Not Track
        }

        session.headers.update(headers)

        # Add random cookies to appear more like a real browser
        cookies = {
            'session-id': f"{random.randint(100000000, 999999999)}",
            'session-token': f"{uuid.uuid4()}",
            'ubid-main': f"{random.randint(100000000, 999999999)}"
        }
        session.cookies.update(cookies)

        # Add a random proxy if available
        if self.proxies:
            proxy = random.choice(self.proxies)
            session.proxies = {
                'http': proxy,
                'https': proxy
            }

        return session

    def fetch_page(self, url, referer=None, delay_range=(2, 5)):
        """
        Fetch a page using requests with stealth techniques

        Args:
            url (str): URL to fetch
            referer (str): Referer URL
            delay_range (tuple): Range of delay between requests (min, max)

        Returns:
            dict: Page data including HTML content
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

        # Maximum retries
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
                response = session.get(url, params=params, timeout=30)

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

            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    # Create a new session with different fingerprint
                    session = self.create_stealth_session()
                else:
                    # Return empty data if all retries failed
                    return {
                        'url': url,
                        'html': '',
                        'title': '',
                        'meta_description': '',
                        'status_code': 0,
                        'latency': 0,
                        'crawled_at': datetime.now().isoformat()
                    }

        # Calculate latency
        latency = time.time() - start_time

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title and meta description
        title = soup.title.string if soup.title else ''
        meta_description = ''
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag and 'content' in meta_tag.attrs:
            meta_description = meta_tag['content']

        # Return page data
        return {
            'url': url,
            'html': response.text,
            'title': title,
            'meta_description': meta_description,
            'status_code': response.status_code,
            'latency': latency,
            'crawled_at': datetime.now().isoformat()
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

                # Create product dictionary
                product = {
                    'title': title,
                    'url': link if link and link.startswith('http') else urljoin(self.base_url, link) if link else '',
                    'price': price,
                    'original_price': original_price,
                    'rating': rating,
                    'reviews_count': reviews_count,
                    'availability': availability,
                    'image_url': image_url,
                    'asin': asin
                }

                # Only add products with title and URL
                if product['title'] and product['url']:
                    results.append(product)

            except Exception as e:
                logger.error(f"Error extracting product: {str(e)}")

        logger.info(f"Extracted {len(results)} products")
        return results

    def extract_links(self, html, base_url):
        """
        Extract links from a page

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
                    'source': base_url,
                    'target': href,
                    'text': text if text else '',
                    'nofollow': False
                })

        return links

    def crawl(self, query, max_pages=10, max_depth=2, delay_range=(2, 5)):
        """
        Crawl Amazon search results

        Args:
            query (str): Search query
            max_pages (int): Maximum number of pages to crawl
            max_depth (int): Maximum crawl depth
            delay_range (tuple): Range of delay between requests (min, max)

        Returns:
            dict: Dictionary containing crawl results
        """
        # Reset data structures
        self.visited_urls = set()
        self.all_products = []
        self.all_links = []
        self.pages_data = []

        # Start with search URL
        search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        urls_to_visit = [(search_url, None, 0)]  # (url, referer, depth)

        # Crawl progress tracking
        page_count = 0
        start_time = time.time()

        # Log crawl start
        logger.info(f"Starting cloud crawl for query: {query}")
        logger.info(f"Max pages: {max_pages}, Max depth: {max_depth}")

        # Create a simple sitemap and graph for visualization
        sitemap = {'nodes': [], 'links': []}
        graph = nx.DiGraph()

        # Add the root node
        root_id = 'root'
        sitemap['nodes'].append({
            'id': root_id,
            'name': 'Amazon',
            'url': 'https://www.amazon.com',
            'level': 0
        })
        graph.add_node(root_id, name='Amazon', url='https://www.amazon.com', level=0)

        # Main crawl loop
        while urls_to_visit and page_count < max_pages:
            # Get the next URL to visit
            current_url, referer, level = urls_to_visit.pop(0)

            # Skip if already visited or too deep
            if current_url in self.visited_urls or level > max_depth:
                continue

            # Mark as visited
            self.visited_urls.add(current_url)

            # Increment page count
            page_count += 1

            try:
                # Fetch page
                page_data = self.fetch_page(
                    current_url,
                    referer=referer,
                    delay_range=delay_range
                )

                html = page_data.pop('html')  # Remove HTML from page_data to save memory

                # Extract products if it's a search or product page
                products = []
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

                # Extract links
                links = self.extract_links(html, current_url)
                self.all_links.extend(links)

                # Add page to pages data
                self.pages_data.append(page_data)

                # Add node to sitemap and graph
                node_id = f"page_{page_count}"
                sitemap['nodes'].append({
                    'id': node_id,
                    'name': page_data['title'][:30] + '...' if len(page_data['title']) > 30 else page_data['title'],
                    'url': current_url,
                    'level': level
                })
                graph.add_node(node_id, name=page_data['title'], url=current_url, level=level)

                # Add link from referer to current page
                if referer:
                    # Find the referer node
                    referer_node = None
                    for node in sitemap['nodes']:
                        if node['url'] == referer:
                            referer_node = node['id']
                            break

                    if referer_node:
                        sitemap['links'].append({
                            'source': referer_node,
                            'target': node_id
                        })
                        graph.add_edge(referer_node, node_id)
                else:
                    # Link from root if no referer
                    sitemap['links'].append({
                        'source': root_id,
                        'target': node_id
                    })
                    graph.add_edge(root_id, node_id)

                # Add new URLs to visit
                for link in links:
                    target_url = link['target']

                    # Only add Amazon product or search pages
                    if 'amazon.com' in target_url and (
                        '/dp/' in target_url or
                        's?k=' in target_url or
                        '/gp/product/' in target_url
                    ):
                        if target_url not in self.visited_urls:
                            urls_to_visit.append((target_url, current_url, level + 1))

                # Log progress
                elapsed = time.time() - start_time
                logger.info(f"Crawled {page_count}/{max_pages} pages, {len(self.all_products)} products, {elapsed:.1f}s elapsed")

            except Exception as e:
                logger.error(f"Error crawling {current_url}: {str(e)}")

        # Save results to files if output directory exists
        try:
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

            # Update URLs file
            if self.pages_data:
                try:
                    urls_df = pd.DataFrame(self.pages_data)
                    urls_df.to_csv(self.urls_file, mode='w', header=True, index=False)
                except Exception as e:
                    logger.error(f"Error saving URLs to CSV: {str(e)}")

            # Update links file
            if self.all_links:
                try:
                    links_df = pd.DataFrame(self.all_links)
                    links_df.to_csv(self.links_file, mode='w', header=True, index=False)
                except Exception as e:
                    logger.error(f"Error saving links to CSV: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")

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

    def analyze_robots_txt(self):
        """
        Analyze robots.txt file for crawlability assessment

        Returns:
            dict: Dictionary containing robots.txt analysis
        """
        logger.info("Analyzing robots.txt file")

        try:
            # Create a stealth session
            session = self.create_stealth_session()

            # Fetch robots.txt
            robots_url = urljoin(self.base_url, '/robots.txt')
            response = session.get(robots_url, timeout=30)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch robots.txt: {response.status_code}")
                return {
                    'status': 'error',
                    'message': f"Failed to fetch robots.txt: {response.status_code}",
                    'crawlability_score': 50,  # Neutral score
                    'disallowed_paths': [],
                    'allowed_paths': [],
                    'sitemaps': [],
                    'crawl_delay': None
                }

            # Parse robots.txt content
            content = response.text

            # Extract disallowed paths
            disallowed_paths = []
            for line in content.split('\n'):
                if line.lower().startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        disallowed_paths.append(path)

            # Extract allowed paths
            allowed_paths = []
            for line in content.split('\n'):
                if line.lower().startswith('allow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        allowed_paths.append(path)

            # Extract sitemaps
            sitemaps = []
            for line in content.split('\n'):
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    if sitemap_url:
                        sitemaps.append(sitemap_url)

            # Extract crawl delay
            crawl_delay = None
            for line in content.split('\n'):
                if line.lower().startswith('crawl-delay:'):
                    try:
                        crawl_delay = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass

            # Calculate crawlability score
            # This is a simple heuristic - more sophisticated scoring could be implemented
            crawlability_score = 100  # Start with perfect score

            # Penalize for each disallowed path
            crawlability_score -= min(50, len(disallowed_paths) * 2)

            # Bonus for each allowed path
            crawlability_score += min(20, len(allowed_paths) * 2)

            # Penalize for crawl delay
            if crawl_delay:
                crawlability_score -= min(30, crawl_delay * 5)

            # Bonus for sitemaps
            crawlability_score += min(10, len(sitemaps) * 5)

            # Ensure score is between 0 and 100
            crawlability_score = max(0, min(100, crawlability_score))

            # Save the results
            robots_data = {
                'status': 'success',
                'content': content,
                'crawlability_score': crawlability_score,
                'disallowed_paths': disallowed_paths,
                'allowed_paths': allowed_paths,
                'sitemaps': sitemaps,
                'crawl_delay': crawl_delay
            }

            # Save to file if output directory exists
            try:
                robots_file = os.path.join(self.output_dir, "_robots.json")
                with open(robots_file, 'w') as f:
                    json.dump(robots_data, f, indent=2)
                logger.info(f"Saved robots.txt analysis to {robots_file}")
            except Exception as e:
                logger.error(f"Error saving robots.txt analysis: {str(e)}")

            return robots_data

        except Exception as e:
            logger.error(f"Error analyzing robots.txt: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'crawlability_score': 0,
                'disallowed_paths': [],
                'allowed_paths': [],
                'sitemaps': [],
                'crawl_delay': None
            }

    def analyze_sitemap(self):
        """
        Analyze sitemap for content assessment

        Returns:
            dict: Dictionary containing sitemap analysis
        """
        logger.info("Analyzing sitemap")

        try:
            # Create a stealth session
            session = self.create_stealth_session()

            # Try to get sitemap URL from robots.txt first
            robots_data = self.analyze_robots_txt()
            sitemap_urls = robots_data.get('sitemaps', [])

            # If no sitemaps found in robots.txt, try common sitemap URLs
            if not sitemap_urls:
                common_sitemap_paths = [
                    '/sitemap.xml',
                    '/sitemap_index.xml',
                    '/sitemap/sitemap.xml',
                    '/sitemapindex.xml'
                ]

                for path in common_sitemap_paths:
                    sitemap_url = urljoin(self.base_url, path)
                    response = session.get(sitemap_url, timeout=30)

                    if response.status_code == 200 and '<sitemap' in response.text:
                        sitemap_urls.append(sitemap_url)
                        break

            if not sitemap_urls:
                logger.warning("No sitemaps found")
                return {
                    'status': 'error',
                    'message': "No sitemaps found",
                    'urls_count': 0,
                    'content_types': {},
                    'last_modified_dates': []
                }

            # Analyze the first sitemap
            sitemap_url = sitemap_urls[0]
            logger.info(f"Analyzing sitemap: {sitemap_url}")

            response = session.get(sitemap_url, timeout=30)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch sitemap: {response.status_code}")
                return {
                    'status': 'error',
                    'message': f"Failed to fetch sitemap: {response.status_code}",
                    'urls_count': 0,
                    'content_types': {},
                    'last_modified_dates': []
                }

            # Parse sitemap content
            soup = BeautifulSoup(response.text, 'xml')

            # Check if it's a sitemap index
            is_sitemap_index = soup.find('sitemapindex') is not None

            urls = []
            if is_sitemap_index:
                # Get URLs of individual sitemaps
                sitemap_tags = soup.find_all('sitemap')
                for sitemap_tag in sitemap_tags[:3]:  # Limit to first 3 sitemaps
                    loc_tag = sitemap_tag.find('loc')
                    if loc_tag:
                        child_sitemap_url = loc_tag.text.strip()
                        try:
                            child_response = session.get(child_sitemap_url, timeout=30)
                            if child_response.status_code == 200:
                                child_soup = BeautifulSoup(child_response.text, 'xml')
                                url_tags = child_soup.find_all('url')
                                for url_tag in url_tags:
                                    loc_tag = url_tag.find('loc')
                                    if loc_tag:
                                        url = loc_tag.text.strip()
                                        lastmod_tag = url_tag.find('lastmod')
                                        lastmod = lastmod_tag.text.strip() if lastmod_tag else None
                                        urls.append({
                                            'url': url,
                                            'lastmod': lastmod
                                        })
                        except Exception as e:
                            logger.error(f"Error fetching child sitemap {child_sitemap_url}: {str(e)}")
            else:
                # Get URLs directly from sitemap
                url_tags = soup.find_all('url')
                for url_tag in url_tags:
                    loc_tag = url_tag.find('loc')
                    if loc_tag:
                        url = loc_tag.text.strip()
                        lastmod_tag = url_tag.find('lastmod')
                        lastmod = lastmod_tag.text.strip() if lastmod_tag else None
                        urls.append({
                            'url': url,
                            'lastmod': lastmod
                        })

            # Analyze content types
            content_types = {}
            for url_data in urls[:20]:  # Limit to first 20 URLs
                url = url_data['url']
                try:
                    # Try to determine content type from URL pattern
                    if '/product/' in url or '/dp/' in url:
                        content_type = 'product'
                    elif '/category/' in url or '/s?' in url:
                        content_type = 'category'
                    elif '/blog/' in url or '/article/' in url:
                        content_type = 'blog'
                    else:
                        content_type = 'other'

                    content_types[content_type] = content_types.get(content_type, 0) + 1
                except Exception as e:
                    logger.error(f"Error analyzing content type for {url}: {str(e)}")

            # Extract last modified dates
            last_modified_dates = []
            for url_data in urls:
                if url_data.get('lastmod'):
                    last_modified_dates.append(url_data['lastmod'])

            # Save the results
            sitemap_data = {
                'status': 'success',
                'sitemap_url': sitemap_url,
                'is_sitemap_index': is_sitemap_index,
                'urls_count': len(urls),
                'content_types': content_types,
                'last_modified_dates': last_modified_dates[:10]  # Limit to first 10 dates
            }

            # Save to file if output directory exists
            try:
                sitemap_file = os.path.join(self.output_dir, "_sitemap.json")
                with open(sitemap_file, 'w') as f:
                    json.dump(sitemap_data, f, indent=2)
                logger.info(f"Saved sitemap analysis to {sitemap_file}")
            except Exception as e:
                logger.error(f"Error saving sitemap analysis: {str(e)}")

            return sitemap_data

        except Exception as e:
            logger.error(f"Error analyzing sitemap: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'urls_count': 0,
                'content_types': {},
                'last_modified_dates': []
            }
