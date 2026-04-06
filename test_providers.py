"""
Test script for individual provider scrapers
Use this to debug and verify each provider works correctly
"""

import json
from datetime import datetime


def test_aussie():
    """Test Aussie Broadband scraper"""
    print("\n" + "="*50)
    print("Testing Aussie Broadband Scraper")
    print("="*50)
    
    try:
        from providers.aussie import scrape_aussie
        plans = scrape_aussie()
        
        print(f"✓ Scraped {len(plans)} plans")
        
        if plans:
            print(f"\nFirst plan:")
            print(json.dumps(plans[0], indent=2, default=str))
        
        return len(plans) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_telstra():
    """Test Telstra scraper"""
    print("\n" + "="*50)
    print("Testing Telstra Scraper")
    print("="*50)
    print("Note: Requires Playwright and may take 30+ seconds")
    
    try:
        from providers.telstra import scrape_telstra_sync
        plans = scrape_telstra_sync()
        
        print(f"✓ Scraped {len(plans)} plans")
        
        if plans:
            print(f"\nFirst plan:")
            print(json.dumps(plans[0], indent=2, default=str))
        
        return len(plans) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_optus():
    """Test Optus scraper"""
    print("\n" + "="*50)
    print("Testing Optus Scraper")
    print("="*50)
    print("Note: Requires Playwright and may take 30+ seconds")
    
    try:
        from providers.optus import scrape_optus_sync
        plans = scrape_optus_sync()
        
        print(f"✓ Scraped {len(plans)} plans")
        
        if plans:
            print(f"\nFirst plan:")
            print(json.dumps(plans[0], indent=2, default=str))
        
        return len(plans) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_superloop():
    """Test Superloop scraper"""
    print("\n" + "="*50)
    print("Testing Superloop Scraper")
    print("="*50)
    print("Note: Requires Playwright and may take 30+ seconds")
    
    try:
        from providers.superloop import scrape_superloop_sync
        plans = scrape_superloop_sync()
        
        print(f"✓ Scraped {len(plans)} plans")
        
        if plans:
            print(f"\nFirst plan:")
            print(json.dumps(plans[0], indent=2, default=str))
        
        return len(plans) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_validator():
    """Test data validator"""
    print("\n" + "="*50)
    print("Testing Data Validator")
    print("="*50)
    
    from utils.validator import PlanValidator
    
    # Test valid plan
    valid_plan = {
        "provider_id": 1,
        "plan_name": "Test Plan",
        "speed": 100,
        "price": 89.99,
    }
    
    is_valid, error = PlanValidator.validate_plan(valid_plan)
    print(f"✓ Valid plan test: {is_valid}")
    
    # Test invalid plan (missing price)
    invalid_plan = {
        "provider_id": 1,
        "plan_name": "Test Plan",
        "speed": 100,
    }
    
    is_valid, error = PlanValidator.validate_plan(invalid_plan)
    print(f"✓ Invalid plan test: {not is_valid} (error: {error})")
    
    # Test speed extraction
    speed = PlanValidator.extract_speed_from_name("NBN 100Mbps Plan")
    print(f"✓ Speed extraction: {speed} Mbps")
    
    # Test price normalization
    price = PlanValidator.normalize_price("$89.99/month")
    print(f"✓ Price normalization: ${price}")
    
    return True


def test_logger():
    """Test JSON logger"""
    print("\n" + "="*50)
    print("Testing JSON Logger")
    print("="*50)
    
    from utils.logger import JSONLogger
    from config import OUTPUT_LOGS_FILE
    import os
    
    # Remove old test logs
    if os.path.exists(OUTPUT_LOGS_FILE):
        os.remove(OUTPUT_LOGS_FILE)
    
    logger = JSONLogger(OUTPUT_LOGS_FILE)
    
    # Test different log types
    logger.success("Test success message", provider="test")
    logger.error("Test error message", provider="test")
    logger.warning("Test warning message", provider="test")
    logger.info("Test info message", provider="test")
    
    # Read and display logs
    logs = logger._load_logs()
    print(f"✓ Logged {len(logs)} events")
    print(f"✓ Log file: {OUTPUT_LOGS_FILE}")
    
    if logs:
        print(f"\nFirst log entry:")
        print(json.dumps(logs[0], indent=2))
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("ISP PLAN SCRAPER - PROVIDER TESTS")
    print("="*70)
    
    results = {
        "aussie": False,
        "telstra": False,
        "optus": False,
        "superloop": False,
        "validator": False,
        "logger": False,
    }
    
    # Test utilities first
    results["validator"] = test_validator()
    results["logger"] = test_logger()
    
    # Test providers (comment out if Playwright not installed)
    print("\n" + "="*70)
    print("PROVIDER TESTS (requires Playwright)")
    print("="*70)
    
    results["aussie"] = test_aussie()
    # Uncomment to test Playwright scrapers (slower):
    # results["telstra"] = test_telstra()
    # results["optus"] = test_optus()
    # results["superloop"] = test_superloop()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:15} {status}")
    
    total = sum(1 for r in results.values() if r)
    print(f"\n{total}/{len(results)} tests passed")
    
    return total == len(results)


if __name__ == "__main__":
    import sys
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
