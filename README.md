# ISP Plan Scraping System

A production-ready ISP plan scraping system that extracts plan data from multiple Australian internet service providers.

## Features

- **Multi-Provider Support**: Scrapes from Telstra, Optus, Aussie Broadband, and Superloop
- **API-First Approach**: Prioritizes API access when available, falls back to Playwright for dynamic websites
- **Dual Storage**: Saves data to both MySQL database and JSON files
- **JSON Logging**: All logs stored in JSON format (not database)
- **Data Validation**: Comprehensive validation ensures data quality
- **Error Handling**: Robust error handling prevents system-wide failures
- **Modular Architecture**: Clean, reusable code structure

## Installation

### 1. Install Python Dependencies

```bash
cd scrape
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```

### 3. Configure Database

Update the database configuration in `config.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'isp_plans',
    'port': 3306
}
```

### 4. Create Database

```sql
CREATE DATABASE isp_plans;
```

## Usage

### Run the Complete Pipeline

```bash
python main.py
```

This will:
1. Scrape all providers
2. Validate and clean data
3. Save to MySQL database
4. Save to JSON file
5. Log all operations

### Run Individual Provider Scrapers

```python
from providers import telstra

plans = telstra.scrape_telstra_plans()
```

## Project Structure

```
scrape/
├── providers/
│   ├── telstra.py       # Telstra scraper
│   ├── optus.py         # Optus scraper
│   ├── aussie.py        # Aussie Broadband scraper
│   └── superloop.py     # Superloop scraper
├── utils/
│   ├── db.py            # Database operations
│   ├── logger.py        # JSON logging
│   ├── save_json.py     # JSON file operations
│   └── validator.py     # Data validation
├── output/
│   ├── plans.json       # Scraped plans output
│   └── logs.json        # Log file
├── config.py            # Configuration settings
├── main.py              # Main pipeline
└── requirements.txt     # Python dependencies
```

## Database Schema

### Table: `plans_current`

| Column | Type | Description |
|--------|------|-------------|
| provider_id | INT | Provider identifier |
| plan_name | VARCHAR(255) | Name of the plan |
| network_type | VARCHAR(50) | Network technology (NBN, FTTP, etc.) |
| speed_label | INT | Speed tier label |
| download_speed | INT | Download speed in Mbps |
| upload_speed | INT | Upload speed in Mbps |
| monthly_price | DECIMAL(10,2) | Regular monthly price |
| promo_price | DECIMAL(10,2) | Promotional price |
| promo_period | VARCHAR(50) | Promotional period |
| contract_term | VARCHAR(50) | Contract duration |
| source_url | TEXT | Source URL |
| last_checked | DATETIME | Last verification timestamp |

**Unique Key**: (provider_id, plan_name, speed_label)

## Provider IDs

- Telstra: 1
- Optus: 2
- Aussie Broadband: 3
- Superloop: 4

## Data Validation Rules

All plans must have:
- ✅ Non-empty `plan_name`
- ✅ Valid `price` (positive number)
- ✅ Valid `speed` (positive integer)

Invalid records are logged and excluded from output.

## Logging

All logs are stored in `output/logs.json` with the following structure:

```json
{
  "timestamp": "2026-04-20T10:30:00",
  "status": "success|error|warning|info",
  "message": "Description of the event",
  "provider": "provider_name",
  "data": {}
}
```

## Error Handling

- Each provider scraper is isolated (failures don't crash the entire system)
- Retry logic for network requests
- Graceful fallback from API to Playwright scraping
- Comprehensive error logging

## Customization

### Adding a New Provider

1. Create a new file in `providers/` directory
2. Implement the `scrape_<provider>_plans()` function
3. Add provider configuration to `config.py`
4. Import and add to the scrapers list in `main.py`

### Modifying Selectors

Update the CSS selectors in each provider's `extract_plan_from_card()` function based on the actual website structure.

## Notes

- **API Endpoints**: The API URLs in the code are placeholders. Update them with actual API endpoints if available.
- **Website Changes**: If provider websites change their structure, update the Playwright selectors accordingly.
- **Rate Limiting**: Consider adding delays between requests to avoid being blocked.

## License

MIT License
