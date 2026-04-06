"""
Save plans to JSON file
"""

import json
import os
from typing import List, Dict, Any


class JSONSaver:
    """Saves plans to JSON file"""

    def __init__(self, output_file: str):
        """
        Initialize JSON saver
        
        Args:
            output_file: Path to output JSON file
        """
        self.output_file = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def save_plans(self, plans: List[Dict[str, Any]]) -> None:
        """
        Save plans to JSON file
        
        Args:
            plans: List of plan dictionaries
        """
        with open(self.output_file, "w") as f:
            json.dump(
                {
                    "total_plans": len(plans),
                    "plans": plans,
                },
                f,
                indent=2,
                default=str,
            )

    def load_plans(self) -> List[Dict[str, Any]]:
        """
        Load plans from JSON file
        
        Returns:
            List of plans or empty list if file doesn't exist
        """
        if not os.path.exists(self.output_file):
            return []

        try:
            with open(self.output_file, "r") as f:
                data = json.load(f)
                return data.get("plans", [])
        except json.JSONDecodeError:
            return []
