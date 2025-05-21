import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse

def create_graph_visualization(links_df, urls_file=None):
    """
    Create a simple graph visualization from links data
    
    Args:
        links_df: DataFrame containing source and target columns
        urls_file: Optional path to URLs CSV file for additional data
    
    Returns:
        dict: Dictionary with edges_df and graph_url
    """
    st.subheader("📊 Graph Visualization")
    
    try:
        # Check if we have data
        if links_df.empty:
            st.warning("No link data available for visualization. Please wait for the crawler to complete.")
            return {'edges_df': pd.DataFrame(), 'graph_url': None}
        
        # Display basic statistics
        st.metric("Total Links", len(links_df))
        st.metric("Unique Source Pages", links_df['source'].nunique())
        st.metric("Unique Target Pages", links_df['target'].nunique())
        
        # Create a graph
        G = nx.DiGraph()
        
        # Add edges
        for _, row in links_df.iterrows():
            G.add_edge(row['source'], row['target'])
        
        # Create visualization
        with st.spinner("Generating graph visualization..."):
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
            
            # Add explanation
            with st.expander("How to Read This Visualization"):
                st.write("""
                ### Understanding the Graph
                
                - **Nodes (circles)**: Each circle represents a page on the website
                - **Edges (arrows)**: Arrows show links between pages
                - **Labels**: Each node is labeled with its URL path
                
                ### What to Look For
                
                - **Central nodes**: Pages with many connections are central to the site
                - **Isolated nodes**: Pages with few connections may be hard to find
                - **Clusters**: Groups of connected pages often represent sections of the site
                """)
            
            # Return a placeholder for the graph URL
            return {
                'edges_df': links_df,
                'graph_url': 'https://example.com/graph'  # Placeholder
            }
            
    except Exception as e:
        st.error(f"Error creating graph visualization: {str(e)}")
        st.info("This may happen if the crawler hasn't collected enough data yet. Please wait for it to complete.")
        
        # Show technical details in an expander
        with st.expander("Technical Details"):
            st.code(str(e))
            
        return {'edges_df': pd.DataFrame(), 'graph_url': None}

def run_filters(links_df, link_unique, urls_file):
    """Simple wrapper around create_graph_visualization"""
    return create_graph_visualization(links_df, urls_file)
