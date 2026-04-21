"""
Telstra ISP plan scraper.
Uses API-first approach, falls back to Playwright if needed.
"""

import requests
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
import config
from utils.logger import log_info, log_error, log_success
from utils.stealth import create_stealth_browser, create_stealth_page


# Telstra API endpoint (example - update with actual API if available)
TELSTRA_API_URL = "https://www.telstra.com.au/content/api/plans"
TELSTRA_WEBSITE_URL = "https://www.telstra.com.au/internet/nbn"


def scrape_telstra_plans() -> List[Dict[str, Any]]:
    """
    Scrape Telstra ISP plans.
    First attempts API, falls back to Playwright scraping.
    
    Returns:
        List of plan dictionaries
    """
    log_info("Starting Telstra scraper", provider="telstra")
    
    # Try API first
    try:
        plans = scrape_via_api()
        if plans:
            log_success(f"Successfully scraped {len(plans)} plans via API", provider="telstra")
            return plans
    except Exception as e:
        log_info("API scraping failed, falling back to Playwright", provider="telstra", 
                data={'error': str(e)})
    
    # Fallback to Playwright
    try:
        plans = scrape_via_playwright()
        if plans:
            log_success(f"Successfully scraped {len(plans)} plans via Playwright", provider="telstra")
            return plans
    except Exception as e:
        log_error(f"Playwright scraping failed: {str(e)}", provider="telstra")
    
    log_error("All scraping methods failed for Telstra", provider="telstra")
    return []


def scrape_via_api() -> List[Dict[str, Any]]:
    """
    Scrape Telstra plans using their API.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    try:
        response = requests.get(TELSTRA_API_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse API response (adjust based on actual API structure)
        if isinstance(data, dict) and 'plans' in data:
            for plan_data in data['plans']:
                plan = parse_telstra_api_plan(plan_data)
                if plan:
                    plans.append(plan)
        
    except requests.exceptions.RequestException as e:
        log_error(f"API request failed: {str(e)}", provider="telstra")
    except Exception as e:
        log_error(f"API parsing failed: {str(e)}", provider="telstra")
    
    return plans


def parse_telstra_api_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Telstra API plan response into standardized format.
    
    Args:
        plan_data: Raw plan data from API
    
    Returns:
        Standardized plan dictionary
    """
    try:
        return {
            'provider_id': config.PROVIDERS['telstra']['id'],
            'plan_name': plan_data.get('name', ''),
            'network_type': plan_data.get('networkType', 'NBN'),
            'speed': int(plan_data.get('speed', 0)),
            'download_speed': int(plan_data.get('downloadSpeed', plan_data.get('speed', 0))),
            'upload_speed': int(plan_data.get('uploadSpeed', 0)),
            'price': float(plan_data.get('monthlyPrice', 0)),
            'promo_price': float(plan_data.get('promoPrice', 0)) if plan_data.get('promoPrice') else None,
            'promo_period': plan_data.get('promoPeriod', ''),
            'contract': plan_data.get('contractTerm', 'No Contract'),
            'source_url': TELSTRA_WEBSITE_URL
        }
    except Exception as e:
        log_error(f"Failed to parse Telstra API plan: {str(e)}", provider="telstra")
        return None


