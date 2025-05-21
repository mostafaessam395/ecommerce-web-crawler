import streamlit as st

from css import all_css
import graphistry, pandas as pd, numpy as np
# from components import GraphistrySt  # Comment out problematic import
import os
from components import cfgMaker, createDep, ValidAction, chart_functions
import subprocess
import altair as alt
from streamlit_echarts import st_echarts
import json
from streamlit_apexjs import st_apexcharts
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import asyncio
import sys
from components.js_detector import JSDetector
from components.sitemap_visualizer import SitemapVisualizer
from components.browser_crawler import BrowserCrawler

# Default configuration for crawler
dataConfig = ["https://example.com", 5, 3, True, False]  # [start_url, concurrent_requests, depth, check_lang, surfer]
link_unique = True  # Whether to use unique links only

page_title_str = "Graph dashboard"
st.set_page_config(
    layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
    initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
    page_title=page_title_str,  # String or None. Strings get appended with "• Streamlit".
    page_icon=os.environ.get('FAVICON_URL', 'https://hub.graphistry.com/pivot/favicon/favicon.ico'),
    # String, anything supported by st.image, or None.
)

st.markdown(
    '''
    <style>
    .streamlit-expanderHeader {
        background-color: white;
        color: black; # Adjust this for expander header color
    }
    .streamlit-expanderContent {
        background-color: white;
        color: black; # Expander content color
    }
    </style>
    ''',
    unsafe_allow_html=True
)

st.markdown("""
<style>
div[data-testid="metric-container"] {
   background-color: rgba(28, 131, 225, 0.1);
   border: 1px solid rgba(28, 131, 225, 0.1);
   padding: 5% 5% 5% 10%;
   border-radius: 5px;
   color: rgb(30, 103, 119);
   overflow-wrap: break-word;

}

/* breakline for metric text         */
div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
   overflow-wrap: break-word;
   white-space: break-spaces;
   color: red;
}

</style>
"""
            , unsafe_allow_html=True)


def run():
    run_all()


def dataCSV(csv1, csv2):
    try:
        # Check if files exist
        if not os.path.exists(csv1):
            st.error(f"Data file not found: {csv1}")
            st.info("Please wait for the crawler to complete or try a different URL.")
            return None

        if not os.path.exists(csv2):
            st.error(f"Links file not found: {csv2}")
            st.info("Please wait for the crawler to complete or try a different URL.")
            return None

        df1 = pd.read_csv(csv1)
        df2 = pd.read_csv(csv2)
        df2 = df2.rename(columns={'target': 'url'})

        groupAnchor = df2.groupby('url')['text'].nunique().reset_index(name='nb_anchors_unique')

        df2.pop('text')
        df2.pop('source')
        df2.pop('nofollow')
        df2.pop('disallow')

        merge = pd.merge(df1, df2.drop_duplicates(subset=['url']), on='url', how='left', suffixes=('', ''))

        merge = pd.merge(merge, groupAnchor, on='url', how='left')

        return merge
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.info("Please wait for the crawler to complete or try a different URL.")
        return None


def custom_css():
    all_css()
    st.markdown(
        """<style>

        </style>""", unsafe_allow_html=True)


@st.cache_data()
def run_filters(file, links_type, urls_file):
    """Process links data for visualization"""
    try:
        # Check if file is empty
        if file.empty:
            st.warning("No link data available for visualization.")
            return {'edges_df': pd.DataFrame(), 'graph_url': None}

        # Check if urls_file exists
        if not os.path.exists(urls_file):
            st.warning(f"URL data file not found: {urls_file}")
            return {'edges_df': pd.DataFrame(), 'graph_url': None}

        # Filter links if needed
        if links_type:
            links = file.drop_duplicates(subset=['target'])
        else:
            links = file

        # Try to read the file containing pagerank
        try:
            urls_df = pd.read_csv(urls_file)

            # Check if urls_df has the required columns
            if 'url' not in urls_df.columns or 'pagerank' not in urls_df.columns:
                st.warning("URL data file does not contain required columns (url, pagerank).")
                # Add missing columns with default values
                if 'url' not in urls_df.columns:
                    urls_df['url'] = ''
                if 'pagerank' not in urls_df.columns:
                    urls_df['pagerank'] = 0

            # Try to merge links with urls_df to get pagerank
            links = pd.merge(links, urls_df[['url', 'pagerank']], left_on='target', right_on='url', how='left')
            links['pagerank'].fillna(0, inplace=True)
        except Exception as e:
            st.warning(f"Error processing URL data: {str(e)}")
            # Continue without pagerank data
            if 'pagerank' not in links.columns:
                links['pagerank'] = 0

        # Return the processed links
        return {'edges_df': links, 'graph_url': None}
    except Exception as e:
        st.error(f"Error in visualization processing: {str(e)}")
        return {'edges_df': pd.DataFrame(), 'graph_url': None}


