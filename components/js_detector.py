import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import json
import time
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JSDetector')

class JSDetector:
    def __init__(self):
        self.js_indicators = {
            'script_tags': 0,
            'event_handlers': 0,
            'ajax_calls': 0,
            'dynamic_content': 0
        }
        self.html_content = None
        self.soup = None
        self.url = None

        # Common user agents to rotate through
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]

    def fetch_page(self, url, max_retries=3, retry_delay=2, use_browser=False):
        """
        Fetch a web page and store its content for analysis

        Args:
            url (str): The URL to fetch
            max_retries (int): Maximum number of retry attempts for temporary errors
            retry_delay (int): Base delay between retries in seconds
            use_browser (bool): Whether to use a headless browser for JavaScript-heavy sites

        Returns:
            bool: True if successful, raises Exception otherwise
        """
        self.url = url
        retry_count = 0
        last_error = None

        # Log the attempt
        logger.info(f"Attempting to fetch {url}")

        while retry_count < max_retries:
            try:
                # Select a random user agent
                user_agent = random.choice(self.user_agents)

                # Set up headers to look more like a browser
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0'
                }

                # Make the request
                response = requests.get(url, headers=headers, timeout=15)

                # Handle different status codes
                if response.status_code == 200:
                    self.html_content = response.text
                    self.soup = BeautifulSoup(self.html_content, 'html.parser')

                    # Analyze the content
                    self._analyze_content()
                    logger.info(f"Successfully fetched and analyzed {url}")
                    return True

                elif response.status_code in [429, 503, 502, 500, 504]:
                    # These are potentially temporary errors, so we'll retry
                    retry_count += 1
                    wait_time = retry_delay * (2 ** (retry_count - 1))  # Exponential backoff

                    # Add some randomness to avoid detection
                    wait_time = wait_time * (0.5 + random.random())

                    logger.warning(f"Received status code {response.status_code} for {url}. "
                                  f"Retrying in {wait_time:.2f} seconds (attempt {retry_count}/{max_retries})")

                    time.sleep(wait_time)
                    last_error = f"Temporary error: HTTP {response.status_code} - {response.reason}"
                    continue

                else:
                    # For other status codes, we won't retry
                    raise Exception(f"HTTP Error: {response.status_code} - {response.reason}")

            except requests.Timeout:
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                logger.warning(f"Request timed out for {url}. "
                              f"Retrying in {wait_time:.2f} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
                last_error = "Request timed out"

            except requests.ConnectionError:
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                logger.warning(f"Connection error for {url}. "
                              f"Retrying in {wait_time:.2f} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
                last_error = "Connection error"

            except Exception as e:
                # For other exceptions, we'll retry once
                retry_count += 1
                wait_time = retry_delay
                logger.warning(f"Unexpected error for {url}: {str(e)}. "
                              f"Retrying in {wait_time:.2f} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
                last_error = str(e)

        # If we've exhausted all retries, raise an exception with details
        error_msg = f"Failed to fetch {url} after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)

        # Suggest using a headless browser if not already tried
        if not use_browser:
            logger.info("Consider using a headless browser for this site by setting use_browser=True")

        raise Exception(error_msg)

    def _analyze_content(self):
        """Analyze the page content for JavaScript indicators"""
        if not self.html_content or not self.soup:
            raise Exception("No page content to analyze. Call fetch_page() first.")

        # Count script tags
        self.js_indicators['script_tags'] = len(self.soup.find_all('script'))

        # Look for event handlers
        event_handlers = re.findall(r'on\w+\s*=', self.html_content)
        self.js_indicators['event_handlers'] = len(event_handlers)

        # Look for AJAX calls
        ajax_calls = re.findall(r'\.ajax\(|fetch\(|axios\.', self.html_content)
        self.js_indicators['ajax_calls'] = len(ajax_calls)

        # Look for dynamic content indicators
        dynamic_content = re.findall(r'document\.getElementById|document\.querySelector|innerHTML', self.html_content)
        self.js_indicators['dynamic_content'] = len(dynamic_content)

    def count_script_tags(self):
        """Return the number of script tags found"""
        if self.js_indicators['script_tags'] is None:
            return 0
        return self.js_indicators['script_tags']

    def count_event_handlers(self):
        """Return the number of event handlers found"""
        if self.js_indicators['event_handlers'] is None:
            return 0
        return self.js_indicators['event_handlers']

    def count_ajax_calls(self):
        """Return the number of AJAX calls found"""
        if self.js_indicators['ajax_calls'] is None:
            return 0
        return self.js_indicators['ajax_calls']

    def count_dynamic_content(self):
        """Return the number of dynamic content indicators found"""
        if self.js_indicators['dynamic_content'] is None:
            return 0
        return self.js_indicators['dynamic_content']

    def _calculate_js_score(self):
        """Calculate a JavaScript usage score from 0-100"""
        # Weight factors for each indicator
        weights = {
            'script_tags': 0.3,
            'event_handlers': 0.2,
            'ajax_calls': 0.3,
            'dynamic_content': 0.2
        }

        # Calculate normalized scores (0-100) for each indicator
        scores = {}
        scores['script_tags'] = min(100, self.js_indicators['script_tags'] * 10)
        scores['event_handlers'] = min(100, self.js_indicators['event_handlers'] * 5)
        scores['ajax_calls'] = min(100, self.js_indicators['ajax_calls'] * 20)
        scores['dynamic_content'] = min(100, self.js_indicators['dynamic_content'] * 10)

        # Calculate weighted score
        weighted_score = sum(scores[key] * weights[key] for key in weights)

        return int(weighted_score)

    def _get_recommendation(self):
        """Get recommendation based on JS score"""
        score = self._calculate_js_score()

        if score < 30:
            return "Basic crawler (Scrapy) should work fine"
        elif score < 70:
            return "Consider using Splash for JavaScript rendering"
        else:
            return "Use Playwright/Selenium for full JavaScript support"

    def calculate_js_score(self):
        """Calculate a JavaScript usage score from 0-100"""
        return self._calculate_js_score()

    def analyze_page(self, url, max_retries=3, retry_delay=2, use_browser=False):
        """
        Analyze a page for JavaScript usage

        Args:
            url (str): The URL to analyze
            max_retries (int): Maximum number of retry attempts for temporary errors
            retry_delay (int): Base delay between retries in seconds
            use_browser (bool): Whether to use a headless browser for JavaScript-heavy sites

        Returns:
            dict: Analysis results or error information
        """
        try:
            # Try to fetch the page with retry mechanism
            self.fetch_page(url, max_retries=max_retries, retry_delay=retry_delay, use_browser=use_browser)

            # If successful, return the analysis results
            result = {
                'status': 'success',
                'js_score': self._calculate_js_score(),
                'indicators': self.js_indicators,
                'recommendation': self._get_recommendation(),
                'url': url
            }

            logger.info(f"Successfully analyzed JavaScript for {url} with score {result['js_score']}/100")
            return result

        except Exception as e:
            # Log the error
            logger.error(f"Failed to analyze JavaScript for {url}: {str(e)}")

            # Return a detailed error response
            error_response = {
                'status': 'error',
                'message': str(e),
                'url': url
            }

            # Add suggestions for common errors
            if '503' in str(e):
                error_response['suggestion'] = (
                    "The server returned a 503 Service Unavailable error. This usually means the server is "
                    "temporarily overloaded or under maintenance. Try again later or use a headless browser approach."
                )
            elif '429' in str(e):
                error_response['suggestion'] = (
                    "The server returned a 429 Too Many Requests error. You may be rate-limited. "
                    "Try increasing the retry delay or using a proxy."
                )
            elif 'timeout' in str(e).lower():
                error_response['suggestion'] = (
                    "The request timed out. The server might be slow or unresponsive. "
                    "Try increasing the timeout value or try again later."
                )

            return error_response

    def _get_recommendation(self):
        """Get recommendation based on JavaScript usage"""
        score = self._calculate_js_score()

        if score < 20:
            return {
                'tool': 'Scrapy',
                'reason': 'Low JavaScript usage, standard crawling sufficient'
            }
        elif score < 50:
            return {
                'tool': 'Scrapy + Splash',
                'reason': 'Moderate JavaScript usage, consider using Splash for rendering'
            }
        else:
            return {
                'tool': 'Playwright/Selenium',
                'reason': 'High JavaScript usage, requires full browser automation'
            }