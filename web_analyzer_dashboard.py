"""
Enhanced E-commerce Dashboard with advanced visualizations and insights panel
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import os
from components.ecommerce_crawler import EcommerceCrawler
from settings import config

# Set page configuration
st.set_page_config(
    page_title="Enhanced E-commerce Crawler & Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.session_state.crawler = EcommerceCrawler(output_dir=config['results_dir'])
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

# Title and description
st.title("🔍 Enhanced E-commerce Crawler & Analyzer")
st.markdown("""
This advanced tool crawls e-commerce websites to extract product information, analyze site structure,
and provide insights on crawlability and content. Use the controls below to configure and start the crawl.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Crawler Configuration")

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

    # Analyze robots.txt if enabled
    if analyze_robots:
        status_text.text("Analyzing robots.txt...")
        st.session_state.robots_data = st.session_state.crawler.analyze_robots_txt()
        st.session_state.progress = 10
        progress_bar.progress(st.session_state.progress)

    # Analyze sitemap if enabled
    if analyze_sitemap:
        status_text.text("Analyzing sitemap...")
        st.session_state.sitemap_data = st.session_state.crawler.analyze_sitemap()
        st.session_state.progress = 20
        progress_bar.progress(st.session_state.progress)

    # Start crawling
    status_text.text(f"Crawling for '{query}'...")

    # Run the crawler
    results = st.session_state.crawler.crawl(
        query=query,
        max_pages=max_pages,
        max_depth=max_depth,
        delay_range=(min_delay, max_delay)
    )

    st.session_state.crawl_results = results
    st.session_state.crawl_in_progress = False
    st.session_state.progress = 100
    progress_bar.progress(100)
    status_text.text(f"Crawl completed! Visited {len(results['visited_urls'])} pages, found {len(results['products'])} products.")

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

if os.path.exists(os.path.join(config['results_dir'], "_products.csv")):
    products_df = pd.read_csv(os.path.join(config['results_dir'], "_products.csv"))

if os.path.exists(os.path.join(config['results_dir'], "_urls.csv")):
    urls_df = pd.read_csv(os.path.join(config['results_dir'], "_urls.csv"))

if os.path.exists(os.path.join(config['results_dir'], "_links.csv")):
    links_df = pd.read_csv(os.path.join(config['results_dir'], "_links.csv"))

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
        filtered_df = products_df

        if 'price' in products_df.columns:
            # Convert price to numeric
            filtered_df['price_numeric'] = filtered_df['price'].str.replace('$', '').str.replace(',', '').astype(float)
            filtered_df = filtered_df[(filtered_df['price_numeric'] >= min_price) & (filtered_df['price_numeric'] <= max_price)]

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
        for i in range(start_idx, end_idx, 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < end_idx:
                    product = filtered_df.iloc[i + j]
                    with cols[j]:
                        st.markdown(f"<div class='insight-card'>", unsafe_allow_html=True)
                        if 'image_url' in product and product['image_url']:
                            st.image(product['image_url'], width=150)
                        st.markdown(f"**{product['title'][:50]}...**")
                        if 'price' in product:
                            st.markdown(f"**Price:** {product['price']}")
                        if 'rating' in product:
                            st.markdown(f"**Rating:** {product['rating']} ⭐")
                        if 'url' in product:
                            st.markdown(f"[View Product]({product['url']})")
                        st.markdown("</div>", unsafe_allow_html=True)
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

    if not urls_df.empty and 'crawled_at' in urls_df.columns:
        # Convert crawled_at to datetime
        urls_df['crawled_at'] = pd.to_datetime(urls_df['crawled_at'])

        # Sort by crawled_at
        urls_df_sorted = urls_df.sort_values('crawled_at')

        # Create timeline
        fig = px.scatter(
            urls_df_sorted,
            x='crawled_at',
            y='latency',
            color='response_code',
            hover_name='title',
            size='size',
            title="Crawl Timeline",
            labels={
                'crawled_at': 'Time',
                'latency': 'Response Time (s)',
                'response_code': 'HTTP Status',
                'size': 'Page Size'
            }
        )
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