def main_area(edges_df, graph_url):
    """Display the main visualization area with network graph"""
    st.subheader("🕸️ Network Graph Visualization")

    if edges_df.empty:
        st.warning("No graph data available for visualization.")
        return

    # Add explanation of the network graph
    with st.expander("About Network Visualization", expanded=True):
        st.write("""
        ### Network Graph Visualization

        This visualization shows the connections between pages on the website as a network graph:

        - **Nodes**: Each circle represents a page on the website
        - **Edges**: Arrows show links between pages
        - **Labels**: Each node is labeled with its URL path
        """)

    # Show a spinner while loading the graph
    with st.spinner("Loading network graph visualization..."):
        try:
            # Display statistics about the graph
            st.metric("Total Nodes", edges_df['source'].nunique() + edges_df['target'].nunique())
            st.metric("Total Edges", len(edges_df))

            # Create a graph
            import networkx as nx
            import matplotlib.pyplot as plt
            from urllib.parse import urlparse

            G = nx.DiGraph()

            # Add edges
            for _, row in edges_df.iterrows():
                G.add_edge(row['source'], row['target'])

            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 10))

            # Use spring layout
            pos = nx.spring_layout(G, seed=42)

            # Draw nodes
            nx.draw_networkx_nodes(G, pos,
                                 node_color='lightblue',
                                 node_size=100,
                                 alpha=0.7)

            # Draw edges
            nx.draw_networkx_edges(G, pos,
                                 edge_color='gray',
                                 arrows=True,
                                 arrowsize=10,
                                 alpha=0.5)

            # Add simplified labels
            labels = {}
            for node in G.nodes():
                parsed = urlparse(node)
                path = parsed.path
                if not path:
                    path = '/'
                elif len(path) > 15:
                    path = path[:12] + '...'
                labels[node] = path

            nx.draw_networkx_labels(G, pos, labels, font_size=8)

            plt.title("Website Link Structure")
            plt.axis('off')

            # Display the plot
            st.pyplot(fig)

            # Calculate the most connected nodes
            source_counts = edges_df['source'].value_counts().head(5)
            target_counts = edges_df['target'].value_counts().head(5)

            with st.expander("Network Statistics"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("### Top Source Pages")
                    for url, count in source_counts.items():
                        st.write(f"- **{count} links**: {url.split('/')[-1] or url}")

                with col2:
                    st.write("### Top Target Pages")
                    for url, count in target_counts.items():
                        st.write(f"- **{count} links**: {url.split('/')[-1] or url}")

        except Exception as e:
            st.error(f"Error rendering graph: {str(e)}")
            st.info("This may happen if the crawler hasn't generated enough data yet. Please wait for it to complete.")

            # Show a more detailed error message in an expander
            with st.expander("Technical Details"):
                st.code(str(e))
                st.write("Try the following:")
                st.write("1. Wait for the crawler to collect more data")
                st.write("2. Check your internet connection")
                st.write("3. Try refreshing the page")


def analyze_robots_txt(url, max_retries=3, retry_delay=2):
    """
    Analyze robots.txt and return crawlability information

    Args:
        url (str): The URL to analyze
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Base delay between retries in seconds

    Returns:
        dict: Analysis results with status, rules, and score
    """
    try:
        # Parse the URL to get the domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # If no domain is found, try to extract it from the URL
        if not domain:
            if url.startswith('http'):
                domain = url.split('/')[2]
            else:
                domain = url.split('/')[0]

        # Construct the robots.txt URL
        robots_url = f"{parsed_url.scheme or 'https'}://{domain}/robots.txt"

        # Set up headers to look more like a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/plain,text/html;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        # Initialize retry counter and last error
        retry_count = 0
        last_error = None

        # Try to fetch robots.txt with retries
        while retry_count < max_retries:
            try:
                response = requests.get(robots_url, headers=headers, timeout=10)

                # If successful, break out of the retry loop
                if response.status_code == 200:
                    break

                # If robots.txt doesn't exist (404), that's actually good for crawlability
                elif response.status_code == 404:
                    return {
                        'status': 'success',
                        'message': 'No robots.txt found - site is fully crawlable',
                        'rules': {
                            'allowed_paths': ['*'],  # Everything is allowed
                            'disallowed_paths': [],
                            'crawl_delay': None,
                            'sitemaps': []
                        },
                        'score': 100  # Maximum crawlability score
                    }

                # For temporary errors, retry
                elif response.status_code in [429, 503, 502, 500, 504]:
                    retry_count += 1
                    wait_time = retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    time.sleep(wait_time)
                    last_error = f"Temporary error: HTTP {response.status_code}"
                    continue

                # For other status codes, return an error
                else:
                    return {
                        'status': 'error',
                        'message': f'Could not fetch robots.txt (Status code: {response.status_code})',
                        'score': 50  # Default score when robots.txt can't be fetched
                    }

            except (requests.Timeout, requests.ConnectionError) as e:
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                time.sleep(wait_time)
                last_error = str(e)
                continue

            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Error fetching robots.txt: {str(e)}',
                    'score': 50  # Default score when robots.txt can't be fetched
                }

        # If we've exhausted all retries
        if retry_count >= max_retries:
            return {
                'status': 'error',
                'message': f'Failed to fetch robots.txt after {max_retries} attempts. Last error: {last_error}',
                'score': 50  # Default score when robots.txt can't be fetched
            }

        # If we get here, we successfully fetched robots.txt
        robots_content = response.text

        # Extract rules
        rules = {
            'allowed_paths': [],
            'disallowed_paths': [],
            'crawl_delay': None,
            'sitemaps': []
        }

        # Process each line in robots.txt
        for line in robots_content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Look for different directives (case-insensitive)
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'allow':
                    rules['allowed_paths'].append(value)
                elif directive == 'disallow':
                    rules['disallowed_paths'].append(value)
                elif directive == 'crawl-delay':
                    rules['crawl_delay'] = value
                elif directive == 'sitemap':
                    rules['sitemaps'].append(value)

        # Calculate the crawlability score
        score = calculate_crawlability_score(rules)

        return {
            'status': 'success',
            'rules': rules,
            'score': score
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing robots.txt: {str(e)}',
            'score': 50  # Default score when robots.txt can't be analyzed
        }

