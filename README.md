# Aviation Safety Network Scraper

A Python-based web scraper for extracting aviation accident data from the Aviation Safety Network (ASN) database. This tool systematically collects detailed information about aviation accidents and incidents, providing structured data for analysis and research purposes.

## Overview

The scraper extracts comprehensive accident information including:
- Date and time of the incident
- Aircraft details (type, registration, MSN, year of manufacture)
- Operator information
- Casualty details
- Location and flight phase
- Airport information
- Investigation status
- Damage assessment
- Confidence rating of the information

## Features

- Year-based data extraction
- Automatic pagination handling
- Progress saving after each record
- Comprehensive error handling and retry logic
- Rate limiting to respect server resources
- Data validation and consistency checks
- CSV output format

## Requirements

- Python 3.9 or higher
- uv (Python packaging toolchain)
- Dependencies listed in `requirements.txt`

## Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/Aviation-Safety-Network.git
cd Aviation-Safety-Network
```

3. Create and activate a virtual environment:
```bash
uv venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

4. Install required packages:
```bash
uv pip install -r requirements.txt
```

## Usage

1. Basic usage to scrape all accidents for a specific year:
```bash
python asn_scraper.py
```

By default, the script will:
- Analyze all pages for the selected year.
- Display the number of accidents found on each page
- Ask for confirmation before proceeding with the full scrape
- Save results to `output/asn_accidents_YYYY.csv`

2. To use the scraper in your own code:
```python
from asn_scraper import ASNScraper

scraper = ASNScraper()
df = scraper.scrape_year(2024)
```

## Output Format

The scraper generates a CSV file with the following columns:
- Date
- Time
- Type (aircraft model)
- Owner/operator
- Registration
- MSN (Manufacturer Serial Number)
- Year of manufacture
- Engine model
- Fatalities
- Other fatalities
- Aircraft damage
- Category
- Location
- Phase
- Nature
- Departure airport
- Destination airport
- Investigating agency
- Confidence Rating
- URL

## Rate Limiting

The scraper implements responsible scraping practices:
- 1-3 second delay between individual accident records
- 2-4 second delay between pages
- Maximum 3 retry attempts for failed requests
- Progress saving after each record

## Error Handling

The scraper includes comprehensive error handling:
- Automatic retry for failed requests
- Data validation at multiple stages
- Progress saving to prevent data loss
- Detailed logging of all operations

## Legal Notice

This scraper is for educational and research purposes only. 

:)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 