import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

st.title("Visualization Test")

# Test matplotlib
st.subheader("Testing Matplotlib")
fig, ax = plt.subplots()
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)
ax.set_title("Simple Sine Wave")
st.pyplot(fig)

# Test networkx
st.subheader("Testing NetworkX")
G = nx.DiGraph()
G.add_node(1, name="Node 1")
G.add_node(2, name="Node 2")
G.add_node(3, name="Node 3")
G.add_edge(1, 2)
G.add_edge(2, 3)
G.add_edge(3, 1)

fig, ax = plt.subplots(figsize=(8, 6))
pos = nx.spring_layout(G)
nx.draw_networkx(G, pos, with_labels=True, node_color='lightblue', node_size=500, arrows=True)
ax.set_title("Simple Network Graph")
ax.axis('off')
st.pyplot(fig)

# Test pandas
st.subheader("Testing Pandas")
df = pd.DataFrame({
    'url': ['https://example.com/page1', 'https://example.com/page2', 'https://example.com/page3'],
    'pagerank': [0.8, 0.5, 0.3],
    'level': [1, 2, 2]
})
st.dataframe(df)

# Create a simple sitemap visualization
st.subheader("Simple Sitemap Test")
links_df = pd.DataFrame({
    'source': ['https://example.com/page1', 'https://example.com/page1', 'https://example.com/page2'],
    'target': ['https://example.com/page2', 'https://example.com/page3', 'https://example.com/page3'],
    'text': ['Link 1', 'Link 2', 'Link 3']
})

G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_node(row['url'], pagerank=row['pagerank'], level=row['level'])

for _, row in links_df.iterrows():
    if row['source'] in G and row['target'] in G:
        G.add_edge(row['source'], row['target'])

fig, ax = plt.subplots(figsize=(10, 8))
pos = nx.spring_layout(G)
node_sizes = [G.nodes[node]['pagerank'] * 1000 for node in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=node_sizes, alpha=0.8)
nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
labels = {node: node.split('/')[-1] for node in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=10)
ax.set_title("Simple Sitemap Visualization")
ax.axis('off')
st.pyplot(fig)
