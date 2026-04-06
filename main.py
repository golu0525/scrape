"""
Main pipeline for ISP plan scraping system
Orchestrates all providers and handles data processing
"""

import sys
from typing import List, Dict, Any
from datetime import datetime

# Import utilities
from config import (
    OUTPUT_PLANS_FILE,
    OUTPUT_LOGS_FILE,
    DB_CONFIG,
    PROVIDERS,
)
from utils.logger import JSONLogger
from utils.db import Database
from utils.save_json import JSONSaver
from utils.validator import PlanValidator


def main():
    """Main execution pipeline"""

    # Initialize logger
    logger = JSONLogger(OUTPUT_LOGS_FILE)
    logger.info("Starting ISP plan scraper pipeline")

    # Initialize database
    db = None
    try:
        db = Database(DB_CONFIG)
        db.create_table()
        logger.success("Database connection established", details={"database": DB_CONFIG["database"]})
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        print(f"Error: Cannot connect to database. {e}")
        return

    # Initialize JSON saver
    saver = JSONSaver(OUTPUT_PLANS_FILE)

    # Collect all plans from providers
    all_plans = []
    logger.info("Starting provider scraping")

    # Scrape from each provider
    provider_results = _scrape_all_providers(logger)

    for provider_name, plans in provider_results.items():
        if plans:
            all_plans.extend(plans)
            logger.success(
                f"Scraped {len(plans)} plans",
                provider=provider_name,
                details={"count": len(plans)},
            )
        else:
            logger.warning(f"No plans scraped", provider=provider_name)

    logger.info(f"Total plans collected: {len(all_plans)}")

    # Validate and clean data
    logger.info("Starting data validation")
    valid_plans, invalid_plans = PlanValidator.clean_plans(all_plans)

    if invalid_plans:
        logger.warning(
            f"Invalid plans removed: {len(invalid_plans)}",
            details={"invalid_count": len(invalid_plans)},
        )

    logger.info(f"Valid plans after validation: {len(valid_plans)}")

    # Save to database
    logger.info("Saving plans to database")
    if valid_plans:
        try:
            successful, failed = db.insert_plans_batch(valid_plans)
            logger.success(
                f"Database insert completed",
                details={"successful": successful, "failed": failed},
            )
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            print(f"Error saving to database: {e}")

    # Save to JSON file
    logger.info("Saving plans to JSON file")
    try:
        saver.save_plans(valid_plans)
        logger.success(
            f"Plans saved to JSON",
            details={"file": OUTPUT_PLANS_FILE, "count": len(valid_plans)},
        )
    except Exception as e:
        logger.error(f"JSON save failed: {e}")
        print(f"Error saving JSON: {e}")

    # Final statistics
    stats = {
        "total_plans_collected": len(all_plans),
        "valid_plans": len(valid_plans),
        "invalid_plans": len(invalid_plans),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    logger.success(
        "ISP plan scraper pipeline completed",
        details=stats,
    )

    print(f"\n{'='*50}")
    print(f"SCRAPING PIPELINE COMPLETED")
    print(f"{'='*50}")
    print(f"Total plans collected: {stats['total_plans_collected']}")
    print(f"Valid plans saved: {stats['valid_plans']}")
    print(f"Invalid plans: {stats['invalid_plans']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"JSON file: {OUTPUT_PLANS_FILE}")
    print(f"Logs file: {OUTPUT_LOGS_FILE}")
    print(f"{'='*50}\n")

    # Close database connection
    if db:
        db.close()


def _scrape_all_providers(logger: JSONLogger) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scrape plans from all providers with error handling
    
    Args:
        logger: JSONLogger instance
        
    Returns:
        Dictionary of provider_name -> list of plans
    """
    results = {}

    # Scrape Aussie (API-first)
    logger.info("Scraping Aussie Broadband...")
    try:
        from providers.aussie import scrape_aussie

        results["aussie"] = scrape_aussie()
    except Exception as e:
        logger.error(f"Aussie scraper failed: {e}", provider="aussie")
        results["aussie"] = []

    # Scrape Telstra (Playwright)
    logger.info("Scraping Telstra...")
    try:
        from providers.telstra import scrape_telstra_sync

        results["telstra"] = scrape_telstra_sync()
    except Exception as e:
        logger.error(f"Telstra scraper failed: {e}", provider="telstra")
        results["telstra"] = []

    # Scrape Optus (Playwright)
    logger.info("Scraping Optus...")
    try:
        from providers.optus import scrape_optus_sync

        results["optus"] = scrape_optus_sync()
    except Exception as e:
        logger.error(f"Optus scraper failed: {e}", provider="optus")
        results["optus"] = []

    # Scrape Superloop (Playwright)
    logger.info("Scraping Superloop...")
    try:
        from providers.superloop import scrape_superloop_sync

        results["superloop"] = scrape_superloop_sync()
    except Exception as e:
        logger.error(f"Superloop scraper failed: {e}", provider="superloop")
        results["superloop"] = []

    return results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScraper interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
