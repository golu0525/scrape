# ISP Plan Scraper - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies

**Windows:**
```bash
setup.bat
```

**Linux/macOS:**
```bash
bash setup.sh
```

**Manual:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Database

**Copy environment file:**
```bash
cp .env.example .env
```

**Edit `.env` with your MySQL credentials:**
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=isp_plans
DB_PORT=3306
```

**Create MySQL database:**
```sql
CREATE DATABASE isp_plans CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Initialize Database

```bash
python init_db.py
```

Expected output:
```
Connected to database: isp_plans
✓ Table created successfully
✓ Current plans in database: 0
✓ Database initialization complete!
```

### 4. Run the Scraper

```bash
python main.py
```

Expected output:
```
==================================================
SCRAPING PIPELINE COMPLETED
==================================================
Total plans collected: 150
Valid plans saved: 148
Invalid plans: 2
Database: isp_plans
JSON file: output/plans.json
Logs file: output/logs.json
==================================================
```

## 📁 File Structure

```
d:\projects\scrape/
├── config.py              # Configuration
├── main.py               # Main pipeline
├── init_db.py            # Database initialization
├── test_providers.py     # Provider testing
├── requirements.txt      # Dependencies
├── .env                  # Configuration (create from .env.example)
├── .env.example          # Example configuration
├── .gitignore            # Git ignore rules
├── setup.bat             # Windows setup
├── setup.sh              # Linux/Mac setup
├── README.md             # Full documentation
├── QUICK_START.md        # This file
│
├── providers/            # ISP provider scrapers
│   ├── __init__.py
│   ├── aussie.py        # API-based scraper
│   ├── telstra.py       # Playwright scraper
│   ├── optus.py         # Playwright scraper
│   └── superloop.py     # Playwright scraper
│
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── db.py            # MySQL database operations
│   ├── logger.py        # JSON logging
│   ├── save_json.py     # JSON file output
│   └── validator.py     # Data validation
│
└── output/              # Generated files
    ├── plans.json       # Scraped plans
    └── logs.json        # Pipeline logs
```

## 🧪 Testing

### Test individual components:

```bash
# Test all providers and utilities
python test_providers.py

# Output:
# ISP PLAN SCRAPER - PROVIDER TESTS
# ======================================================================
# 
# ==================================================
# Testing Data Validator
# ==================================================
# ✓ Valid plan test: True
# ✓ Invalid plan test: True (error: Missing required field: price)
# ✓ Speed extraction: 100 Mbps
# ✓ Price normalization: 89.99
# ...
```

### Test database connection:

```bash
python init_db.py
```

### Debug a specific provider:

```python
from providers.aussie import scrape_aussie
plans = scrape_aussie()
print(f"Aussie plans: {len(plans)}")
```

## 📊 Output Files

### `output/plans.json`
Contains all validated plans:
```json
{
  "total_plans": 150,
  "plans": [
    {
      "provider_id": 1,
      "plan_name": "NBN 100/20",
      "speed": 100,
      "price": 89.99,
      "network_type": "FTTP",
      "source_url": "https://...",
      "upload_speed": 20,
      ...
    }
  ]
}
```

### `output/logs.json`
Contains all pipeline events:
```json
[
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "message": "Scraped 45 plans",
    "provider": "aussie",
    "details": { "count": 45 }
  },
  {
    "timestamp": "2024-01-15T10:32:15Z",
    "status": "error",
    "message": "Telstra scraper failed: Timeout",
    "provider": "telstra",
    "details": null
  }
]
```

## 🗄️ Database

### Check scraped plans:

```sql
-- All plans
SELECT * FROM plans_current;

-- Plans by provider
SELECT * FROM plans_current WHERE provider_id = 1;

-- Summary
SELECT provider_id, COUNT(*) as count, MAX(last_checked) FROM plans_current GROUP BY provider_id;
```

### Database schema:

