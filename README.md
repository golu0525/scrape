# ISP Plan Scraping System

A production-ready Python scraping system for extracting ISP plan data from multiple Australian broadband providers.

## Features

- **API-first approach**: Uses APIs when available (Aussie Broadband)
- **Dynamic content handling**: Uses Playwright for JavaScript-heavy sites (Telstra, Optus, Superloop)
- **Robust data validation**: Validates all plan data before persistence
- **Multi-target storage**: Saves data to MySQL database and JSON files
- **JSON logging**: All events logged to JSON (not database)
- **Retry logic**: Automatic retries for failed scrapes
- **Error handling**: Provider failures don't crash the entire system

## Supported Providers

1. **Telstra** - Playwright scraper
2. **Optus** - Playwright scraper (with retry logic)
3. **Aussie Broadband** - API-based scraper
4. **Superloop** - Playwright scraper

## Project Structure

```
/scrape
  /providers/
    telstra.py         # Telstra scraper
    optus.py           # Optus scraper
    aussie.py          # Aussie Broadband scraper (API)
    superloop.py       # Superloop scraper
  /utils/
    db.py              # MySQL database operations
    logger.py          # JSON logging
    save_json.py       # JSON file output
    validator.py       # Data validation & cleaning
  /output/
    plans.json         # Output plans file
    logs.json          # Output logs file
  config.py            # Configuration
  main.py              # Main pipeline
  requirements.txt     # Python dependencies
```

## Installation

### Prerequisites

- Python 3.11+
- MySQL 8.0+

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Configure database connection:
```bash
# Create .env file
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=isp_plans
DB_PORT=3306
```

Or set environment variables directly.

## Configuration

Edit `config.py` to customize:

- Database connection details
- Output file paths
- Provider configurations
- Playwright timeouts
- Retry settings
- Request headers

## Database Schema

The system creates a `plans_current` table with:

- `provider_id` - Provider identifier
- `plan_name` - Plan name
- `network_type` - Network type (FTTP, FTTN, etc.)
- `speed_label` - Speed category
- `download_speed` - Download speed (Mbps)
- `upload_speed` - Upload speed (Mbps)
- `monthly_price` - Monthly price (AUD)
- `promo_price` - Promotional price (if available)
- `promo_period` - Promotional period duration
- `contract_term` - Contract length
- `source_url` - Source website URL
- `last_checked` - Last check timestamp

Unique constraint: `(provider_id, plan_name, speed_label)`

## Usage

### Run the full pipeline:

```bash
python main.py
```

This will:
1. Scrape all providers
2. Validate and clean data
3. Save to MySQL database
4. Save to JSON file
5. Log all events to JSON

### Output Files

- **plans.json**: Contains all scraped and validated plans
```json
{
  "total_plans": 150,
  "plans": [
    {
      "provider_id": 1,
      "plan_name": "NBN 100",
      "speed": 100,
      "price": 89.99,
      "network_type": "FTTP",
      "source_url": "https://...",
      ...
    }
  ]
}
```

- **logs.json**: Contains all pipeline events
```json
[
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "message": "Scraped 45 plans",
    "provider": "aussie",
    "details": { "count": 45 }
  }
]
```

## Data Validation

The validator ensures:

- `plan_name` is non-empty string
- `price` is valid number ≥ 0
- `speed` is positive integer
- `provider_id` is positive integer
- Optional fields have correct types
- Removes invalid records before persistence

## Scraper Details

### Aussie Broadband (API)

- Uses public API for fastest, most reliable scraping
- Fallback to Playwright if API unavailable
- Structured API responses

### Telstra, Optus, Superloop (Playwright)

- Handles JavaScript-rendered content
- Waits for dynamic page loads
- Retry logic for timeouts
- Headless browser mode
- User-Agent spoofing

## Error Handling

- Each provider scraper wrapped in try-catch
- Provider failures don't crash pipeline
- All errors logged to logs.json
- Continues with remaining providers
- Clear error messages with provider context

## Performance Considerations

- Headless browser mode for faster scraping
- Connection pooling for database
- Batch inserts with duplicate key updates
- ~2-5 seconds per dynamic page load
- API responses typically <1 second

## Logging

All pipeline events logged to `output/logs.json`:

- Provider scraping start/completion
- Plans collected per provider
- Validation results
- Database operations
- JSON file saves
- Errors with full context

View logs:
```bash
cat output/logs.json | python -m json.tool
```

## Common Issues

### Playwright timeout errors
- Increase `PLAYWRIGHT_CONFIG["wait_selector_timeout"]` in config.py
- Check website structure hasn't changed

### Database connection errors
- Verify MySQL is running
- Check credentials in .env file
- Ensure database user has CREATE TABLE permission

### No plans scraped
- Provider website may be blocking requests
- Try updating selectors in provider files
- Check network/firewall access

## Best Practices

1. **Schedule regularly**: Run via cron or task scheduler for daily updates
2. **Monitor logs**: Check `output/logs.json` for failures
3. **Backup database**: Regular database backups recommended
4. **Update selectors**: Websites change - update selectors as needed
5. **Test individually**: Test each provider separately during development

## Extension

To add a new provider:

1. Create `providers/new_provider.py`
2. Implement scraper function returning standardized JSON
3. Add provider config to `config.py`
4. Add import/call in `main.py` `_scrape_all_providers()`
5. Test thoroughly

Scraper must return list of dicts with:
```python
{
    "provider_id": int,
    "plan_name": str,
    "speed": int,
    "price": float,
    "network_type": str,
    "source_url": str,
    # Optional:
    "upload_speed": int,
    "promo_price": float,
    "promo_period": str,
    "contract": str,
}
```

## Testing

Run individual provider scrapers:

```python
# Test Aussie API scraper
from providers.aussie import scrape_aussie
plans = scrape_aussie()
print(f"Aussie: {len(plans)} plans")

# Test Telstra Playwright scraper
from providers.telstra import scrape_telstra_sync
plans = scrape_telstra_sync()
print(f"Telstra: {len(plans)} plans")
```

## Production Deployment

1. Use systemd to run main.py
2. Implement cron job for scheduled execution
3. Set up log rotation for logs.json
4. Monitor database size and performance
5. Implement weekly database cleanup/archival
6. Use environment variables for sensitive config

## License

Proprietary - Internal use only

## Support

For issues or improvements, check:
- Website selectors (may have changed)
- Database connection settings
- Python version (use 3.11+)
- Playwright browser installation
