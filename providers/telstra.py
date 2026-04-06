"""
Telstra ISP plans scraper
Telstra does not have a public API, so we use Playwright
"""

import asyncio
from typing import List, Dict, Any, Optional
import re
from datetime import datetime


async def scrape_telstra() -> List[Dict[str, Any]]:
    """
    Scrape Telstra NBN plans
    
    Note: Telstra doesn't have a public API
    This requires Playwright to handle dynamic content
    
    Returns:
        List of plan dictionaries
    """
    from config import PROVIDERS, PLAYWRIGHT_CONFIG, RETRY_CONFIG

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Install with: pip install playwright")
        return []

    provider_config = PROVIDERS["telstra"]
    plans = []

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(headless=PLAYWRIGHT_CONFIG["headless"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # Navigate to Telstra NBN page
            await page.goto(provider_config["web_url"], timeout=PLAYWRIGHT_CONFIG["timeout"])

            # Wait for plans to load
            await page.wait_for_selector('[data-testid*="plan"]', timeout=PLAYWRIGHT_CONFIG["wait_selector_timeout"])
            await asyncio.sleep(2)

            # Extract plan data
            plan_elements = await page.query_selector_all('[data-testid*="plan-card"]')

            for element in plan_elements:
                try:
                    plan_data = await _extract_telstra_plan(element, provider_config)
                    if plan_data:
                        plans.append(plan_data)
                except Exception as e:
                    print(f"Error extracting Telstra plan: {e}")
                    continue

            await context.close()

        except Exception as e:
            print(f"Error scraping Telstra: {e}")
        finally:
            if browser:
                await browser.close()

    return plans


async def _extract_telstra_plan(
    element: Any, provider_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Extract plan details from a plan element
    
    Args:
        element: Playwright element selector
        provider_config: Provider configuration
        
    Returns:
        Plan dictionary or None
    """
    try:
        # Extract text content
        text_content = await element.text_content()

        # Extract plan name
        plan_name_elem = await element.query_selector('[data-testid*="plan-name"]')
        plan_name = await plan_name_elem.text_content() if plan_name_elem else "Unknown"
        plan_name = plan_name.strip()

        # Extract speed
        speed_elem = await element.query_selector('[data-testid*="speed"]')
        speed_text = await speed_elem.text_content() if speed_elem else ""
        speed = _extract_speed(speed_text)

        # Extract price
        price_elem = await element.query_selector('[data-testid*="price"]')
        price_text = await price_elem.text_content() if price_elem else ""
        price = _extract_price(price_text)

        if not plan_name or speed is None or price is None:
            return None

        plan = {
            "provider_id": provider_config["id"],
            "plan_name": plan_name,
            "speed": speed,
            "price": price,
            "network_type": "FTTP",  # Telstra NBN is typically FTTP
            "source_url": provider_config["web_url"],
            "upload_speed": _extract_upload_speed(text_content),
            "promo_price": _extract_promo_price(text_content),
        }

        return plan

    except Exception as e:
        print(f"Error in _extract_telstra_plan: {e}")
        return None


def _extract_speed(speed_text: str) -> Optional[int]:
    """Extract speed from text"""
    if not speed_text:
        return None

    match = re.search(r'(\d+)\s*(?:Mbps|mbps)', speed_text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def _extract_upload_speed(text: str) -> Optional[int]:
    """Extract upload speed from text"""
    if not text:
        return None

    # Look for patterns like "100/40" (down/up)
    match = re.search(r'\d+\s*/\s*(\d+)', text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def _extract_price(price_text: str) -> Optional[float]:
    """Extract price from text"""
    if not price_text:
        return None

    # Remove common words
    price_text = price_text.lower()

    # Find dollar amount
    match = re.search(r'\$?\s*(\d+(?:\.\d{2})?)', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None


def _extract_promo_price(text: str) -> Optional[float]:
    """Extract promo price if available"""
    if not text or "promo" not in text.lower():
        return None

    match = re.search(r'[^\d]*(\d+(?:\.\d{2})?)[^\d]*(?:first|promo|special)', text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None


def scrape_telstra_sync() -> List[Dict[str, Any]]:
    """Synchronous wrapper for scrape_telstra"""
    return asyncio.run(scrape_telstra())