def scrape_via_playwright() -> List[Dict[str, Any]]:
    """
    Scrape Telstra plans using Playwright (for dynamic websites).
    Uses data attributes from Telstra's plan card components.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    with sync_playwright() as p:
        browser = create_stealth_browser(p)
        page = create_stealth_page(browser)
        
        try:
            page.goto(TELSTRA_WEBSITE_URL, timeout=config.PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # Wait for plan card headers to appear
            page.wait_for_selector('.planCardHeader', timeout=15000, state='attached')
            
            # Extract plans using data attributes (most reliable method)
            plans = extract_plans_from_data_attributes(page)
            
            # Deduplicate plans by name+price
            plans = deduplicate_plans(plans)
            
        except Exception as e:
            log_error(f"Playwright scraping error: {str(e)}", provider="telstra")
        finally:
            browser.close()
    
    return plans


def extract_plans_from_data_attributes(page) -> List[Dict[str, Any]]:
    """
    Extract plans using data attributes embedded in Telstra's HTML.
    Falls back to parsing structured data from the page.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    seen = set()
    
    # Get plan names from header headlines
    headers = page.query_selector_all('h3.tcom-fixed-plan-card-header__headline')
    prices = page.query_selector_all('[data-fixed-plan-card-price]')
    downloads = page.query_selector_all('[data-tcom-fixed-plancard-dsq-evening-download]')
    uploads = page.query_selector_all('[data-tcom-fixed-plancard-dsq-evening-upload]')
    
    for i, header in enumerate(headers):
        # Use the data attribute for clean plan name, fall back to inner text
        plan_name = header.get_attribute('data-tcom-fixed-plan-card-header-label') or ''
        if not plan_name:
            raw_name = header.inner_text().strip()
            plan_name = raw_name.split('\n')[0].replace('Online exclusive offer', '').strip()
        
        price = 0
        if i < len(prices):
            price = float(prices[i].get_attribute('data-fixed-plan-card-price') or '0')
        
        download_speed = 0
        if i < len(downloads):
            dl_val = downloads[i].get_attribute('data-tcom-fixed-plancard-dsq-evening-download') or '0'
            download_speed = extract_speed_from_text(dl_val)
        
        upload_speed = 0
        if i < len(uploads):
            ul_val = uploads[i].get_attribute('data-tcom-fixed-plancard-dsq-evening-upload') or '0'
            upload_speed = extract_speed_from_text(ul_val)
        
        # Network type from plan name
        network_type = '5G' if '5G' in plan_name else 'NBN'
        
        # Deduplicate by name+price
        key = f"{plan_name}_{price}"
        if key in seen:
            continue
        seen.add(key)
        
        if plan_name and price > 0:
            plans.append({
                'provider_id': config.PROVIDERS['telstra']['id'],
                'plan_name': plan_name,
                'network_type': network_type,
                'speed': download_speed,
                'download_speed': download_speed,
                'upload_speed': upload_speed,
                'price': price,
                'promo_price': None,
                'promo_period': None,
                'contract': 'No Contract',
                'source_url': TELSTRA_WEBSITE_URL
            })
    
    return plans


def extract_plan_from_card(page, card) -> Dict[str, Any]:
    """
    Extract plan data from a Telstra plan card container.
    Uses Telstra-specific class names and data attributes.
    
    Args:
        page: Playwright page object
        card: Playwright element handle for planCardCarouselContainer
    
    Returns:
        Standardized plan dictionary
    """
    try:
        # Plan name from header headline
        name_elem = card.query_selector('h3.tcom-fixed-plan-card-header__headline')
        plan_name = name_elem.inner_text().strip() if name_elem else ''
        
        # Price from data attribute
        price_elem = card.query_selector('[data-fixed-plan-card-price]')
        price = float(price_elem.get_attribute('data-fixed-plan-card-price') or '0') if price_elem else 0
        
        # Download speed from DSQ evening data attribute
        dl_elem = card.query_selector('[data-tcom-fixed-plancard-dsq-evening-download]')
        download_speed = int(dl_elem.get_attribute('data-tcom-fixed-plancard-dsq-evening-download') or '0') if dl_elem else 0
        
        # Upload speed from DSQ evening data attribute
        ul_elem = card.query_selector('[data-tcom-fixed-plancard-dsq-evening-upload]')
        upload_speed = int(ul_elem.get_attribute('data-tcom-fixed-plancard-dsq-evening-upload') or '0') if ul_elem else 0
        
        # Network type from plan name
        network_type = '5G' if '5G' in plan_name else 'NBN'
        
        return {
            'provider_id': config.PROVIDERS['telstra']['id'],
            'plan_name': plan_name,
            'network_type': network_type,
            'speed': download_speed,
            'download_speed': download_speed,
            'upload_speed': upload_speed,
            'price': price,
            'promo_price': None,
            'promo_period': None,
            'contract': 'No Contract',
            'source_url': TELSTRA_WEBSITE_URL
        }
        
    except Exception as e:
        log_error(f"Error extracting plan from card: {str(e)}", provider="telstra")
        return None


def deduplicate_plans(plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate plans by name+price combination."""
    seen = set()
    unique = []
    for plan in plans:
        key = f"{plan.get('plan_name')}_{plan.get('price')}"
        if key not in seen:
            seen.add(key)
            unique.append(plan)
    return unique


def extract_speed_from_text(text: str) -> int:
    """
    Extract speed value from text.
    
    Args:
        text: Text containing speed information
    
    Returns:
        Speed as integer
    """
    import re
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0


def extract_price_from_text(text: str) -> float:
    """
    Extract price value from text.
    
    Args:
        text: Text containing price information
    
    Returns:
        Price as float
    """
    import re
    # Remove currency symbols and extract number
    match = re.search(r'\$?([\d.]+)', text)
    return float(match.group(1)) if match else 0.0
