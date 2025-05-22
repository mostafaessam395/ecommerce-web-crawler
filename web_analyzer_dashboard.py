"""
Enhanced E-commerce Dashboard with advanced visualizations and insights panel
"""
import streamlit as st

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Enhanced E-commerce Crawler & Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other libraries
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import os
import sys
from settings import config, is_streamlit_cloud

# Import the appropriate crawler based on the environment
# We'll do this after the page is set up to avoid Streamlit errors
def get_crawler():
    """Get the appropriate crawler based on the environment"""
    if is_streamlit_cloud():
        try:
            from components.cloud_crawler import CloudCrawler
            return CloudCrawler
        except ImportError:
            from components.ecommerce_crawler import EcommerceCrawler
            return EcommerceCrawler
    else:
        from components.ecommerce_crawler import EcommerceCrawler
        return EcommerceCrawler

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        background-color: #121212;
        color: #f0f0f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e1e1e;
        border-radius: 4px;
        padding: 10px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 20px 10px;
    }
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .insight-card {
        background-color: #2d2d2d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #ff9900;
        color: black;
        font-weight: bold;
    }
    .stProgress .st-bo {
        background-color: #ff9900;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'crawler' not in st.session_state:
    # Get the appropriate crawler class
    CrawlerClass = get_crawler()
    st.session_state.crawler = CrawlerClass(output_dir=config['results_dir'])

    # Show crawler information (after initialization)
    crawler_type = type(st.session_state.crawler).__name__
    if crawler_type == "CloudCrawler":
        st.sidebar.success("Using Cloud-optimized crawler for Streamlit Cloud")
    elif crawler_type == "EcommerceCrawler" and is_streamlit_cloud():
        st.sidebar.warning("Cloud crawler not available, using standard crawler")
if 'crawl_results' not in st.session_state:
    st.session_state.crawl_results = None
if 'crawl_in_progress' not in st.session_state:
    st.session_state.crawl_in_progress = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'robots_data' not in st.session_state:
    st.session_state.robots_data = None
if 'sitemap_data' not in st.session_state:
    st.session_state.sitemap_data = None

# Add in-memory storage for Streamlit Cloud
if 'products_data' not in st.session_state:
    st.session_state.products_data = []

if 'urls_data' not in st.session_state:
    st.session_state.urls_data = []

if 'links_data' not in st.session_state:
    st.session_state.links_data = []

# Title and description
st.title("🔍 Enhanced E-commerce Crawler & Analyzer")
st.markdown("""
This advanced tool crawls e-commerce websites to extract product information, analyze site structure,
and provide insights on crawlability and content. Use the controls below to configure and start the crawl.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Crawler Configuration")

    # Display environment and configuration information
    env_expander = st.expander("Environment Info", expanded=False)
    with env_expander:
        from settings import ENVIRONMENT, is_streamlit_cloud
        st.write(f"Current Environment: {ENVIRONMENT}")
        st.write(f"Running on Streamlit Cloud: {is_streamlit_cloud()}")
        st.write(f"Results Directory: {config['results_dir']}")
        st.write(f"Save Results: {config['save_results']}")

        # Show crawler information
        crawler_type = type(st.session_state.crawler).__name__
        st.write(f"Crawler Type: {crawler_type}")

        if crawler_type == "CloudCrawler":
            st.success("Using Cloud-optimized crawler that works on Streamlit Cloud")
            # Show proxy information if available
            if hasattr(st.session_state.crawler, 'proxies') and st.session_state.crawler.proxies:
                st.write(f"Using {len(st.session_state.crawler.proxies)} proxies for rotation")
            else:
                st.warning("No proxies configured. Amazon may block requests from Streamlit Cloud IP addresses.")
                st.info("Consider adding proxies to the CloudCrawler.proxies list for better results.")
        elif crawler_type == "EcommerceCrawler":
            if is_streamlit_cloud():
                st.warning("Using standard crawler on Streamlit Cloud. This may not work properly.")
                st.info("The standard crawler uses Playwright which has limited support on Streamlit Cloud.")
            else:
                st.success("Using standard crawler with Playwright for local environment")

        # Check if the results directory is writable
        import os
        results_dir = config['results_dir']
        if not os.path.exists(results_dir):
            try:
                os.makedirs(results_dir, exist_ok=True)
                st.success(f"Created results directory: {results_dir}")
            except Exception as e:
                st.error(f"Error creating results directory: {str(e)}")
        else:
            st.success(f"Results directory exists: {results_dir}")

        # Check if we can write to the results directory
        try:
            test_file = os.path.join(results_dir, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("Test write")
            os.remove(test_file)
            st.success(f"Results directory is writable")
        except Exception as e:
            st.error(f"Results directory is not writable: {str(e)}")

    query = st.text_input("Search Query", "laptop")
    max_pages = st.slider("Maximum Pages to Crawl", 5, 100, config['max_pages'])
    max_depth = st.slider("Maximum Depth", 1, 5, config['max_depth'])

    st.subheader("Advanced Settings")
    col1, col2 = st.columns(2)
    with col1:
        min_delay = st.number_input("Min Delay (s)", 1.0, 10.0, float(config['delay_range'][0]), 0.5)
    with col2:
        max_delay = st.number_input("Max Delay (s)", min_delay, 15.0, float(config['delay_range'][1]), 0.5)

    stealth_mode = st.checkbox("Stealth Mode", config['stealth_mode'])
    analyze_robots = st.checkbox("Analyze Robots.txt", config['analyze_robots'])
    analyze_sitemap = st.checkbox("Analyze Sitemap", config['analyze_sitemap'])

    # Add proxy configuration for CloudCrawler
    if is_streamlit_cloud() or type(st.session_state.crawler).__name__ == "CloudCrawler":
        st.subheader("Proxy Configuration")
        st.info("Amazon may block requests from Streamlit Cloud IP addresses. Adding proxies can help avoid this.")

        # Add proxy input
        proxy_input = st.text_area(
            "Add Proxies (one per line, format: http://username:password@ip:port)",
            height=100,
            help="Enter one proxy per line in the format http://username:password@ip:port. Free proxies can be found at https://free-proxy-list.net/"
        )

        # Add button to update proxies
        if st.button("Update Proxies"):
            if proxy_input:
                # Split by newlines and filter out empty lines
                proxies = [p.strip() for p in proxy_input.split('\n') if p.strip()]

                # Update the crawler's proxies
                if hasattr(st.session_state.crawler, 'proxies'):
                    st.session_state.crawler.proxies = proxies
                    st.success(f"Added {len(proxies)} proxies to the crawler")
                else:
                    st.error("Current crawler does not support proxies")
            else:
                # Clear proxies if input is empty
                if hasattr(st.session_state.crawler, 'proxies'):
                    st.session_state.crawler.proxies = []
                    st.info("Cleared all proxies from the crawler")

    # Save configuration button
    if st.button("Save Configuration"):
        config['max_pages'] = max_pages
        config['max_depth'] = max_depth
        config['delay_range'] = (min_delay, max_delay)
        config['stealth_mode'] = stealth_mode
        config['analyze_robots'] = analyze_robots
        config['analyze_sitemap'] = analyze_sitemap

        from settings import save_config
        if save_config(config):
            st.success("Configuration saved successfully!")
        else:
            st.error("Failed to save configuration.")

    # Start crawling button
    start_button = st.button("Start Crawling", type="primary")

# Function to create insights panel
def create_insights_panel(df_products, *_):
    """Create an insights panel with actionable intelligence"""

    st.subheader("📊 Product Insights")

    # Clean price data
    if 'price' in df_products.columns:
        df_products['price_numeric'] = df_products['price'].str.replace('$', '').str.replace(',', '').astype(float)

    # Clean rating data
    if 'rating' in df_products.columns:
        df_products['rating_numeric'] = pd.to_numeric(df_products['rating'], errors='coerce')

    col1, col2, col3 = st.columns(3)

    with col1:
        # Average price
        if 'price_numeric' in df_products.columns:
            avg_price = df_products['price_numeric'].mean()
            st.metric("Average Price", f"${avg_price:.2f}")

    with col2:
        # Product count
        st.metric("Total Products", len(df_products))

    with col3:
        # Average rating
        if 'rating_numeric' in df_products.columns:
            avg_rating = df_products['rating_numeric'].mean()
            st.metric("Average Rating", f"{avg_rating:.1f} ⭐")

    # Price distribution
    if 'price_numeric' in df_products.columns:
        st.subheader("Price Distribution")
        fig = px.histogram(
            df_products,
            x='price_numeric',
            nbins=20,
            title="Price Distribution",
            labels={'price_numeric': 'Price ($)', 'count': 'Number of Products'},
            color_discrete_sequence=['#FF9900']  # Amazon orange
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

    # Rating vs. Price
    if 'price_numeric' in df_products.columns and 'rating_numeric' in df_products.columns:
        st.subheader("Rating vs. Price")
        fig = px.scatter(
            df_products,
            x='rating_numeric',
            y='price_numeric',
            hover_name='title',
            title="Rating vs. Price",
            labels={
                'rating_numeric': 'Rating (stars)',
                'price_numeric': 'Price ($)'
            },
            color_discrete_sequence=['#FF9900']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

    # Brand analysis
    if 'brand' in df_products.columns:
        st.subheader("Brand Analysis")
        brand_counts = df_products['brand'].value_counts().reset_index()
        brand_counts.columns = ['Brand', 'Count']
        brand_counts = brand_counts.head(10)  # Top 10 brands

        fig = px.bar(
            brand_counts,
            x='Brand',
            y='Count',
            title="Top 10 Brands",
            color='Count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

# Function to start crawling
def start_crawling():
    st.session_state.crawl_in_progress = True
    st.session_state.progress = 0

    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    debug_info = st.empty()

    # Analyze robots.txt if enabled
    if analyze_robots:
        status_text.text("Analyzing robots.txt...")
        try:
            if hasattr(st.session_state.crawler, 'analyze_robots_txt'):
                st.session_state.robots_data = st.session_state.crawler.analyze_robots_txt()
                st.session_state.progress = 10
                progress_bar.progress(st.session_state.progress)
            else:
                debug_info.warning("Robots.txt analysis not available for this crawler")
                st.session_state.progress = 10
                progress_bar.progress(st.session_state.progress)
        except Exception as e:
            debug_info.error(f"Error analyzing robots.txt: {str(e)}")
            st.session_state.progress = 10
            progress_bar.progress(st.session_state.progress)

    # Analyze sitemap if enabled
    if analyze_sitemap:
        status_text.text("Analyzing sitemap...")
        try:
            if hasattr(st.session_state.crawler, 'analyze_sitemap'):
                st.session_state.sitemap_data = st.session_state.crawler.analyze_sitemap()
                st.session_state.progress = 20
                progress_bar.progress(st.session_state.progress)
            else:
                debug_info.warning("Sitemap analysis not available for this crawler")
                st.session_state.progress = 20
                progress_bar.progress(st.session_state.progress)
        except Exception as e:
            debug_info.error(f"Error analyzing sitemap: {str(e)}")
            st.session_state.progress = 20
            progress_bar.progress(st.session_state.progress)

    # Start crawling
    status_text.text(f"Crawling for '{query}'...")

    # Make sure the output directory exists
    try:
        results_dir = config['results_dir']
        os.makedirs(results_dir, exist_ok=True)
        debug_info.success(f"Created/verified output directory: {os.path.abspath(results_dir)}")

        # Test if the directory is writable
        test_file = os.path.join(results_dir, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("Test write")
        os.remove(test_file)
        debug_info.success(f"Output directory is writable")

        # Log the output directory
        debug_info.info(f"Output directory: {os.path.abspath(results_dir)}")

        # For Streamlit Cloud, ensure the crawler uses the correct output directory
        from settings import ENVIRONMENT
        if ENVIRONMENT == 'streamlit_cloud':
            st.session_state.crawler.output_dir = results_dir
            st.session_state.crawler.urls_file = os.path.join(results_dir, "_urls.csv")
            st.session_state.crawler.links_file = os.path.join(results_dir, "_links.csv")
            st.session_state.crawler.products_file = os.path.join(results_dir, "_products.csv")
            st.session_state.crawler.robots_file = os.path.join(results_dir, "_robots.json")
            debug_info.info(f"Updated crawler output paths for Streamlit Cloud")
            debug_info.info(f"Products will be saved to: {st.session_state.crawler.products_file}")
    except Exception as e:
        debug_info.error(f"Error setting up output directory: {str(e)}")

    try:
        # Run the crawler
        results = st.session_state.crawler.crawl(
            query=query,
            max_pages=max_pages,
            max_depth=max_depth,
            delay_range=(min_delay, max_delay)
        )

        st.session_state.crawl_results = results

        # Check if products were found
        products_count = len(results.get('products', []))

        # Log detailed information about the results
        debug_info.info(f"Crawl completed with {products_count} products found")

        # Store results in session state for Streamlit Cloud
        if products_count > 0:
            st.session_state.products_data = results.get('products', [])
            debug_info.success(f"Stored {len(st.session_state.products_data)} products in session state")

        if 'visited_urls' in results:
            st.session_state.urls_data = [{'url': url} for url in results.get('visited_urls', [])]
            debug_info.success(f"Stored {len(st.session_state.urls_data)} URLs in session state")

        if 'links' in results:
            st.session_state.links_data = results.get('links', [])
            debug_info.success(f"Stored {len(st.session_state.links_data)} links in session state")

        if 'files' in results:
            file_info = results['files']
            debug_info.info(f"Products file: {file_info.get('products_file')}")
            debug_info.info(f"Products file exists: {file_info.get('products_file_exists')}")
            debug_info.info(f"Products file size: {file_info.get('products_file_size')} bytes")

        st.session_state.crawl_in_progress = False
        st.session_state.progress = 100
        progress_bar.progress(100)

        status_message = f"Crawl completed! Visited {len(results['visited_urls'])} pages, found {products_count} products."
        status_text.text(status_message)

        # If no products were found, show a warning
        if products_count == 0:
            debug_info.warning("No products were found during the crawl. This might be due to Amazon's anti-scraping measures or changes in their HTML structure.")
            debug_info.info("Try adjusting the crawler settings or using a different search query.")

    except Exception as e:
        st.session_state.crawl_in_progress = False
        status_text.error(f"Error during crawl: {str(e)}")
        debug_info.exception(e)

    # Rerun to update the UI
    st.rerun()

# Start crawling if button is clicked
if start_button:
    start_crawling()

# Main content tabs
tabs = st.tabs(["Overview", "Products", "Visual Sitemap", "Network Graph", "Crawl Timeline", "Data Explorer"])

# Load data if available
products_df = pd.DataFrame()
urls_df = pd.DataFrame()
links_df = pd.DataFrame()

# Define file paths
products_file = os.path.join(config['results_dir'], "_products.csv")
urls_file = os.path.join(config['results_dir'], "_urls.csv")
links_file = os.path.join(config['results_dir'], "_links.csv")

# Log file paths and existence
st.sidebar.markdown("### Debug Information")
debug_expander = st.sidebar.expander("Show Data File Info", expanded=False)
with debug_expander:
    st.write(f"Products file: {products_file}")
    st.write(f"Products file exists: {os.path.exists(products_file)}")
    if os.path.exists(products_file):
        st.write(f"Products file size: {os.path.getsize(products_file)} bytes")

    st.write(f"URLs file: {urls_file}")
    st.write(f"URLs file exists: {os.path.exists(urls_file)}")

    st.write(f"Links file: {links_file}")
    st.write(f"Links file exists: {os.path.exists(links_file)}")

    # Show session state data
    st.write("### Session State Data")
    st.write(f"Products in session state: {len(st.session_state.products_data)}")
    st.write(f"URLs in session state: {len(st.session_state.urls_data)}")
    st.write(f"Links in session state: {len(st.session_state.links_data)}")

    # Show a sample of products in session state
    if len(st.session_state.products_data) > 0:
        st.write("Sample product from session state:")
        st.json(st.session_state.products_data[0])

# Check if we have data in session state (for Streamlit Cloud)
if len(st.session_state.products_data) > 0:
    debug_expander.write(f"Using {len(st.session_state.products_data)} products from session state")
    products_df = pd.DataFrame(st.session_state.products_data)

if len(st.session_state.urls_data) > 0:
    debug_expander.write(f"Using {len(st.session_state.urls_data)} URLs from session state")
    urls_df = pd.DataFrame(st.session_state.urls_data)

if len(st.session_state.links_data) > 0:
    debug_expander.write(f"Using {len(st.session_state.links_data)} links from session state")
    links_df = pd.DataFrame(st.session_state.links_data)

# If session state is empty, try to load from files
if products_df.empty or urls_df.empty or links_df.empty:
    debug_expander.write("Session state data not available, trying to load from files")
    try:
        if os.path.exists(products_file) and os.path.getsize(products_file) > 0:
            try:
                # Try to read with standard settings first
                products_df = pd.read_csv(products_file)
                debug_expander.write(f"Loaded {len(products_df)} products with standard settings")
            except Exception as e1:
                debug_expander.write(f"Standard CSV reading failed: {str(e1)}")
                try:
                    # Try with more robust error handling
                    products_df = pd.read_csv(
                        products_file,
                        error_bad_lines=False,  # Skip bad lines
                        warn_bad_lines=True,    # Warn about bad lines
                        quoting=1,              # Quote all fields
                        escapechar='\\',        # Use backslash as escape character
                        on_bad_lines='skip'     # Skip bad lines (pandas 1.3+)
                    )
                    debug_expander.write(f"Loaded {len(products_df)} products with robust settings")
                except Exception as e2:
                    debug_expander.write(f"Robust CSV reading also failed: {str(e2)}")
                    # Last resort: read the file manually
                    try:
                        import csv
                        with open(products_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            headers = next(reader)
                            data = []
                            for row in reader:
                                if len(row) == len(headers):
                                    data.append(row)
                                else:
                                    debug_expander.write(f"Skipping malformed row: {row}")
                            products_df = pd.DataFrame(data, columns=headers)
                        debug_expander.write(f"Loaded {len(products_df)} products with manual CSV reading")
                    except Exception as e3:
                        debug_expander.write(f"Manual CSV reading failed: {str(e3)}")
                        # Create an empty DataFrame with the expected columns
                        products_df = pd.DataFrame(columns=['title', 'url', 'price', 'original_price', 'rating',
                                                        'reviews_count', 'availability', 'image_url', 'asin', 'brand'])
        else:
            debug_expander.write("Products file is empty or doesn't exist")

        if os.path.exists(urls_file):
            try:
                urls_df = pd.read_csv(urls_file)
            except Exception as e:
                debug_expander.write(f"Error reading URLs file: {str(e)}")
                urls_df = pd.DataFrame()

        if os.path.exists(links_file):
            try:
                links_df = pd.read_csv(links_file)
            except Exception as e:
                debug_expander.write(f"Error reading links file: {str(e)}")
                links_df = pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Error loading data: {str(e)}")
        if products_df.empty:
            products_df = pd.DataFrame(columns=['title', 'url', 'price', 'original_price', 'rating',
                                            'reviews_count', 'availability', 'image_url', 'asin', 'brand'])
        if urls_df.empty:
            urls_df = pd.DataFrame()
        if links_df.empty:
            links_df = pd.DataFrame()

# Overview tab
with tabs[0]:
    st.header("Crawl Overview")

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pages Crawled", len(urls_df) if not urls_df.empty else 0)

    with col2:
        st.metric("Products Found", len(products_df) if not products_df.empty else 0)

    with col3:
        st.metric("Links Extracted", len(links_df) if not links_df.empty else 0)

    with col4:
        crawlability = st.session_state.crawler.crawlability_score if hasattr(st.session_state.crawler, 'crawlability_score') else 0
        st.metric("Crawlability Score", f"{crawlability:.1f}%")

    # Response status codes
    st.subheader("Response Status Codes")
    if not urls_df.empty and 'response_code' in urls_df.columns:
        status_counts = urls_df['response_code'].value_counts().reset_index()
        status_counts.columns = ['Status Code', 'Count']

        fig = px.bar(
            status_counts,
            x='Status Code',
            y='Count',
            color='Status Code',
            color_continuous_scale='Viridis',
            title="HTTP Status Codes"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

    # Robots.txt analysis
    if st.session_state.robots_data:
        st.subheader("Robots.txt Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Crawl Delay:** {st.session_state.robots_data.get('crawl_delay', 'None')}")
            st.markdown(f"**Crawlability Score:** {st.session_state.robots_data.get('crawlability_score', 0):.1f}%")

        with col2:
            st.markdown(f"**Sitemaps:** {len(st.session_state.robots_data.get('sitemaps', []))}")
            st.markdown(f"**Disallowed Paths:** {len(st.session_state.robots_data.get('disallowed_paths', []))}")

        # Show disallowed paths
        if st.session_state.robots_data.get('disallowed_paths'):
            with st.expander("Disallowed Paths"):
                for path in st.session_state.robots_data.get('disallowed_paths', [])[:20]:  # Show first 20
                    st.markdown(f"- `{path}`")

    # Create insights panel
    if not products_df.empty and not urls_df.empty:
        create_insights_panel(products_df, urls_df, links_df)

# Products tab
with tabs[1]:
    st.header("Products")

    if not products_df.empty:
        # Filter options
        st.subheader("Filter Products")
        col1, col2 = st.columns(2)

        with col1:
            min_price = st.number_input("Min Price", 0.0, 10000.0, 0.0, 10.0)

        with col2:
            max_price = st.number_input("Max Price", min_price, 10000.0, 2000.0, 10.0)

        # Apply filters
        filtered_df = products_df.copy()

        # Debug information about the products dataframe
        st.sidebar.markdown("### Products DataFrame Info")
        debug_products = st.sidebar.expander("Show Products DataFrame Info", expanded=False)
        with debug_products:
            st.write(f"Products DataFrame Shape: {products_df.shape}")
            st.write(f"Products DataFrame Columns: {products_df.columns.tolist()}")
            if not products_df.empty:
                st.write("First few rows of products_df:")
                st.dataframe(products_df.head(3))

        if 'price' in products_df.columns:
            try:
                # Handle price conversion more robustly
                def safe_convert_price(price_str):
                    if pd.isna(price_str) or not isinstance(price_str, str):
                        return 0.0
                    # Remove currency symbols and commas
                    price_str = str(price_str).replace('$', '').replace('£', '').replace('€', '').replace(',', '')
                    # Extract the first number found
                    import re
                    match = re.search(r'(\d+(\.\d+)?)', price_str)
                    if match:
                        return float(match.group(1))
                    return 0.0

                filtered_df['price_numeric'] = filtered_df['price'].apply(safe_convert_price)
                filtered_df = filtered_df[(filtered_df['price_numeric'] >= min_price) & (filtered_df['price_numeric'] <= max_price)]

                # Show price conversion debug info
                with debug_products:
                    if not filtered_df.empty:
                        st.write("Price conversion examples:")
                        price_examples = pd.DataFrame({
                            'original_price': filtered_df['price'].head(5),
                            'converted_price': filtered_df['price_numeric'].head(5)
                        })
                        st.dataframe(price_examples)
            except Exception as e:
                st.sidebar.error(f"Error converting prices: {str(e)}")
                # If price conversion fails, just use the original dataframe
                filtered_df = products_df.copy()

        # Display products
        st.subheader(f"Found {len(filtered_df)} Products")

        # Add pagination
        items_per_page = 30  # Show 30 products per page (10 rows of 3)
        total_pages = max(1, (len(filtered_df) + items_per_page - 1) // items_per_page)

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            if total_pages > 1:
                page_number = st.slider("Page", 1, total_pages, 1)
            else:
                page_number = 1

        # Calculate start and end indices for current page
        start_idx = (page_number - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_df))

        # Display page info
        st.markdown(f"Showing products {start_idx+1}-{end_idx} of {len(filtered_df)}")

        # Display as cards
        try:
            for i in range(start_idx, end_idx, 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < end_idx:
                        try:
                            product = filtered_df.iloc[i + j]
                            with cols[j]:
                                st.markdown(f"<div class='insight-card'>", unsafe_allow_html=True)

                                # Display image if available
                                if 'image_url' in product and pd.notna(product['image_url']):
                                    try:
                                        st.image(product['image_url'], width=150)
                                    except Exception as img_err:
                                        st.warning(f"Could not load image")

                                # Display title
                                if 'title' in product and pd.notna(product['title']):
                                    title_text = str(product['title'])
                                    if len(title_text) > 50:
                                        title_text = title_text[:50] + "..."
                                    st.markdown(f"**{title_text}**")
                                else:
                                    st.markdown("**No title available**")

                                # Display price
                                if 'price' in product and pd.notna(product['price']):
                                    st.markdown(f"**Price:** {product['price']}")

                                # Display rating
                                if 'rating' in product and pd.notna(product['rating']):
                                    st.markdown(f"**Rating:** {product['rating']} ⭐")

                                # Display link
                                if 'url' in product and pd.notna(product['url']):
                                    url = product['url']
                                    # Make sure URL is valid
                                    if url.startswith('http'):
                                        st.markdown(f"[View Product]({url})")
                                    else:
                                        st.markdown(f"[View Product](https://www.amazon.com{url})")

                                st.markdown("</div>", unsafe_allow_html=True)
                        except Exception as card_err:
                            with cols[j]:
                                st.error(f"Error displaying product card")
        except Exception as display_err:
            st.error(f"Error displaying products: {str(display_err)}")
            st.info("Try running a new crawl to generate better product data.")
    else:
        st.info("No products found. Start a crawl to see products here.")

# Visual Sitemap tab
with tabs[2]:
    st.header("Website Structure")

    if not links_df.empty:
        try:
            # Create network graph
            G = nx.DiGraph()

            # Add nodes and edges
            valid_edges = 0
            for _, row in links_df.iterrows():
                try:
                    if pd.notna(row['source']) and pd.notna(row['target']):
                        G.add_edge(row['source'], row['target'])
                        valid_edges += 1
                except Exception as e:
                    st.warning(f"Error adding edge: {str(e)}")
                    continue

            if valid_edges == 0:
                st.warning("No valid edges found in the data. Cannot create network graph.")
                st.info("Try running a new crawl to generate better network data.")
                # Skip the rest of the visualization
                fig = None

            # Limit graph size for better visualization
            if len(G.nodes()) > 100:
                st.info(f"Large network detected ({len(G.nodes())} nodes). Showing only top 100 nodes by degree.")
                # Keep only the top 100 nodes by degree
                degrees = dict(G.degree())
                top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:100]
                top_node_ids = [n for n, _ in top_nodes]
                G = G.subgraph(top_node_ids)

            # Get positions using spring layout with more iterations for better layout
            pos = nx.spring_layout(G, seed=42, iterations=100)

            # Create edge trace
            edge_x = []
            edge_y = []
            for edge in G.edges():
                if edge[0] in pos and edge[1] in pos:  # Make sure both nodes have positions
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')

            # Create node trace
            node_x = []
            node_y = []
            for node in G.nodes():
                if node in pos:  # Make sure node has a position
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    showscale=True,
                    colorscale='YlOrRd',
                    reversescale=True,
                    color=[],
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title=dict(
                            text='Node Connections',
                            side='right'
                        ),
                        xanchor='left'
                    ),
                    line_width=2))

            # Color nodes by number of connections
            node_adjacencies = []
            node_text = []
            for node in G.nodes():
                if node in pos:  # Make sure node has a position
                    adjacencies = list(G.neighbors(node))
                    node_adjacencies.append(len(adjacencies))

                    # Get page title if available
                    title = ""
                    if not urls_df.empty:
                        title_row = urls_df[urls_df['url'] == node]
                        if not title_row.empty and 'title' in title_row.columns:
                            title = title_row.iloc[0]['title']

                    # Truncate URL for display
                    display_url = node
                    if len(display_url) > 50:
                        display_url = display_url[:47] + "..."

                    node_text.append(f"{display_url}<br>Connections: {len(adjacencies)}<br>Title: {title}")

            node_trace.marker.color = node_adjacencies
            node_trace.text = node_text

            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title=dict(
                                    text='E-commerce Website Structure',
                                    font=dict(size=16)
                                ),
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='white')
                            ))
        except Exception as e:
            st.error(f"Error creating network graph: {str(e)}")
            st.info("Try running a new crawl to generate better network data.")
            fig = None

        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No links found. Start a crawl to see the website structure.")

# Network Graph tab
with tabs[3]:
    st.header("Network Graph Analysis")

    if not links_df.empty:
        try:
            # Create a more advanced network graph
            G = nx.DiGraph()

            # Add nodes and edges
            valid_edges = 0
            for _, row in links_df.iterrows():
                try:
                    if pd.notna(row['source']) and pd.notna(row['target']):
                        G.add_edge(row['source'], row['target'])
                        valid_edges += 1
                except Exception as e:
                    continue

            if valid_edges == 0:
                st.warning("No valid edges found in the data. Cannot create network graph.")
                st.info("Try running a new crawl to generate better network data.")
                # Skip the rest of the analysis
                raise ValueError("No valid edges found")

            # Calculate PageRank
            pagerank = nx.pagerank(G)

            # Get top nodes by PageRank
            top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:20]

            st.subheader("Top Pages by PageRank")

            # Display top nodes
            for i, (node, rank) in enumerate(top_nodes):
                # Get page title if available
                title = ""
                if not urls_df.empty:
                    title_row = urls_df[urls_df['url'] == node]
                    if not title_row.empty and 'title' in title_row.columns:
                        title = title_row.iloc[0]['title']

                # Truncate URL for display
                display_url = node
                if len(display_url) > 50:
                    display_url = display_url[:47] + "..."

                st.markdown(f"{i+1}. **{title or display_url}** (PageRank: {rank:.4f})")
                st.markdown(f"   URL: [{display_url}]({node})")

            # Network statistics
            st.subheader("Network Statistics")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Nodes", len(G.nodes()))

            with col2:
                st.metric("Edges", len(G.edges()))

            with col3:
                try:
                    density = nx.density(G)
                    st.metric("Network Density", f"{density:.4f}")
                except:
                    st.metric("Network Density", "N/A")

            # Degree distribution
            in_degrees = [d for _, d in G.in_degree()]
            out_degrees = [d for _, d in G.out_degree()]

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=in_degrees,
                name="In-Degree",
                opacity=0.7,
                marker=dict(color="blue")
            ))
            fig.add_trace(go.Histogram(
                x=out_degrees,
                name="Out-Degree",
                opacity=0.7,
                marker=dict(color="red")
            ))
            fig.update_layout(
                title="Degree Distribution",
                xaxis_title="Degree",
                yaxis_title="Count",
                barmode='overlay',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error creating network analysis: {str(e)}")
            st.info("Try running a new crawl to generate better network data.")
    else:
        st.info("No links found. Start a crawl to see network analysis.")

# Crawl Timeline tab
with tabs[4]:
    st.header("Crawl Timeline")

    if not urls_df.empty and 'crawled_at' in urls_df.columns and 'latency' in urls_df.columns:
        try:
            # Convert crawled_at to datetime
            urls_df['crawled_at'] = pd.to_datetime(urls_df['crawled_at'], errors='coerce')

            # Drop rows with invalid dates
            urls_df = urls_df.dropna(subset=['crawled_at'])

            if urls_df.empty:
                st.info("No valid crawl data found. Start a crawl to see timeline information.")
            else:
                # Sort by crawled_at
                urls_df_sorted = urls_df.sort_values('crawled_at')

                # Check if we have the required columns for the scatter plot
                required_columns = ['crawled_at', 'latency']
                if not all(col in urls_df_sorted.columns for col in required_columns):
                    st.warning(f"Missing required columns for timeline visualization. Required: {required_columns}")
                else:
                    # Check if we have response_code for coloring
                    color_column = 'response_code' if 'response_code' in urls_df_sorted.columns else None

                    # Check if we have title for hover
                    hover_column = 'title' if 'title' in urls_df_sorted.columns else None

                    # Check if we have size column, if not create a constant size
                    if 'size' not in urls_df_sorted.columns:
                        # Add a constant size column
                        urls_df_sorted['size_value'] = 10
                        size_column = 'size_value'
                    else:
                        size_column = 'size'

                    # Create scatter plot parameters
                    scatter_params = {
                        'data_frame': urls_df_sorted,
                        'x': 'crawled_at',
                        'y': 'latency',
                        'title': "Crawl Timeline",
                        'labels': {
                            'crawled_at': 'Time',
                            'latency': 'Response Time (s)'
                        }
                    }

                    # Add optional parameters if columns exist
                    if color_column:
                        scatter_params['color'] = color_column
                        scatter_params['labels'][color_column] = 'HTTP Status'

                    if hover_column:
                        scatter_params['hover_name'] = hover_column

                    if size_column:
                        scatter_params['size'] = size_column
                        scatter_params['labels'][size_column] = 'Page Size'

                    # Create timeline
                    fig = px.scatter(**scatter_params)

                    # Update layout
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Response time distribution
                    st.subheader("Response Time Distribution")
                    if 'latency' in urls_df.columns:
                        fig = px.histogram(
                            urls_df,
                            x='latency',
                            nbins=20,
                            title="Response Time Distribution",
                            labels={'latency': 'Response Time (s)'},
                            color_discrete_sequence=['#FF9900']
                        )
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white'),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                        )
                        st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating timeline visualization: {str(e)}")
            st.info("Try running a new crawl to generate better data.")
    else:
        st.info("No crawl data found. Start a crawl to see timeline information.")

# Data Explorer tab
with tabs[5]:
    st.header("Data Explorer")

    # Select dataset
    dataset = st.selectbox(
        "Select Dataset",
        ["Products", "URLs", "Links"]
    )

    if dataset == "Products" and not products_df.empty:
        st.subheader("Products Dataset")
        st.dataframe(products_df)

        # Download button
        csv = products_df.to_csv(index=False)
        st.download_button(
            label="Download Products CSV",
            data=csv,
            file_name="products.csv",
            mime="text/csv"
        )
    elif dataset == "URLs" and not urls_df.empty:
        st.subheader("URLs Dataset")

        # Select columns to display
        all_columns = urls_df.columns.tolist()
        selected_columns = st.multiselect(
            "Select Columns",
            all_columns,
            default=["url", "response_code", "title", "crawled_at", "latency"]
        )

        if selected_columns:
            st.dataframe(urls_df[selected_columns])
        else:
            st.dataframe(urls_df)

        # Download button
        csv = urls_df.to_csv(index=False)
        st.download_button(
            label="Download URLs CSV",
            data=csv,
            file_name="urls.csv",
            mime="text/csv"
        )
    elif dataset == "Links" and not links_df.empty:
        st.subheader("Links Dataset")
        st.dataframe(links_df)

        # Download button
        csv = links_df.to_csv(index=False)
        st.download_button(
            label="Download Links CSV",
            data=csv,
            file_name="links.csv",
            mime="text/csv"
        )
    else:
        st.info(f"No {dataset} data found. Start a crawl to see data.")