def calculate_crawlability_score(rules):
    """
    Calculate a crawlability score from 0-100 based on robots.txt rules

    A higher score means the site is more crawlable (fewer restrictions).

    Args:
        rules (dict): Dictionary containing robots.txt rules

    Returns:
        int: Crawlability score from 0-100
    """
    # Start with a perfect score
    score = 100

    # Check if there are any disallowed paths
    if rules['disallowed_paths']:
        # Check for complete crawling restriction
        if '/' in rules['disallowed_paths']:
            # Site completely blocks crawling
            score -= 70  # Severe penalty, but not 0 because some parts might still be crawlable
        else:
            # Calculate penalty based on number and type of disallowed paths
            disallow_penalty = 0

            for path in rules['disallowed_paths']:
                if path.endswith('*'):
                    # Wildcard disallow is more restrictive
                    disallow_penalty += 3
                elif path.startswith('/'):
                    # Root path disallow is more restrictive
                    disallow_penalty += 2
                else:
                    # Regular path disallow
                    disallow_penalty += 1

            # Cap the penalty at 50 points
            score -= min(disallow_penalty * 2, 50)

    # Check for allowed paths (these can offset disallowed paths)
    if rules['allowed_paths']:
        # Bonus for explicit allowed paths
        allow_bonus = min(len(rules['allowed_paths']) * 2, 20)
        score += allow_bonus

    # Penalize for crawl delay
    if rules['crawl_delay']:
        try:
            delay = float(rules['crawl_delay'])
            if delay > 0:
                # Logarithmic penalty for crawl delay
                # 1s delay: -5 points
                # 5s delay: -15 points
                # 10s delay: -20 points
                # 60s delay: -30 points
                delay_penalty = min(5 * (1 + int(delay ** 0.5)), 30)
                score -= delay_penalty
        except (ValueError, TypeError):
            # If we can't parse the delay, apply a small penalty
            score -= 5

    # Bonus for sitemaps (they make crawling more efficient)
    if rules['sitemaps']:
        # More sitemaps = better crawlability
        sitemap_bonus = min(len(rules['sitemaps']) * 5, 20)
        score += sitemap_bonus

    # Ensure score is between 0 and 100
    return max(0, min(100, score))

