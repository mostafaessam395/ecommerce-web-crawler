import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import os
import random

# Set page title and layout
st.set_page_config(page_title="Web Crawler Visualization Demo", layout="wide")

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
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Page title
st.title("Web Crawler Visualization Demo")
st.markdown("This demo shows the visualization capabilities of the Intelligent Web Crawler & Analyzer.")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Crawlability Analysis", "Visual Sitemap", "Network Graph"])

with tab1:
    st.header("🔍 Crawlability Analysis")
    
    # Sample crawlability score
    score = 85
    
    # Display score with a metric
    st.metric("Crawlability Score", f"{score}/100")
    
    # Add a progress bar to visualize the score
    st.progress(score/100)
    
    # Add crawlability interpretation
    st.info("🔵 This site is generally crawlable with some restrictions.")
    
    # Display rules
    with st.expander("View Robots.txt Rules", expanded=True):
        # Display allowed paths
        st.write("✅ Allowed Paths:")
        st.write("- /products/*")
        st.write("- /blog/*")
        
        # Display disallowed paths
        st.write("❌ Disallowed Paths:")
        st.write("- /admin/*")
        st.write("- /private/*")
        st.write("- /cart/*")
        
        # Display crawl delay
        st.write("⏱️ Crawl Delay: 1 seconds")
        st.success("This is a minimal crawl delay.")
        
        # Display sitemaps
        st.write("🗺️ Sitemaps:")
        st.write("- [https://example.com/sitemap.xml](https://example.com/sitemap.xml)")
        st.success("Sitemaps make crawling more efficient by providing a list of URLs to crawl.")
    
    # Add recommendations
    with st.expander("Crawling Recommendations"):
        st.write("✅ **Recommended Approach**: Standard crawling with respect for robots.txt rules.")
        st.write("⚠️ **Crawl Rate**: Use a moderate crawl rate to avoid issues.")
        st.write("✅ **Depth**: Can crawl to moderate depths.")
        st.write("✅ **Sitemaps**: Use the provided sitemaps for more efficient crawling.")

with tab2:
    st.header("🗺️ Visual Sitemap")
    
    # Create sample data
    urls = [
        "https://example.com/",
        "https://example.com/products",
        "https://example.com/blog",
        "https://example.com/about",
        "https://example.com/contact",
        "https://example.com/products/item1",
        "https://example.com/products/item2",
        "https://example.com/products/item3",
        "https://example.com/blog/post1",
        "https://example.com/blog/post2",
    ]
    
    levels = [0, 1, 1, 1, 1, 2, 2, 2, 2, 2]
    pageranks = [0.9, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.2, 0.2, 0.1]
    
    urls_df = pd.DataFrame({
        'url': urls,
        'level': levels,
        'pagerank': pageranks
    })
    
    links_df = pd.DataFrame([
        {'source': urls[0], 'target': urls[1]},
        {'source': urls[0], 'target': urls[2]},
        {'source': urls[0], 'target': urls[3]},
        {'source': urls[0], 'target': urls[4]},
        {'source': urls[1], 'target': urls[5]},
        {'source': urls[1], 'target': urls[6]},
        {'source': urls[1], 'target': urls[7]},
        {'source': urls[2], 'target': urls[8]},
        {'source': urls[2], 'target': urls[9]},
    ])
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pages", len(urls_df))
    with col2:
        st.metric("Total Links", len(links_df))
    with col3:
        st.metric("Average Depth", f"{sum(levels)/len(levels):.1f}")
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add nodes
    for _, row in urls_df.iterrows():
        G.add_node(row['url'], level=row['level'], pagerank=row['pagerank'])
    
    # Add edges
    for _, row in links_df.iterrows():
        G.add_edge(row['source'], row['target'])
    
    # Create visualization
    with st.spinner("Generating sitemap visualization..."):
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Use spring layout
        pos = nx.spring_layout(G, seed=42)
        
        # Draw nodes with size based on PageRank
        node_sizes = [G.nodes[node]['pagerank'] * 1000 + 100 for node in G.nodes()]
        nx.draw_networkx_nodes(G, pos, 
                             node_color='lightblue',
                             node_size=node_sizes,
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
            elif len(path) > 20:
                path = path[:17] + '...'
            labels[node] = path
        
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Website Structure Visualization")
        plt.axis('off')
        
        # Display the plot
        st.pyplot(fig)
        
        # Add explanation
        with st.expander("How to Read This Visualization"):
            st.write("""
            ### Understanding the Sitemap
            
            - **Nodes (circles)**: Each circle represents a page on the website
            - **Size of nodes**: Larger circles indicate pages with higher PageRank (more important)
            - **Edges (arrows)**: Arrows show links between pages
            - **Labels**: Each node is labeled with its URL path
            
            ### What to Look For
            
            - **Central nodes**: Pages with many connections are central to the site
            - **Isolated nodes**: Pages with few connections may be hard to find
            - **Clusters**: Groups of connected pages often represent sections of the site
            """)

with tab3:
    st.header("🕸️ Network Graph Visualization")
    
    # Create a larger sample dataset
    base_urls = [
        "https://example.com/",
        "https://example.com/products",
        "https://example.com/blog",
        "https://example.com/about",
        "https://example.com/contact",
    ]
    
    # Generate more URLs
    all_urls = base_urls.copy()
    for base in base_urls[1:]:
        for i in range(1, 6):
            all_urls.append(f"{base}/item{i}")
    
    # Generate links
    all_links = []
    for i, source in enumerate(all_urls):
        # Home page links to all top-level pages
        if i == 0:
            for target in base_urls[1:]:
                all_links.append({'source': source, 'target': target})
        # Each section links to its items
        elif source in base_urls[1:]:
            for target in [url for url in all_urls if url.startswith(source + "/")]:
                all_links.append({'source': source, 'target': target})
        # Add some random links
        else:
            for _ in range(random.randint(0, 2)):
                target = random.choice(all_urls)
                if target != source:
                    all_links.append({'source': source, 'target': target})
    
    links_df = pd.DataFrame(all_links)
    
    # Display statistics
    st.metric("Total Nodes", links_df['source'].nunique() + links_df['target'].nunique())
    st.metric("Total Edges", len(links_df))
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add edges
    for _, row in links_df.iterrows():
        G.add_edge(row['source'], row['target'])
    
    # Create visualization
    with st.spinner("Generating network visualization..."):
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
        source_counts = links_df['source'].value_counts().head(5)
        target_counts = links_df['target'].value_counts().head(5)
        
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

# Add a footer
st.markdown("---")
st.markdown("Intelligent Web Crawler & Analyzer - Visualization Demo")
