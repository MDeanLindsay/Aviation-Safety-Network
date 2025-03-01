import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
import logging
from datetime import datetime
import os
import random
import time
import re
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ASNScraper:
    def __init__(self, base_url: str = "https://asn.flightsafety.org"):
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session.headers.update(self.headers)

    def _make_request(self, url: str) -> requests.Response:
        """Make a request with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, verify=False, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(random.uniform(2, 5))

    def _get_page_info(self, soup: BeautifulSoup, year: int, page: int) -> Tuple[int, int, int]:
        """Extract page information and verify it matches expected patterns.
        Returns (total_accidents, start_range, end_range)"""
        
        # Check for content wrapper
        content = soup.find('div', {'id': 'contentwrapper'})
        if not content:
            raise ValueError("Content wrapper not found")
        
        # Get and verify caption
        caption = content.find('span', {'class': 'caption'})
        if not caption:
            raise ValueError("Caption not found")
        
        text = caption.get_text()
        
        # Extract total accidents
        total_match = re.search(r'(\d+)\s*occurrences', text)
        if not total_match:
            raise ValueError(f"Could not find total occurrences in: {text}")
        total_accidents = int(total_match.group(1))
        
        # Extract range if present
        range_match = re.search(r'showing occurrence\s+(\d+)\s*-\s*(\d+)', text)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
        else:
            # First page
            start = 1
            end = min(100, total_accidents)
            
        # Verify the ranges make sense
        if not (1 <= start <= end <= total_accidents):
            raise ValueError(f"Invalid range: {start}-{end} of {total_accidents}")
            
        return total_accidents, start, end

    def _get_page_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract accident links from a page."""
        links = []
        table = soup.find('table', {'class': 'hp'})
        if not table:
            raise ValueError("Table not found")
            
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            link_elem = row.find('a')
            if link_elem and 'href' in link_elem.attrs:
                full_link = self.base_url + link_elem['href']
                links.append(full_link)
        return links

    def _extract_accident_details(self, url: str) -> Dict[str, str]:
        """Extract details from an accident page."""
        details = {
            'Date': '',
            'Time': '',
            'Type': '',
            'Owner/operator': '',
            'Registration': '',
            'MSN': '',
            'Year of manufacture': '',
            'Engine model': '',
            'Fatalities': '',
            'Other fatalities': '',
            'Aircraft damage': '',
            'Category': '',
            'Location': '',
            'Phase': '',
            'Nature': '',
            'Departure airport': '',
            'Destination airport': '',
            'Investigating agency': '',
            'Confidence Rating': '',
            'URL': url
        }
        
        response = self._make_request(url)
        soup = BeautifulSoup(response.text, 'lxml')
        
        tables = soup.find_all('table')
        if tables:
            main_table = tables[0]
            rows = main_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).rstrip(':')
                    value = cells[1].get_text(strip=True)
                    if key in details:
                        details[key] = value
        
        return details

    def scrape_year(self, year: int, output_dir: str = "output") -> pd.DataFrame:
        """Scrape all accidents for a specific year."""
        # First, analyze all pages to get counts
        page = 1
        total_accidents = None
        page_counts = []
        
        print(f"\nAnalyzing pages for year {year}...")
        while True:
            url = f"{self.base_url}/database/year/{year}/{page}"
            try:
                response = self._make_request(url)
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Get page info
                page_total, start_range, end_range = self._get_page_info(soup, year, page)
                
                # Set or verify total accidents
                if total_accidents is None:
                    total_accidents = page_total
                elif total_accidents != page_total:
                    raise ValueError(f"Total accidents mismatch: {total_accidents} != {page_total}")
                
                # Get links for this page
                page_links = self._get_page_links(soup)
                page_counts.append(len(page_links))
                print(f"Page {page}: {len(page_links)} accidents (records {start_range}-{end_range})")
                
                if end_range >= total_accidents:
                    break
                    
                page += 1
                time.sleep(1)  # Small delay between analysis requests
                
            except Exception as e:
                logging.error(f"Error analyzing page {page}: {str(e)}")
                return pd.DataFrame()
        
        print(f"\nFound {total_accidents} total accidents across {page} pages")
        proceed = input("\nProceed with scraping all accidents? (y/n): ")
        if proceed.lower() != 'y':
            print("Scraping cancelled")
            return pd.DataFrame()
            
        # Reset for actual scraping
        all_samples = []
        page = 1
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"asn_accidents_{year}.csv")
        
        print(f"\nStarting to scrape all accidents...")
        while True:
            url = f"{self.base_url}/database/year/{year}/{page}"
            logging.info(f"Processing page {page}")
            
            try:
                # Get and verify page content
                response = self._make_request(url)
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Get page info and verify it
                page_total, start_range, end_range = self._get_page_info(soup, year, page)
                
                # Verify total accidents hasn't changed
                if page_total != total_accidents:
                    raise ValueError(f"Total accidents changed during scraping: {total_accidents} != {page_total}")
                
                logging.info(f"Processing accidents {start_range}-{end_range} of {total_accidents}")
                
                # Get and verify links
                page_links = self._get_page_links(soup)
                expected_links = min(100, end_range - start_range + 1)
                if len(page_links) != expected_links:
                    raise ValueError(f"Expected {expected_links} links, got {len(page_links)}")
                
                # Process all accidents on this page
                for i, link in enumerate(page_links, 1):
                    logging.info(f"Processing accident {i}/{len(page_links)} from page {page}")
                    try:
                        details = self._extract_accident_details(link)
                        all_samples.append(details)
                        
                        # Save progress
                        df = pd.DataFrame(all_samples)
                        df.to_csv(output_file, index=False)
                        logging.info(f"Progress saved: {len(all_samples)} accidents so far")
                        
                        time.sleep(random.uniform(1, 3))  # Be nice to the server
                    except Exception as e:
                        logging.error(f"Error processing {link}: {str(e)}")
                
                # Check if we've reached the end
                if end_range >= total_accidents:
                    logging.info(f"Reached end of accidents ({page} pages total)")
                    break
                    
                # Move to next page
                page += 1
                time.sleep(random.uniform(2, 4))  # Delay between pages
                
            except Exception as e:
                logging.error(f"Error processing page {page}: {str(e)}")
                break
        
        # Create final DataFrame
        df = pd.DataFrame(all_samples)
        df.to_csv(output_file, index=False)
        logging.info(f"Saved {len(df)} accidents to {output_file}")
        
        # Print summary
        print(f"\nScraped {len(df)} accidents across {page} pages")
        print(f"Total accidents in database: {total_accidents}")
        
        return df

def main():
    scraper = ASNScraper()
    scraper.scrape_year(2024)

if __name__ == "__main__":
    main() 