def display_crawlability_analysis(url):
    """Display crawlability analysis in Streamlit with improved visualization"""
    st.subheader("🔍 Crawlability Analysis")

    # Add retry options in an expander
    with st.expander("Advanced Options"):
        max_retries = st.slider("Max Retries for Robots.txt", 1, 5, 3,
                               help="Maximum number of retry attempts for temporary errors")
        retry_delay = st.slider("Retry Delay for Robots.txt (seconds)", 1, 5, 2,
                               help="Base delay between retries in seconds")

    # Show a spinner while analyzing
    with st.spinner("Analyzing site crawlability..."):
        # Get the analysis with retry options
        analysis = analyze_robots_txt(url, max_retries=max_retries, retry_delay=retry_delay)

    if analysis['status'] == 'success':
        # Display score with a metric
        score = analysis['score']
        st.metric("Crawlability Score", f"{score}/100")

        # Add a progress bar to visualize the score
        st.progress(score/100)

        # Add crawlability interpretation
        if score >= 90:
            st.success("🟢 This site is highly crawlable with minimal restrictions.")
        elif score >= 70:
            st.info("🔵 This site is generally crawlable with some restrictions.")
        elif score >= 40:
            st.warning("🟠 This site has significant crawling restrictions.")
        else:
            st.error("🔴 This site has severe crawling restrictions.")

        # Display message if available
        if 'message' in analysis:
            st.info(analysis['message'])

        # Display rules
        with st.expander("View Robots.txt Rules", expanded=True):
            # Display allowed paths
            if analysis['rules']['allowed_paths']:
                st.write("✅ Allowed Paths:")
                for path in analysis['rules']['allowed_paths']:
                    st.write(f"- {path}")
            else:
                st.write("✅ Allowed Paths: None specified")

            # Display disallowed paths
            if analysis['rules']['disallowed_paths']:
                st.write("❌ Disallowed Paths:")
                for path in analysis['rules']['disallowed_paths']:
                    st.write(f"- {path}")
            else:
                st.write("❌ Disallowed Paths: None (everything is allowed)")

            # Display crawl delay
            if analysis['rules']['crawl_delay']:
                delay = analysis['rules']['crawl_delay']
                st.write(f"⏱️ Crawl Delay: {delay} seconds")

                # Add interpretation of crawl delay
                try:
                    delay_float = float(delay)
                    if delay_float > 10:
                        st.warning(f"This is a high crawl delay that will significantly slow down crawling.")
                    elif delay_float > 5:
                        st.warning(f"This is a moderate crawl delay that will slow down crawling.")
                    elif delay_float > 1:
                        st.info(f"This is a reasonable crawl delay.")
                    else:
                        st.success(f"This is a minimal crawl delay.")
                except:
                    pass
            else:
                st.write("⏱️ Crawl Delay: None specified")

            # Display sitemaps
            if analysis['rules']['sitemaps']:
                st.write("🗺️ Sitemaps:")
                for sitemap in analysis['rules']['sitemaps']:
                    st.write(f"- [{sitemap}]({sitemap})")

                # Add a note about sitemaps
                st.success("Sitemaps make crawling more efficient by providing a list of URLs to crawl.")
            else:
                st.write("🗺️ Sitemaps: None specified")
                st.info("No sitemaps found. Crawling will be less efficient.")

        # Add recommendations based on score
        with st.expander("Crawling Recommendations"):
            if score >= 90:
                st.write("✅ **Recommended Approach**: Standard crawling with Scrapy or similar tools.")
                st.write("✅ **Crawl Rate**: Can use a relatively high crawl rate.")
                st.write("✅ **Depth**: Can crawl to greater depths.")
            elif score >= 70:
                st.write("✅ **Recommended Approach**: Standard crawling with respect for robots.txt rules.")
                st.write("⚠️ **Crawl Rate**: Use a moderate crawl rate to avoid issues.")
                st.write("✅ **Depth**: Can crawl to moderate depths.")
            elif score >= 40:
                st.write("⚠️ **Recommended Approach**: Careful crawling with strict adherence to robots.txt.")
                st.write("⚠️ **Crawl Rate**: Use a low crawl rate to avoid being blocked.")
                st.write("⚠️ **Depth**: Limit crawl depth to avoid issues.")
            else:
                st.write("❌ **Recommended Approach**: Consider alternative data sources or APIs if available.")
                st.write("❌ **Crawl Rate**: Use a very low crawl rate if crawling is necessary.")
                st.write("❌ **Depth**: Keep crawl depth minimal.")

            # Add sitemap recommendation
            if analysis['rules']['sitemaps']:
                st.write("✅ **Sitemaps**: Use the provided sitemaps for more efficient crawling.")
            else:
                st.write("⚠️ **Sitemaps**: No sitemaps available, will need to discover URLs through crawling.")
    else:
        # Display error with suggestions
        st.error(f"Error analyzing robots.txt: {analysis['message']}")

        # Still show the default score
        score = analysis.get('score', 50)
        st.metric("Default Crawlability Score", f"{score}/100")
        st.progress(score/100)

        # Add suggestions based on the error
        if "404" in analysis['message']:
            st.info("No robots.txt file found. This means the site has no crawling restrictions, but be respectful with your crawling rate.")
        elif any(code in analysis['message'] for code in ["429", "503", "502", "500"]):
            st.warning("The server returned a temporary error. You can try again later or adjust the retry settings in Advanced Options.")
        else:
            st.info("Using a default crawlability score. Consider manual inspection of the site's robots.txt file.")

