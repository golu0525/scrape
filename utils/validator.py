"""
Data validator for ISP plans
Validates required fields and data format
"""

from typing import List, Dict, Any, Optional
import re


class PlanValidator:
    """Validates ISP plan data"""

    # Required fields for a valid plan
    REQUIRED_FIELDS = ["plan_name", "price", "speed", "provider_id"]

    # Optional fields
    OPTIONAL_FIELDS = [
        "promo_price",
        "promo_period",
        "contract",
        "upload_speed",
        "source_url",
        "network_type",
    ]

    @staticmethod
    def validate_plan(plan: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a single plan
        
        Args:
            plan: Plan data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in PlanValidator.REQUIRED_FIELDS:
            if field not in plan or plan[field] is None:
                return False, f"Missing required field: {field}"

        # Validate plan_name
        if not isinstance(plan["plan_name"], str) or len(plan["plan_name"].strip()) == 0:
            return False, "plan_name must be a non-empty string"

        # Validate price
        try:
            price = float(plan["price"])
            if price < 0:
                return False, "price cannot be negative"
        except (ValueError, TypeError):
            return False, "price must be a valid number"

        # Validate speed
        try:
            speed = int(plan["speed"])
            if speed <= 0:
                return False, "speed must be greater than 0"
        except (ValueError, TypeError):
            return False, "speed must be a valid integer"

        # Validate provider_id
        try:
            provider_id = int(plan["provider_id"])
            if provider_id <= 0:
                return False, "provider_id must be greater than 0"
        except (ValueError, TypeError):
            return False, "provider_id must be a valid integer"

        # Validate optional fields if present
        if "upload_speed" in plan and plan["upload_speed"] is not None:
            try:
                upload_speed = int(plan["upload_speed"])
                if upload_speed < 0:
                    return False, "upload_speed cannot be negative"
            except (ValueError, TypeError):
                return False, "upload_speed must be a valid integer"

        if "promo_price" in plan and plan["promo_price"] is not None:
            try:
                promo_price = float(plan["promo_price"])
                if promo_price < 0:
                    return False, "promo_price cannot be negative"
            except (ValueError, TypeError):
                return False, "promo_price must be a valid number"

        return True, None

    @staticmethod
    def clean_plans(plans: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Clean and validate plans
        
        Args:
            plans: List of plan dictionaries
            
        Returns:
            Tuple of (valid_plans, invalid_plans_with_reasons)
        """
        valid_plans = []
        invalid_plans = []

        for plan in plans:
            is_valid, error_msg = PlanValidator.validate_plan(plan)
            if is_valid:
                # Normalize data types
                cleaned_plan = PlanValidator._normalize_plan(plan)
                valid_plans.append(cleaned_plan)
            else:
                invalid_plans.append({"plan": plan, "reason": error_msg})

        return valid_plans, invalid_plans

    @staticmethod
    def _normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize plan data types
        
        Args:
            plan: Plan dictionary
            
        Returns:
            Normalized plan dictionary
        """
        normalized = dict(plan)

        # Ensure correct types
        normalized["provider_id"] = int(normalized["provider_id"])
        normalized["speed"] = int(normalized["speed"])
        normalized["price"] = float(normalized["price"])

        if "upload_speed" in normalized and normalized["upload_speed"] is not None:
            normalized["upload_speed"] = int(normalized["upload_speed"])

        if "promo_price" in normalized and normalized["promo_price"] is not None:
            normalized["promo_price"] = float(normalized["promo_price"])

        # Ensure plan_name is stripped
        normalized["plan_name"] = normalized["plan_name"].strip()

        # Remove None values for optional fields
        for field in PlanValidator.OPTIONAL_FIELDS:
            if field in normalized and normalized[field] is None:
                del normalized[field]

        return normalized

    @staticmethod
    def extract_speed_from_name(plan_name: str) -> Optional[int]:
        """
        Extract speed from plan name using regex
        
        Args:
            plan_name: Plan name string
            
        Returns:
            Speed in Mbps or None
        """
        # Match patterns like "100Mbps", "100 Mbps", "100/40 Mbps"
        patterns = [
            r'(\d+)\s*(?:Mbps|mbps)',  # 100Mbps or 100 Mbps
            r'(\d+)\s*/\s*\d+',  # 100/40
        ]

        for pattern in patterns:
            match = re.search(pattern, plan_name, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def normalize_price(price_str: str) -> Optional[float]:
        """
        Normalize price strings like "$89/month"
        
        Args:
            price_str: Price string
            
        Returns:
            Float price or None
        """
        if not isinstance(price_str, str):
            return None

        # Remove common words and symbols
        price_str = price_str.lower()
        price_str = re.sub(r'[^0-9.]', '', price_str)

        try:
            return float(price_str)
        except ValueError:
            return None
