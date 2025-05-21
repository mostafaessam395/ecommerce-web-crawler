import streamlit as st
import pandas as pd
import json
import os
import time
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import plotly.express as px
from components.ecommerce_crawler import EcommerceCrawler
import base64

# Set page config
st.set_page_config(
    page_title="E-commerce Crawler Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #232F3E;
    }
    .stProgress > div > div > div > div {
        background-color: #FF9900;
    }
    .css-1v3fvcr {
        background-color: #FFFFFF;
    }
    .css-1kyxreq {
        justify-content: center;
    }
    .stButton>button {
        background-color: #FF9900;
        color: white;
    }
    .stButton>button:hover {
        background-color: #FF9900;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# E-commerce logo
ecommerce_logo = "https://cdn-icons-png.flaticon.com/512/3081/3081559.png"

# Title and description
st.image(ecommerce_logo, width=150)
st.title("E-commerce Web Crawler & Analyzer")
st.markdown("This dashboard allows you to crawl and analyze e-commerce websites using advanced techniques to bypass anti-bot measures.")

# Sidebar
st.sidebar.header("Crawler Settings")

# Search query
query = st.sidebar.text_input("Search Query", "laptop")

# Advanced settings
with st.sidebar.expander("Advanced Settings", expanded=False):
    max_pages = st.slider("Maximum Pages to Crawl", 1, 20, 5,
                         help="Higher values will take longer but collect more data")

    max_depth = st.slider("Maximum Depth", 1, 5, 2,
                         help="How deep to follow links from the search results")

    stealth_mode = st.checkbox("Stealth Mode", True,
                              help="Use advanced techniques to avoid detection")

    min_delay = st.slider("Minimum Delay (seconds)", 1.0, 5.0, 2.0, 0.5,
                         help="Minimum delay between requests")

    max_delay = st.slider("Maximum Delay (seconds)", 2.0, 10.0, 5.0, 0.5,
                         help="Maximum delay between requests")

    output_dir = st.text_input("Output Directory", "ecommerce_data")

# Run crawler button
if st.sidebar.button("Start Crawling"):
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Run crawler with progress updates
    status_text.text("Starting crawler...")

    try:
        # Initialize crawler
        crawler = EcommerceCrawler(output_dir=output_dir, stealth_mode=stealth_mode)

        # Run the crawler
        status_text.text("Crawling e-commerce search results...")

        # Create a placeholder for progress updates
        progress_placeholder = st.empty()

        # Run the crawler directly (synchronously)
        try:
            # Show progress bar animation
            for progress in range(1, 100):
                # Update progress
                progress_bar.progress(progress)
                progress_placeholder.text(f"Crawling... {progress}%")

                # Sleep for a short time
                time.sleep(0.1)

            # Run the crawler
            status_text.text("Running crawler (this may take a few minutes)...")
            results = crawler.crawl(
                query=query,
                max_pages=max_pages,
                max_depth=max_depth,
                delay_range=(min_delay, max_delay)
            )

            # Update progress
            progress_bar.progress(100)
            progress_placeholder.text("Crawl completed!")

            # Save results to session state
            st.session_state.results = results
            st.session_state.crawl_completed = True

            # Rerun to show results
            st.rerun()

        except Exception as e:
            st.error(f"Error during crawling: {str(e)}")
            st.session_state.crawl_completed = False

    except Exception as e:
        st.error(f"Error during crawling: {str(e)}")
        st.session_state.crawl_completed = False

# Initialize session state
if 'crawl_completed' not in st.session_state:
    st.session_state.crawl_completed = False

# Display results if crawl is completed
if st.session_state.crawl_completed:
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Visual Sitemap", "Network Graph", "Data Explorer"])

    # Load data
    try:
        urls_df = pd.read_csv(os.path.join(output_dir, "_urls.csv"))
        links_df = pd.read_csv(os.path.join(output_dir, "_links.csv"))

        with open(os.path.join(output_dir, "sitemap.json"), "r") as f:
            sitemap = json.load(f)

        with open(os.path.join(output_dir, "network_graph.json"), "r") as f:
            graph_data = json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

    # Overview tab
    with tab1:
        st.header("Crawl Overview")

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Pages Crawled", len(urls_df))

        with col2:
            st.metric("Links Extracted", len(links_df))

        with col3:
            # Calculate unique domains
            domains = [urlparse(url).netloc for url in urls_df['url']]
            unique_domains = len(set(domains))
            st.metric("Unique Domains", unique_domains)

        with col4:
            # Calculate average latency
            avg_latency = urls_df['latency'].mean()
            st.metric("Avg. Latency (s)", f"{avg_latency:.2f}")

        # Display charts
        st.subheader("Response Status Codes")
        status_counts = urls_df['response_code'].value_counts().reset_index()
        status_counts.columns = ['Status Code', 'Count']

        fig = px.bar(status_counts, x='Status Code', y='Count',
                    color='Status Code',
                    color_discrete_map={
                        200: 'green',
                        301: 'blue',
                        302: 'blue',
                        404: 'red',
                        403: 'orange',
                        500: 'red',
                        503: 'red'
                    })
        st.plotly_chart(fig)

        # Display crawl timeline
        st.subheader("Crawl Timeline")
        urls_df['crawled_at'] = pd.to_datetime(urls_df['crawled_at'])
        urls_df = urls_df.sort_values('crawled_at')

        fig = px.line(urls_df, x='crawled_at', y=urls_df.index,
                     labels={'crawled_at': 'Time', 'y': 'Pages Crawled'},
                     title='Crawl Progress Over Time')
        st.plotly_chart(fig)

    # Visual Sitemap tab
    with tab2:
        st.header("Visual Sitemap")

        # Create a network graph
        G = nx.DiGraph()

        # Add nodes
        for node in graph_data['nodes']:
            G.add_node(node['id'], group=node['group'])

        # Add edges
        for link in graph_data['links']:
            G.add_edge(link['source'], link['target'], weight=link['value'])

        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8))

        # Use spring layout
        pos = nx.spring_layout(G, seed=42)

        # Draw nodes with different colors based on group
        node_colors = ['#FF9900' if G.nodes[node]['group'] == 1 else '#232F3E' for node in G.nodes()]

        # Draw nodes with size based on degree
        node_sizes = [100 + G.degree(node) * 10 for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos,
                             node_color=node_colors,
                             node_size=node_sizes,
                             alpha=0.8)

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
            elif len(path) > 20:
                path = path[:17] + '...'
            labels[node] = path

        nx.draw_networkx_labels(G, pos, labels, font_size=8)

        plt.title("E-commerce Website Structure")
        plt.axis('off')

        # Display the plot
        st.pyplot(fig)

        # Display sitemap as expandable sections
        st.subheader("Sitemap Structure")

        for page in sitemap:
            with st.expander(page['title'] or page['page']):
                st.write(f"**URL:** {page['page']}")

                if page['links']:
                    st.write(f"**Outgoing Links:** {len(page['links'])}")

                    # Display first 10 links
                    for i, link in enumerate(page['links'][:10]):
                        st.write(f"{i+1}. [{link}]({link})")

                    # Show message if there are more links
                    if len(page['links']) > 10:
                        st.write(f"... and {len(page['links']) - 10} more links")
                else:
                    st.write("No outgoing links found.")

    # Network Graph tab
    with tab3:
        st.header("Interactive Network Graph")

        # Create an HTML file with the D3.js visualization
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>E-commerce Network Graph</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { margin: 0; font-family: Arial, sans-serif; }
                .node circle { stroke: #fff; stroke-width: 1.5px; }
                .link { stroke: #999; stroke-opacity: 0.6; }
                .group1 { fill: #FF9900; }
                .group2 { fill: #232F3E; }
            </style>
        </head>
        <body>
            <svg width="100%" height="600"></svg>
            <script>
                const graph = GRAPH_DATA;

                const svg = d3.select("svg"),
                      width = svg.node().getBoundingClientRect().width,
                      height = +svg.attr("height");

                const simulation = d3.forceSimulation(graph.nodes)
                    .force("link", d3.forceLink(graph.links).id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2));

                const link = svg.append("g")
                    .selectAll("line")
                    .data(graph.links)
                    .join("line")
                    .attr("class", "link")
                    .attr("stroke-width", d => Math.sqrt(d.value));

                const node = svg.append("g")
                    .selectAll("circle")
                    .data(graph.nodes)
                    .join("circle")
                    .attr("class", d => "group" + d.group)
                    .attr("r", 5)
                    .call(drag(simulation));

                node.append("title")
                    .text(d => d.id);

                simulation.on("tick", () => {
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);

                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);
                });

                function drag(simulation) {
                    function dragstarted(event, d) {
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        d.fx = d.x;
                        d.fy = d.y;
                    }

                    function dragged(event, d) {
                        d.fx = event.x;
                        d.fy = event.y;
                    }

                    function dragended(event, d) {
                        if (!event.active) simulation.alphaTarget(0);
                        d.fx = null;
                        d.fy = null;
                    }

                    return d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended);
                }
            </script>
        </body>
        </html>
        """.replace("GRAPH_DATA", json.dumps(graph_data))

        # Save the HTML file
        html_file = os.path.join(output_dir, "network_graph.html")
        with open(html_file, "w") as f:
            f.write(html_content)

        # Display the HTML file in an iframe
        st.components.v1.html(html_content, height=600)

        # Add download button for the HTML file
        with open(html_file, "rb") as f:
            html_bytes = f.read()
            b64 = base64.b64encode(html_bytes).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="ecommerce_network_graph.html">Download HTML File</a>'
            st.markdown(href, unsafe_allow_html=True)

    # Data Explorer tab
    with tab4:
        st.header("Data Explorer")

        # Create subtabs
        subtab1, subtab2 = st.tabs(["Pages", "Links"])

        # Pages tab
        with subtab1:
            st.subheader("Crawled Pages")
            st.dataframe(urls_df)

            # Add download button
            csv = urls_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="ecommerce_pages.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)

        # Links tab
        with subtab2:
            st.subheader("Extracted Links")
            st.dataframe(links_df)

            # Add download button
            csv = links_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="ecommerce_links.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)

else:
    # Show instructions if crawl hasn't been run yet
    st.info("Enter a search query and click 'Start Crawling' to begin analyzing e-commerce websites.")

    # Show example visualization
    st.subheader("Example Visualization")
    example_image = "https://miro.medium.com/max/1400/1*HFAEMgZQCTIj6m4_5oYzuA.png"
    st.image(example_image, caption="Example network graph visualization")

# Footer
st.markdown("---")
st.markdown("E-commerce Web Crawler & Analyzer - Built with Streamlit, Playwright, and NetworkX")