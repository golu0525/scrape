"""
JSON Logger for ISP plan scraper
Appends logs to logs.json
"""

import json
import os
from datetime import datetime
from typing import Any, Optional


class JSONLogger:
    """Logs events to JSON file"""

    def __init__(self, log_file: str):
        """
        Initialize logger
        
        Args:
            log_file: Path to logs.json file
        """
        self.log_file = log_file
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        """Ensure log file exists with empty array if needed"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f)

    def _load_logs(self) -> list:
        """Load existing logs"""
        try:
            with open(self.log_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_logs(self, logs: list) -> None:
        """Save logs to file"""
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=2)

    def log(
        self,
        status: str,
        message: str,
        provider: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """
        Log an event
        
        Args:
            status: "success", "error", "warning", "info"
            message: Log message
            provider: Provider name (optional)
            details: Additional details (optional)
        """
        logs = self._load_logs()

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": status.lower(),
            "message": message,
            "provider": provider,
            "details": details,
        }

        logs.append(log_entry)
        self._save_logs(logs)

    def success(self, message: str, provider: Optional[str] = None, **details) -> None:
        """Log success"""
        self.log("success", message, provider, details if details else None)

    def error(self, message: str, provider: Optional[str] = None, **details) -> None:
        """Log error"""
        self.log("error", message, provider, details if details else None)

    def warning(self, message: str, provider: Optional[str] = None, **details) -> None:
        """Log warning"""
        self.log("warning", message, provider, details if details else None)

    def info(self, message: str, provider: Optional[str] = None, **details) -> None:
        """Log info"""
        self.log("info", message, provider, details if details else None)
