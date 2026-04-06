"""
Superloop ISP plans scraper
Superloop does not have a public API, so we use Playwright
"""

import asyncio
from typing import List, Dict, Any, Optional
import re


async def scrape_superloop() -> List[Dict[str, Any]]:
    """
    Scrape Superloop NBN plans
    
    Note: Superloop doesn't have a public API
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

    provider_config = PROVIDERS["superloop"]
    plans = []
    retries = 0

    async with async_playwright() as p:
        browser = None
        while retries < RETRY_CONFIG["max_retries"]:
            try:
                browser = await p.chromium.launch(headless=PLAYWRIGHT_CONFIG["headless"])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                # Navigate to Superloop NBN page
                await page.goto(provider_config["web_url"], timeout=PLAYWRIGHT_CONFIG["timeout"])

                # Wait for plans to load
                try:
                    await page.wait_for_selector(
                        '[class*="plan"], [data-testid*="plan"]',
                        timeout=PLAYWRIGHT_CONFIG["wait_selector_timeout"]
                    )
                except:
                    # If plans don't load, wait and try to extract any visible content
                    await asyncio.sleep(3)

                # Extract plan data
                plan_elements = await page.query_selector_all('[class*="plan-card"]')

                if not plan_elements:
                    plan_elements = await page.query_selector_all('[class*="plan"]')

                for element in plan_elements:
                    try:
                        plan_data = await _extract_superloop_plan(element, provider_config)
                        if plan_data:
                            plans.append(plan_data)
                    except Exception as e:
                        print(f"Error extracting Superloop plan: {e}")
                        continue

                await context.close()
                break  # Success, exit retry loop

            except Exception as e:
                print(f"Error scraping Superloop (attempt {retries + 1}): {e}")
                retries += 1
                if retries < RETRY_CONFIG["max_retries"]:
                    await asyncio.sleep(RETRY_CONFIG["retry_delay"])
            finally:
                if browser:
                    await browser.close()

    return plans


async def _extract_superloop_plan(
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
        text_content = await element.text_content()

        # Extract plan name (typically in heading)
        plan_name_elem = await element.query_selector('h2, h3, h4, [class*="name"], [class*="title"]')
        plan_name = await plan_name_elem.text_content() if plan_name_elem else ""
        plan_name = plan_name.strip()

        # Extract speed
        speed = _extract_speed(text_content)

        # Extract price
        price = _extract_price(text_content)

        if not plan_name or speed is None or price is None:
            return None

        plan = {
            "provider_id": provider_config["id"],
            "plan_name": plan_name,
            "speed": speed,
            "price": price,
            "network_type": "FTTP",
            "source_url": provider_config["web_url"],
            "upload_speed": _extract_upload_speed(text_content),
        }

        return plan

    except Exception as e:
        print(f"Error in _extract_superloop_plan: {e}")
        return None


def _extract_speed(text: str) -> Optional[int]:
    """Extract speed from text"""
    if not text:
        return None

    # Try to match speed patterns
    patterns = [
        r'(\d+)\s*(?:Mbps|mbps)',  # 100Mbps
        r'Down[^0-9]*(\d+)',  # Download 100
        r'Speed[^0-9]*(\d+)',  # Speed 100
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return None


def _extract_upload_speed(text: str) -> Optional[int]:
    """Extract upload speed from text"""
    if not text:
        return None

    patterns = [
        r'\d+\s*/\s*(\d+)',  # 100/40
        r'Upload[^0-9]*(\d+)',  # Upload 40
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return None


def _extract_price(text: str) -> Optional[float]:
    """Extract price from text"""
    if not text:
        return None

    price_text = text.lower()
    match = re.search(r'\$?\s*(\d+(?:\.\d{2})?)\s*(?:/month|\/m|per month)', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Fallback: just find any dollar amount
    match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None


def scrape_superloop_sync() -> List[Dict[str, Any]]:
    """Synchronous wrapper for scrape_superloop"""
    return asyncio.run(scrape_superloop())
