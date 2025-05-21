# E-commerce Web Crawler & Analyzer

This project is a comprehensive web crawler and analyzer capable of crawling JavaScript-heavy e-commerce websites, extracting key metadata, and visualizing the results through an interactive dashboard.

## Project Overview

The E-commerce Web Crawler & Analyzer is designed to help users extract and analyze product data from e-commerce websites. It provides valuable insights through data visualization and network analysis, making it a powerful tool for market research, price monitoring, and competitive analysis.

### Key Capabilities

- **Intelligent Crawling**: Adaptively crawls e-commerce websites with prioritization of high-value pages
- **Product Data Extraction**: Extracts detailed product information including prices, ratings, and images
- **Anti-Detection Measures**: Implements sophisticated techniques to avoid being blocked
- **Interactive Dashboard**: Visualizes the extracted data through an intuitive Streamlit interface
- **Network Analysis**: Analyzes the website structure and calculates PageRank for important pages

## Features

- **Intelligent Web Crawler**:
  - Uses Playwright for JavaScript-heavy e-commerce sites
  - Implements adaptive crawling with page prioritization
  - Handles pagination and product detail pages
  - Extracts structured data from complex layouts

- **Anti-Detection System**:
  - Rotates user agents to mimic different browsers
  - Implements random delays between requests
  - Uses exponential backoff for retry logic
  - Handles CAPTCHAs and access denied responses

- **Data Extraction**:
  - Product titles, prices, and descriptions
  - Ratings and review counts
  - Product images and URLs
  - Availability and shipping information
  - Brand and category information

- **Crawlability Analysis**:
  - Analyzes robots.txt files for allowed/disallowed paths
  - Calculates crawlability score based on restrictions
  - Identifies sitemaps and analyzes their structure
  - Provides insights on crawling limitations

- **Interactive Dashboard**:
  - Overview of crawl statistics and metrics
  - Product catalog with filtering and pagination
  - Price distribution and rating analysis
  - Visual sitemap of website structure
  - Network graph with PageRank analysis
  - Crawl timeline and performance metrics

- **Data Export**:
  - CSV export of all collected data
  - Network graph export for further analysis
  - Structured JSON output of crawl results

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

### Step 1: Clone or Download the Repository
```bash
git clone https://github.com/yourusername/ecommerce-web-crawler.git
cd ecommerce-web-crawler
```

### Step 2: Install Dependencies
The project includes a script to automatically install all required dependencies:

```bash
python install_ecommerce_crawler.py
```

This will install the following packages:
- Streamlit
- Pandas
- NetworkX
- Matplotlib
- Plotly
- BeautifulSoup4
- Requests
- Playwright (for browser-based crawling)
- Langdetect
- And other dependencies

### Step 3: Install Playwright Browsers
After installing the dependencies, you need to install the Playwright browsers:

```bash
python -m playwright install chromium
```

## Usage

### Running the Crawler Locally

To start the crawler and dashboard:

```bash
python start_crawler.py --mode ecommerce
```

This will launch a Streamlit dashboard in your default web browser at `http://localhost:8501`.

### Using the Dashboard

1. **Configure Crawler Settings**:
   - Enter a search query in the sidebar (e.g., "laptop", "smartphone")
   - Adjust the maximum number of pages to crawl
   - Set the crawl depth
   - Configure advanced settings like delay between requests

2. **Start Crawling**:
   - Click the "Start Crawling" button in the sidebar
   - The crawler will begin fetching data from e-commerce websites
   - Progress will be displayed in real-time

3. **Explore Results**:
   - Navigate through the different tabs to explore the data
   - View product information, price distributions, and ratings
   - Analyze the website structure through the network graph
   - Export data for further analysis

## Project Structure

- `web_analyzer_dashboard.py`: Enhanced dashboard with advanced visualizations
- `product_crawler_dashboard.py`: Standard dashboard for product crawling
- `components/ecommerce_crawler.py`: Main crawler implementation
- `settings.py`: Configuration settings
- `start_crawler.py`: Entry point for running the crawler
- `install_ecommerce_crawler.py`: Script to install dependencies
- `ecommerce_data/`: Directory where crawled data is stored

## Deployment

### Deploying to Streamlit Cloud

1. **Create a GitHub Repository**:
   - Push your project to a GitHub repository
   - Make sure to include a `requirements.txt` file

2. **Sign Up for Streamlit Cloud**:
   - Go to [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with your GitHub account

3. **Deploy Your App**:
   - Click "New app"
   - Select your repository, branch, and the main file (`web_analyzer_dashboard.py`)
   - Click "Deploy"

4. **Configure Resources**:
   - Adjust memory and CPU settings as needed
   - Set any required environment variables

### Deploying to a Local Web Server

For more control, you can deploy the app to a local web server:

1. **Install a Web Server**:
   - Install Nginx or Apache

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure the Web Server**:
   - Set up a proxy to forward requests to the Streamlit app
   - Example Nginx configuration:
   ```
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

4. **Run the App as a Service**:
   - Create a systemd service or use a process manager like Supervisor
   - Example systemd service file:
   ```
   [Unit]
   Description=E-commerce Web Crawler
   After=network.target

   [Service]
   User=yourusername
   WorkingDirectory=/path/to/ecommerce-web-crawler
   ExecStart=/path/to/ecommerce-web-crawler/venv/bin/python start_crawler.py --mode ecommerce
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

## Findings and Insights

During the development and testing of this crawler, we discovered several interesting insights:

1. **E-commerce Website Structure**:
   - Most e-commerce websites follow a similar hierarchical structure
   - Product pages typically have the highest PageRank
   - Category pages serve as important hubs in the network

2. **Anti-Bot Measures**:
   - Modern e-commerce sites employ sophisticated anti-bot techniques
   - Rotating user agents and implementing delays significantly improves success rates
   - Browser-based crawling with Playwright is essential for JavaScript-heavy sites

3. **Data Extraction Challenges**:
   - Product information is often loaded dynamically via JavaScript
   - Price information may be displayed in various formats
   - Rating systems vary across different platforms

4. **Performance Considerations**:
   - Network requests are the main bottleneck in crawling speed
   - Intelligent prioritization of pages improves efficiency
   - Parallel crawling must be balanced with respect for the website's resources

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- NetworkX for graph analysis
- Streamlit for the interactive dashboard
- Playwright for browser automation
- The open-source community for various libraries used in this project
