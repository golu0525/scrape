"""
Database operations for ISP plans
"""

import mysql.connector
from mysql.connector import Error, pooling
from typing import List, Dict, Any, Optional
from datetime import datetime


class Database:
    """MySQL database connection and operations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database connection
        
        Args:
            config: Database configuration dictionary with
                   host, user, password, database, port
        """
        self.config = config
        self.connection = None
        self.pool = None
        self._init_connection()

    def _init_connection(self) -> None:
        """Initialize database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print(f"Connected to database: {self.config['database']}")
        except Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def create_table(self) -> None:
        """Create plans_current table if not exists"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS plans_current (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(create_table_query)
            self.connection.commit()
            print("Table created successfully")
        except Error as e:
            print(f"Error creating table: {e}")
            raise
        finally:
            cursor.close()

    def insert_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Insert or update a plan using INSERT ... ON DUPLICATE KEY UPDATE
        
        Args:
            plan: Plan dictionary with required fields
            
        Returns:
            True if successful, False otherwise
        """
        insert_query = """
        INSERT INTO plans_current 
        (provider_id, plan_name, network_type, speed_label, download_speed, 
         upload_speed, monthly_price, promo_price, promo_period, contract_term, 
         source_url, last_checked)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            network_type = VALUES(network_type),
            download_speed = VALUES(download_speed),
            upload_speed = VALUES(upload_speed),
            monthly_price = VALUES(monthly_price),
            promo_price = VALUES(promo_price),
            promo_period = VALUES(promo_period),
            contract_term = VALUES(contract_term),
            source_url = VALUES(source_url),
            last_checked = VALUES(last_checked);
        """

        try:
            cursor = self.connection.cursor()

            values = (
                plan.get("provider_id"),
                plan.get("plan_name"),
                plan.get("network_type"),
                plan.get("speed_label", plan.get("speed")),
                plan.get("speed"),  # download_speed
                plan.get("upload_speed"),
                plan.get("price"),
                plan.get("promo_price"),
                plan.get("promo_period"),
                plan.get("contract"),
                plan.get("source_url"),
                datetime.utcnow(),
            )

            cursor.execute(insert_query, values)
            self.connection.commit()
            return True

        except Error as e:
            print(f"Error inserting plan: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def insert_plans_batch(self, plans: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Insert multiple plans
        
        Args:
            plans: List of plan dictionaries
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        for plan in plans:
            if self.insert_plan(plan):
                successful += 1
            else:
                failed += 1

        return successful, failed

    def get_all_plans(self) -> List[Dict[str, Any]]:
        """
        Retrieve all plans from database
        
        Returns:
            List of plan dictionaries
        """
        query = "SELECT * FROM plans_current ORDER BY last_checked DESC;"

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            plans = cursor.fetchall()
            return plans if plans else []

        except Error as e:
            print(f"Error retrieving plans: {e}")
            return []
        finally:
            cursor.close()

    def get_plans_by_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """
        Get plans by provider
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List of plan dictionaries
        """
        query = "SELECT * FROM plans_current WHERE provider_id = %s ORDER BY plan_name;"

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (provider_id,))
            plans = cursor.fetchall()
            return plans if plans else []

        except Error as e:
            print(f"Error retrieving plans: {e}")
            return []
        finally:
            cursor.close()

    def delete_plans_by_provider(self, provider_id: int) -> bool:
        """
        Delete all plans for a provider (useful for full refresh)
        
        Args:
            provider_id: Provider ID
            
        Returns:
            True if successful, False otherwise
        """
        query = "DELETE FROM plans_current WHERE provider_id = %s;"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (provider_id,))
            self.connection.commit()
            deleted = cursor.rowcount
            print(f"Deleted {deleted} plans for provider {provider_id}")
            return True

        except Error as e:
            print(f"Error deleting plans: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def close(self) -> None:
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
