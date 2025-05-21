import asyncio
import argparse
import os
import time
import logging
from components.browser_crawler import BrowserCrawler
import pandas as pd
import networkx as nx
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BrowserCrawlerRunner')

def calculate_pagerank(links_df):
    """Calculate PageRank for the crawled pages"""
    if links_df.empty:
        return {}
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add edges from the links dataframe
    for _, row in links_df.iterrows():
        G.add_edge(row['source'], row['target'])
    
    # Calculate PageRank
    pagerank = nx.pagerank(G, alpha=0.85)
    
    return pagerank

def update_pagerank(urls_file, pagerank):
    """Update the PageRank values in the URLs file"""
    if not pagerank:
        return
    
    # Read the URLs file
    urls_df = pd.read_csv(urls_file)
    
    # Update the PageRank values
    urls_df['pagerank'] = urls_df['url'].map(pagerank).fillna(0)
    
    # Save the updated URLs file
    urls_df.to_csv(urls_file, index=False)
    
    logger.info(f"Updated PageRank values in {urls_file}")

def get_domain_folder(url):
    """Get the domain folder name from the URL"""
    domain = urlparse(url).netloc
    return domain.replace('.', '-').lower()

async def main():
    parser = argparse.ArgumentParser(description="Browser-based web crawler for JavaScript-heavy sites")
    parser.add_argument("--url", help="URL to crawl", required=True)
    parser.add_argument("--max-pages", help="Maximum number of pages to crawl", type=int, default=50)
    parser.add_argument("--max-depth", help="Maximum depth to crawl", type=int, default=3)
    parser.add_argument("--min-delay", help="Minimum delay between requests (seconds)", type=float, default=2.0)
    parser.add_argument("--max-delay", help="Maximum delay between requests (seconds)", type=float, default=5.0)
    parser.add_argument("--output-dir", help="Output directory", default="crowl/data")
    
    args = parser.parse_args()
    
    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create a domain-specific folder
    domain_folder = get_domain_folder(args.url)
    os.makedirs(os.path.join(args.output_dir, domain_folder), exist_ok=True)
    
    # Create a browser crawler
    crawler = BrowserCrawler(output_dir=args.output_dir, project_name=domain_folder)
    
    # Start the crawl
    logger.info(f"Starting crawl of {args.url} with max {args.max_pages} pages and depth {args.max_depth}")
    start_time = time.time()
    
    # Run the crawler
    _, links_data = await crawler.crawl(
        args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_range=(args.min_delay, args.max_delay)
    )
    
    # Calculate PageRank
    if links_data:
        links_df = pd.DataFrame(links_data)
        pagerank = calculate_pagerank(links_df)
        
        # Update the PageRank values in the URLs file
        urls_file = os.path.join(args.output_dir, domain_folder, '_urls.csv')
        update_pagerank(urls_file, pagerank)
    
    # Log completion
    elapsed_time = time.time() - start_time
    logger.info(f"Crawl completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