def display_js_analysis(url):
    """Display JavaScript analysis in Streamlit with improved error handling"""
    st.subheader("🔧 JavaScript Analysis")

    # Add retry options in an expander
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            max_retries = st.slider("Max Retries", 1, 10, 3,
                                   help="Maximum number of retry attempts for temporary errors")
            retry_delay = st.slider("Retry Delay (seconds)", 1, 10, 2,
                                   help="Base delay between retries in seconds")
        with col2:
            use_browser = st.checkbox("Use Headless Browser", False,
                                     help="Enable this if the site blocks regular requests")

    # Show a spinner while analyzing
    with st.spinner("Analyzing JavaScript usage..."):
        js_detector = JSDetector()

        # Use the improved analyze_page method with retry capabilities
        result = js_detector.analyze_page(
            url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            use_browser=use_browser
        )

        # Check if analysis was successful
        if result['status'] == 'success':
            # Get the indicators
            indicators = result['indicators']
            script_count = indicators['script_tags']
            event_count = indicators['event_handlers']
            ajax_count = indicators['ajax_calls']
            dynamic_count = indicators['dynamic_content']

            # Get the score and recommendation
            score = result['js_score']
            recommendation = result['recommendation']

            # Display score with a gauge chart
            st.metric("JavaScript Usage Score", f"{score}/100")

            # Create a progress bar to visualize the score
            st.progress(score/100)

            # Display detailed analysis
            with st.expander("View Detailed Analysis", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("📊 JavaScript Elements:")
                    st.write(f"- Script Tags: {script_count}")
                    st.write(f"- Event Handlers: {event_count}")
                    st.write(f"- AJAX Calls: {ajax_count}")
                    st.write(f"- Dynamic Content: {dynamic_count}")

                with col2:
                    st.write("💡 Recommendations:")
                    st.write(f"- {recommendation}")

                    # Add more specific recommendations based on score
                    if score < 30:
                        st.write("- Basic crawler (Scrapy) should work fine")
                    elif score < 70:
                        st.write("- Consider using Splash for JavaScript rendering")
                    else:
                        st.write("- Use Playwright/Selenium for full JavaScript support")
        else:
            # Display error information
            st.error(f"Error analyzing JavaScript: {result['message']}")

            # Display suggestion if available
            if 'suggestion' in result:
                st.info(f"Suggestion: {result['suggestion']}")

            # Provide retry options
            st.warning(
                "You can try adjusting the retry settings in the 'Advanced Options' section above. "
                "For sites with heavy anti-bot protection, try enabling the 'Use Headless Browser' option."
            )

def run_all():
    custom_css()

    st.title("Intelligent Web Crawler & Analyzer")

    text_url = st.text_input("Enter URL to crawl:", "")

    if text_url:
        # Add crawlability analysis at the top
        display_crawlability_analysis(text_url)

        # Add JavaScript analysis
        display_js_analysis(text_url)

        button_clicked = False
        default_display = 'dataframe'

        # Configure crawler settings
        st.sidebar.header("Crawler Settings")
        concurrent_requests = st.sidebar.slider("Concurrent Requests", 1, 10, 5)
        depth = st.sidebar.slider("Crawl Depth", 1, 5, 3)
        check_lang = st.sidebar.checkbox("Check Language", True)
        surfer = st.sidebar.checkbox("Surfer Mode", False)

        # Add browser crawler option
        st.sidebar.header("Advanced Options")
        use_browser = st.sidebar.checkbox("Use Headless Browser", True,
                                         help="Use a headless browser (Playwright) for JavaScript-heavy sites like Amazon")

        # Add delay settings
        min_delay = st.sidebar.slider("Min Delay (seconds)", 1.0, 5.0, 2.0, 0.5,
                                    help="Minimum delay between requests to avoid detection")
        max_delay = st.sidebar.slider("Max Delay (seconds)", 2.0, 10.0, 5.0, 0.5,
                                    help="Maximum delay between requests to avoid detection")

        # Update dataConfig with user inputs
        global dataConfig
        dataConfig = [text_url, concurrent_requests, depth, check_lang, surfer, use_browser, min_delay, max_delay]

        root = createDep().pathProject(text_url)
        slugName = createDep().url_to_name(text_url)
        urls_file = root + '/_urls.csv'
        print(urls_file)

        if not (ValidAction().projectIsset(urls_file)):
            ValidAction().checkCrawlCache(slugName)
            createDep().mkdir(text_url)

            # Get the base directory of the project
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Create the output directory for CSV files
            output_dir = os.path.join(base_dir, 'crowl', 'data', createDep().url_to_name(text_url))
            os.makedirs(output_dir, exist_ok=True)

            # Create symlinks or copy files to the root directory
            if not os.path.exists(f"{root}/_urls.csv"):
                with open(f"{root}/_urls.csv", 'w') as f:
                    f.write("url,response_code,content_type,level,referer,latency,crawled_at,nb_title,title,nb_meta_robots,meta_robots,meta_description,meta_viewport,meta_keywords,canonical,prev,next,h1,nb_h1,nb_h2,wordcount,content,content_lang,XRobotsTag,outlinks,http_date,size,html_lang,hreflangs,microdata,extractors,request_headers,response_headers,redirect,pagerank\n")

            if not os.path.exists(f"{root}/_links.csv"):
                with open(f"{root}/_links.csv", 'w') as f:
                    f.write("source,target,text,nofollow,disallow\n")

            # Check if we should use the browser crawler (for JavaScript-heavy sites)
            if use_browser:
                # Run the browser crawler
                st.info("Using browser-based crawler for JavaScript-heavy site...")

                # Determine the max pages based on depth and concurrent requests
                max_pages = 50  # Default
                if depth == 1:
                    max_pages = 10
                elif depth == 2:
                    max_pages = 25
                elif depth == 3:
                    max_pages = 50
                elif depth == 4:
                    max_pages = 100
                elif depth >= 5:
                    max_pages = 200

                # Run the browser crawler script
                browser_script = os.path.join(base_dir, 'run_browser_crawler.py')

                cmd = f"python \"{browser_script}\" --url \"{text_url}\" --max-pages {max_pages} --max-depth {depth} --min-delay {min_delay} --max-delay {max_delay} --output-dir \"crowl/data\""
                st.info(f"Running browser crawler with command: {cmd}")

                process = subprocess.Popen(cmd, shell=True)

                # Don't wait for the process to complete - let it run in the background
                st.success(f"Browser crawler is running in the background. Check the data directory for results.")
            else:
                # Create config file for standard crawler
                cfgMaker().cfg(dataConfig, root)

                # Build the command with correct paths
                crowl_script = os.path.join(base_dir, 'crowl', 'crowl.py')
                config_file = os.path.join(root, 'config.ini')
                resume_dir = os.path.join(base_dir, 'crowl', 'data', createDep().url_to_name(text_url))

                # Run the crawler
                cmd = f"python \"{crowl_script}\" --conf \"{config_file}\" --resume \"{resume_dir}\""
                st.info(f"Running crawler with command: {cmd}")

                process = subprocess.Popen(cmd, shell=True)

                # Don't wait for the process to complete - let it run in the background
                st.success(f"Standard crawler is running in the background. Check the data directory for results.")

        dataFrame = dataCSV(f"{urls_file}", f"{root}/_links.csv")

        # Check if dataFrame is None (error occurred)
        if dataFrame is None:
            # Show a message about the crawling process
            st.info("The crawler is running in the background. Please wait for it to complete...")

            # Show a progress spinner
            with st.spinner("Crawling in progress..."):
                # Display the crawler command for debugging
                st.code(f"python crowl/crowl.py --conf {root}/config.ini --resume crowl/data/{createDep().url_to_name(text_url)}/")

                # Add a placeholder for the crawler status
                st.empty()

            # Exit early - don't try to process data that doesn't exist yet
            return

        # If we get here, we have data to process
        dataFrame['response_code'] = dataFrame['response_code'].astype(str)
        cols = dataFrame.columns.tolist()
        cols.remove('pagerank')

        cols.insert(1, 'pagerank')
        dataFrame = dataFrame[cols]

        # Add sitemap visualization
        sitemap_visualizer = SitemapVisualizer()
        try:
            sitemap_visualizer.display_sitemap(dataFrame, pd.read_csv(f"{root}/_links.csv"))
        except Exception as e:
            st.error(f"Error displaying sitemap: {str(e)}")

        total_pages = len(dataFrame['url'].unique())

        try:
            dataFrame_links = pd.read_csv(f"{root}/_links.csv")
            total_relations = len(dataFrame_links['source'])
        except Exception as e:
            st.error(f"Error reading links data: {str(e)}")
            dataFrame_links = pd.DataFrame()
            total_relations = 0

        lang_counts = dataFrame['content_lang'].value_counts()

        if not lang_counts.empty:
            most_common_lang = lang_counts.index[0]
            most_common_lang_count = lang_counts.iloc[0]
        else:
            most_common_lang = None
            most_common_lang_count = None

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Pages", value=total_pages)
        with col2:
            st.metric(label="Total Relations", value=total_relations)
        with col3:
            if most_common_lang:
                st.metric(label=f"Language : {most_common_lang.upper()}", value=f"{most_common_lang_count} ")
            else:
                st.metric(label="Language : N/A", value="N/A")

        col5, col6 = st.columns(2)

        with col5:
            expander = st.expander("Graphs")
            with expander:
                col1, col2 = st.columns(2)
                show_general = col1.button("General")
                show_graph = col2.button("Other Graph")

        with col6:
            expander1 = st.expander("Datas")
            with expander1:
                col3, col4 = st.columns(2)
                show_dataframe = col3.button("DataFrame")
                show_visualization = col4.button("Visualization")

        def display_graph_content():
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    options, series = chart_functions().status_code_apex(dataFrame)
                    st.header("Response Code Distribution")
                    st_apexcharts(options, series, 'donut', '600')
                with col2:
                    depth_by_code = dataFrame.groupby(["level", "response_code"]).size().reset_index(name="count")
                    level = depth_by_code['level'].unique()
                    response_code_depth_200 = depth_by_code.query("response_code == '200'")
                    response_code_depth_300 = depth_by_code.query("'300' <= response_code <= '399'")

                    lvl_list = response_code_depth_300['level'].tolist()
                    append_data = []
                    for lvl in level:
                        if lvl_list.count(lvl) == 0:
                            append_data.append({'level': lvl, 'response_code': '301', 'count': '0'})

                    # print(append_data)
                    df = response_code_depth_300.append([{'level': '0', 'response_code': '301', 'count': '0'},
                                                         {'level': '1', 'response_code': '301', 'count': '0'}],
                                                        ignore_index=True)
                    # print(df)
                    df['level'] = df['level'].astype(str)

                    df.sort_values(by=['level'], inplace=True)

                    response_code_depth_400 = depth_by_code.query("response_code == '400'")
                    response_code_depth_500 = depth_by_code.query("response_code == '500'")

                    options, series = chart_functions().http_status_code_by_depth_chart_apex(level,
                                                                                             response_code_depth_200,
                                                                                             df,
                                                                                             response_code_depth_400,
                                                                                             response_code_depth_500)
                    st.header("HTTP Status Code by Depth Chart")
                    st_apexcharts(options, series, 'bar', '600')
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    options, series = chart_functions().https_distribution_apex(dataFrame)
                    st.header("HTTPS Distribution")
                    st_apexcharts(options, series, 'radialBar', '600')

                with col2:
                    options, series = chart_functions().language_distribution_apex(dataFrame)
                    st.header("Language Distribution")
                    st_apexcharts(options, series, 'donut', '600')

                with col3:
                    options, series = chart_functions().latency_distribution_apex(dataFrame)
                    st.header("Latency Distribution")
                    st_apexcharts(options, series, "donut", "600")

            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    options, series = chart_functions().links_per_depth_apex(dataFrame)
                    st.header("Links per Depth")
                    st_apexcharts(options, series, "bar", "600")
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    options, series = chart_functions().title_distribution_apex(dataFrame)
                    st.header("Title Distribution")
                    st_apexcharts(options, series, 'radialBar', '600')

                with col2:
                    options, series = chart_functions().h1_distribution_apex(dataFrame)
                    st.header("H1 Tag Distribution")
                    st_apexcharts(options, series, 'radialBar', '600')

                with col3:
                    options, series = chart_functions().meta_description_distribution_apex(dataFrame)
                    st.header("Meta Description Distribution")
                    st_apexcharts(options, series, 'radialBar', '600')

        if show_dataframe:
            button_clicked = True
            st.dataframe(dataFrame, height=600)

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        if show_visualization:
            button_clicked = True
            # Add option for unique links
            global link_unique
            link_unique = st.sidebar.checkbox("Use Unique Links Only", link_unique)

            # Check if dataFrame_links is empty
            if dataFrame_links.empty:
                st.warning("No link data available for visualization yet. Please wait for the crawler to complete.")
            else:
                try:
                    filter_pipeline_result = run_filters(dataFrame_links, link_unique, urls_file)
                    # Render main viz area based on computed filter pipeline results and sidebar settings
                    main_area(**filter_pipeline_result)
                except Exception as e:
                    st.error(f"Error generating visualization: {str(e)}")
                    st.info("This may happen if the crawler hasn't generated enough data yet. Please wait for it to complete.")
        if show_general:
            button_clicked = True
            display_graph_content()

        if show_graph:
            button_clicked = True
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    options, series = chart_functions().wordcount_distribution_apex(dataFrame)
                    st.header("Word Count Distribution")
                    st_apexcharts(options, series, 'bar', '600')
                with col2:
                    options, series = chart_functions().pagerank_distribution_apex(dataFrame)
                    st.header("PageRank Distribution")
                    st_apexcharts(options, series, 'bar', '600')
        if not button_clicked and default_display == 'dataframe':
            show_dataframe = True
            st.dataframe(dataFrame, height=600)
    else:
        default_display = None




run_all()