```sql
CREATE TABLE plans_current (
  id INT AUTO_INCREMENT PRIMARY KEY,
  provider_id INT NOT NULL,
  plan_name VARCHAR(255) NOT NULL,
  network_type VARCHAR(50),
  speed_label INT,
  download_speed INT NOT NULL,
  upload_speed INT,
  monthly_price DECIMAL(10, 2) NOT NULL,
  promo_price DECIMAL(10, 2),
  promo_period VARCHAR(100),
  contract_term VARCHAR(50),
  source_url TEXT,
  last_checked DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_plan (provider_id, plan_name, speed_label)
) ENGINE=InnoDB;
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Database
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "isp_plans",
    "port": 3306,
}

# Playwright timeouts (milliseconds)
PLAYWRIGHT_CONFIG = {
    "headless": True,
    "timeout": 30000,  # 30 seconds
    "wait_selector_timeout": 10000,  # 10 seconds
}

# Retry logic
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,  # seconds
}
```

## 🚀 Deployment

### Scheduled Execution (Cron - Linux/Mac)

```bash
# Run daily at 2 AM
0 2 * * * cd /home/user/scrape && /home/user/scrape/venv/bin/python main.py >> logs/cron.log 2>&1
```

### Scheduled Execution (Windows Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task: "ISP Plan Scraper"
3. Trigger: Daily at 2:00 AM
4. Action: Run program
   - Program: `C:\projects\scrape\venv\Scripts\python.exe`
   - Arguments: `C:\projects\scrape\main.py`
   - Start in: `C:\projects\scrape`

## 🆘 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database connection error

**Solution:**
1. Verify MySQL is running
2. Check `.env` credentials
3. Ensure database exists:
   ```sql
   SHOW DATABASES;
   ```

### Issue: Playwright timeout on dynamic sites

**Solution:**
1. Increase timeout in `config.py`:
   ```python
   "timeout": 60000,  # 60 seconds
   "wait_selector_timeout": 20000,  # 20 seconds
   ```
2. Check if website structure changed
3. Run with Playwright inspector:
   ```bash
   PWDEBUG=1 python main.py
   ```

### Issue: No plans scraped from provider

**Possible causes:**
- Website layout changed → update CSS selectors
- Provider blocking requests → check IP/user-agent
- API endpoint changed → verify URL
- Page not loading → check network

**Debug:**
```python
# Test individual provider
from providers.aussie import scrape_aussie
plans = scrape_aussie()
print(json.dumps(plans[:1], indent=2))
```

### Issue: JSON encoding errors

**Solution:**
```python
# Ensure datetime objects use default=str
json.dump(data, f, default=str)
```

## 📝 Logs

View pipeline logs:

```bash
# Human-readable format
python -m json.tool output/logs.json | less

# Recent errors only
python -c "import json; logs=[l for l in json.load(open('output/logs.json')) if l['status']=='error']; print('\\n'.join([str(l) for l in logs]))"

# Stats by provider
python -c "
import json
from collections import Counter
logs = json.load(open('output/logs.json'))
providers = [l['provider'] for l in logs if l['provider']]
print(Counter(providers))
"
```

## 🎯 Next Steps

1. **Test the setup:**
   ```bash
   python test_providers.py
   ```

2. **Run the scraper:**
   ```bash
   python main.py
   ```

3. **Query the database:**
   ```bash
   mysql isp_plans -e "SELECT COUNT(*) FROM plans_current;"
   ```

4. **Check output files:**
   ```bash
   cat output/plans.json | python -m json.tool | head -50
   cat output/logs.json | python -m json.tool
   ```

5. **Set up scheduled execution** (see Deployment section)

## 📞 Support

For issues:

1. Check `output/logs.json` for error details
2. Run `python test_providers.py`
3. Review provider-specific selectors if website changed
4. Check database connection settings

## 📚 Learn More

- Full documentation: `README.md`
- Configuration: `config.py`
- Database schema: `utils/db.py`
- Validation rules: `utils/validator.py`

---

**Version:** 1.0  
**Last Updated:** 2024-01-15  
**Status:** Production Ready ✓
