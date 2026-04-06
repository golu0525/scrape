"""
Database initialization script
Creates the plans_current table in MySQL
Run this once before starting the scraper
"""

from utils.db import Database
from config import DB_CONFIG
import sys


def init_database():
    """Initialize database and create tables"""
    print("Initializing ISP Plans database...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Database: {DB_CONFIG['database']}")
    print()

    try:
        db = Database(DB_CONFIG)
        
        # Create table
        db.create_table()
        
        # Verify table
        plans = db.get_all_plans()
        print(f"✓ Table created successfully")
        print(f"✓ Current plans in database: {len(plans)}")
        
        db.close()
        print("\n✓ Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nPlease ensure:")
        print(f"  1. MySQL is running")
        print(f"  2. Database user has CREATE TABLE permission")
        print(f"  3. .env file is configured correctly")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
