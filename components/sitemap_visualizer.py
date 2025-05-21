import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import pandas as pd

class SitemapVisualizer:
    """A simplified sitemap visualizer that creates a network graph of a website's structure."""

    def display_sitemap(self, urls_df, links_df):
        """Display a visual sitemap of the website structure."""
        st.subheader("🗺️ Visual Sitemap")

        # Check if we have data to visualize
        if urls_df.empty or links_df.empty:
            st.warning("No data available for visualization. Please wait for the crawler to collect data.")
            return

        try:
            # Create a new graph
            G = nx.DiGraph()

            # Add nodes (URLs) to the graph
            for _, row in urls_df.iterrows():
                url = row['url']
                G.add_node(url,
                          title=row.get('title', ''),
                          level=row.get('level', 0),
                          pagerank=row.get('pagerank', 0))

            # Add edges (links) to the graph
            for _, row in links_df.iterrows():
                source = row['source']
                target = row['target']
                if source in G.nodes() and target in G.nodes():
                    G.add_edge(source, target)

            # Check if we have nodes in the graph
            if len(G.nodes()) == 0:
                st.warning("No nodes found in the graph. The crawler may not have collected enough data yet.")
                return

            # Display statistics
            st.metric("Total Pages", len(G.nodes()))
            st.metric("Total Links", len(G.edges()))

            # Limit the number of nodes for visualization if there are too many
            if len(G.nodes()) > 50:
                st.warning(f"Large dataset detected ({len(G.nodes())} URLs). Showing only top 50 by PageRank.")

                # Get the top 50 nodes by PageRank
                pageranks = {node: G.nodes[node].get('pagerank', 0) for node in G.nodes()}
                top_nodes = sorted(pageranks.items(), key=lambda x: x[1], reverse=True)[:50]
                top_node_ids = [node[0] for node in top_nodes]

                # Create a subgraph with only the top nodes
                G = G.subgraph(top_node_ids)

            # Create the visualization
            with st.spinner("Generating sitemap visualization..."):
                fig, ax = plt.subplots(figsize=(10, 8))

                # Use spring layout for better visualization
                pos = nx.spring_layout(G, seed=42)

                # Draw nodes with size based on PageRank
                node_sizes = [G.nodes[node].get('pagerank', 0.1) * 1000 + 100 for node in G.nodes()]
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

                # Add simplified labels (just the path part of the URL)
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

        except Exception as e:
            st.error(f"Error creating sitemap visualization: {str(e)}")
            st.info("This may happen if the crawler hasn't collected enough data yet. Please wait for it to complete.")

            # Show technical details in an expander
            with st.expander("Technical Details"):
                st.code(str(e))