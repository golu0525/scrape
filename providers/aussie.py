"""
Aussie Broadband ISP plans scraper
Aussie has a public API - use this for API-first approach
"""

from typing import List, Dict, Any, Optional
import requests
import re
from config import REQUEST_HEADERS, RETRY_CONFIG, PROVIDERS
import time


def scrape_aussie() -> List[Dict[str, Any]]:
    """
    Scrape Aussie Broadband plans using their API
    
    Returns:
        List of plan dictionaries
    """
    provider_config = PROVIDERS["aussie"]
    plans = []

    # Aussie Broadband API endpoints
    # Note: These are example endpoints - verify with actual API documentation
    api_url = "https://api.aussiebroadband.com.au/plans"

    retries = 0
    while retries < RETRY_CONFIG["max_retries"]:
        try:
            response = requests.get(api_url, headers=REQUEST_HEADERS, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse plans from API response
            if isinstance(data, list):
                api_plans = data
            elif isinstance(data, dict) and "plans" in data:
                api_plans = data["plans"]
            else:
                api_plans = []

            for api_plan in api_plans:
                try:
                    plan = _parse_aussie_plan(api_plan, provider_config)
                    if plan:
                        plans.append(plan)
                except Exception as e:
                    print(f"Error parsing Aussie plan: {e}")
                    continue

            break  # Success, exit retry loop

        except requests.exceptions.RequestException as e:
            print(f"Error scraping Aussie API (attempt {retries + 1}): {e}")
            retries += 1
            if retries < RETRY_CONFIG["max_retries"]:
                time.sleep(RETRY_CONFIG["retry_delay"])
        except Exception as e:
            print(f"Unexpected error scraping Aussie: {e}")
            break

    return plans


def _parse_aussie_plan(api_plan: Dict[str, Any], provider_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single plan from Aussie API response
    
    Args:
        api_plan: Plan data from API
        provider_config: Provider configuration
        
    Returns:
        Standardized plan dictionary or None
    """
    try:
        plan_name = api_plan.get("name", "")
        speed = _parse_speed(api_plan.get("speed", 0))
        price = _parse_price(api_plan.get("price", 0))

        if not plan_name or speed is None or price is None:
            return None

        plan = {
            "provider_id": provider_config["id"],
            "plan_name": plan_name,
            "speed": speed,
            "price": price,
            "network_type": api_plan.get("network_type", "FTTP"),
            "source_url": provider_config["web_url"],
            "contract": api_plan.get("contract_term", ""),
            "upload_speed": _parse_speed(api_plan.get("upload_speed")),
            "promo_price": _parse_price(api_plan.get("promotional_price")),
            "promo_period": api_plan.get("promotional_period", ""),
        }

        # Remove None and empty optional fields
        plan = {k: v for k, v in plan.items() if v not in (None, "")}

        return plan

    except Exception as e:
        print(f"Error in _parse_aussie_plan: {e}")
        return None


def _parse_speed(speed_value: Any) -> Optional[int]:
    """
    Parse speed value from API response
    
    Args:
        speed_value: Speed value (int, string, or None)
        
    Returns:
        Speed in Mbps or None
    """
    if speed_value is None:
        return None

    if isinstance(speed_value, int):
        return speed_value if speed_value > 0 else None

    if isinstance(speed_value, str):
        match = re.search(r'(\d+)', speed_value)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

    return None


def _parse_price(price_value: Any) -> Optional[float]:
    """
    Parse price value from API response
    
    Args:
        price_value: Price value (float, int, or string)
        
    Returns:
        Price as float or None
    """
    if price_value is None:
        return None

    if isinstance(price_value, (int, float)):
        price = float(price_value)
        return price if price >= 0 else None

    if isinstance(price_value, str):
        # Remove currency symbols and extract number
        price_str = re.sub(r'[^0-9.]', '', price_value)
        try:
            return float(price_str)
        except ValueError:
            pass

    return None


def scrape_aussie_fallback() -> List[Dict[str, Any]]:
    """
    Fallback scraper using Playwright if API is unavailable
    
    Returns:
        List of plan dictionaries
    """
    import asyncio

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Cannot use fallback scraper.")
        return []

    provider_config = PROVIDERS["aussie"]
    plans = []

    async def _scrape():
        from config import PLAYWRIGHT_CONFIG

        async with async_playwright() as p:
            browser = None
            try:
                browser = await p.chromium.launch(headless=PLAYWRIGHT_CONFIG["headless"])
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(provider_config["web_url"], timeout=PLAYWRIGHT_CONFIG["timeout"])
                await page.wait_for_selector('[data-testid*="plan"]', timeout=PLAYWRIGHT_CONFIG["wait_selector_timeout"])
                await asyncio.sleep(1)

                # Extract plans (implement similar to other providers)
                plan_elements = await page.query_selector_all('[class*="plan"]')

                for element in plan_elements:
                    try:
                        text = await element.text_content()
                        speed = _extract_speed_from_text(text)
                        price = _extract_price_from_text(text)

                        if speed and price:
                            plan = {
                                "provider_id": provider_config["id"],
                                "plan_name": text.split("\n")[0].strip(),
                                "speed": speed,
                                "price": price,
                                "network_type": "FTTP",
                                "source_url": provider_config["web_url"],
                            }
                            plans.append(plan)
                    except Exception as e:
                        print(f"Error extracting Aussie plan: {e}")

                await context.close()

            except Exception as e:
                print(f"Error in fallback scraper: {e}")
            finally:
                if browser:
                    await browser.close()

        return plans

    return asyncio.run(_scrape())


def _extract_speed_from_text(text: str) -> Optional[int]:
    """Extract speed from text"""
    match = re.search(r'(\d+)\s*(?:Mbps|mbps)', text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def _extract_price_from_text(text: str) -> Optional[float]:
    """Extract price from text"""
    match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None
