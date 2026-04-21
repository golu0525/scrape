"""
Superloop ISP plan scraper.
Uses API-first approach, falls back to Playwright if needed.
Extracts plan data from embedded JSON-LD structured data on the nbn plans page.
"""

import re
import json
import requests
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
import config
from utils.logger import log_info, log_error, log_success
from utils.stealth import create_stealth_browser, create_stealth_page


# Superloop API endpoint (example - update with actual API if available)
SUPERLOOP_API_URL = "https://www.superloop.com/api/plans"
SUPERLOOP_WEBSITE_URL = "https://www.superloop.com/internet/nbn/"


def scrape_superloop_plans() -> List[Dict[str, Any]]:
    """
    Scrape Superloop ISP plans.
    First attempts API, falls back to Playwright scraping.
    
    Returns:
        List of plan dictionaries
    """
    log_info("Starting Superloop scraper", provider="superloop")
    
    # Try API first
    try:
        plans = scrape_via_api()
        if plans:
            log_success(f"Successfully scraped {len(plans)} plans via API", provider="superloop")
            return plans
    except Exception as e:
        log_info("API scraping failed, falling back to Playwright", provider="superloop", 
                data={'error': str(e)})
    
    # Fallback to Playwright
    try:
        plans = scrape_via_playwright()
        if plans:
            log_success(f"Successfully scraped {len(plans)} plans via Playwright", provider="superloop")
            return plans
    except Exception as e:
        log_error(f"Playwright scraping failed: {str(e)}", provider="superloop")
    
    log_error("All scraping methods failed for Superloop", provider="superloop")
    return []


def scrape_via_api() -> List[Dict[str, Any]]:
    """
    Scrape Superloop plans using their API.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    try:
        response = requests.get(SUPERLOOP_API_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse API response (adjust based on actual API structure)
        if isinstance(data, dict) and 'plans' in data:
            for plan_data in data['plans']:
                plan = parse_superloop_api_plan(plan_data)
                if plan:
                    plans.append(plan)
        
    except requests.exceptions.RequestException as e:
        log_error(f"API request failed: {str(e)}", provider="superloop")
    except Exception as e:
        log_error(f"API parsing failed: {str(e)}", provider="superloop")
    
    return plans


def parse_superloop_api_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Superloop API plan response into standardized format.
    
    Args:
        plan_data: Raw plan data from API
    
    Returns:
        Standardized plan dictionary
    """
    try:
        return {
            'provider_id': config.PROVIDERS['superloop']['id'],
            'plan_name': plan_data.get('planName', ''),
            'network_type': plan_data.get('networkType', 'NBN'),
            'speed': int(plan_data.get('speed', 0)),
            'download_speed': int(plan_data.get('downloadSpeed', plan_data.get('speed', 0))),
            'upload_speed': int(plan_data.get('uploadSpeed', 0)),
            'price': float(plan_data.get('monthlyPrice', 0)),
            'promo_price': float(plan_data.get('promoPrice', 0)) if plan_data.get('promoPrice') else None,
            'promo_period': plan_data.get('promoPeriod', ''),
            'contract': plan_data.get('contractTerm', 'No Contract'),
            'source_url': SUPERLOOP_WEBSITE_URL
        }
    except Exception as e:
        log_error(f"Failed to parse Superloop API plan: {str(e)}", provider="superloop")
        return None


def scrape_via_playwright() -> List[Dict[str, Any]]:
    """
    Scrape Superloop plans using Playwright with stealth mode.
    Extracts plan data from embedded JSON-LD structured data and visible card elements.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    with sync_playwright() as p:
        browser = create_stealth_browser(p)
        page = create_stealth_page(browser)
        
        try:
            page.goto(SUPERLOOP_WEBSITE_URL, timeout=config.PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # Primary: extract from JSON-LD structured data
            plans = extract_from_json_ld(page)
            
            if not plans:
                # Fallback: extract from visible plan cards
                plans = extract_from_plan_cards(page)
            
        except Exception as e:
            log_error(f"Playwright scraping error: {str(e)}", provider="superloop")
        finally:
            browser.close()
    
    return plans


def extract_from_json_ld(page) -> List[Dict[str, Any]]:
    """
    Extract plan data from JSON-LD structured data embedded in the page.
    Superloop embeds schema.org Product data with plan variants.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    try:
        scripts = page.query_selector_all('script[type="application/ld+json"]')
        
        for script in scripts:
            text = script.inner_text()
            data = json.loads(text)
            
            # Handle single object or array
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if item.get('@type') != 'ProductGroup':
                    continue
                    
                variants = item.get('hasVariant', [])
                for variant in variants:
                    plan = parse_json_ld_variant(variant)
                    if plan:
                        plans.append(plan)
        
        if plans:
            log_info(f"Extracted {len(plans)} plans from JSON-LD", provider="superloop")
            
    except Exception as e:
        log_error(f"JSON-LD extraction failed: {str(e)}", provider="superloop")
    
    return plans


def parse_json_ld_variant(variant: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a JSON-LD Product variant into standardized plan format.
    
    Example variant:
    {"name": "Extra Value - nbn 50/20", "description": "Typical evening speed is 50/17Mbps.",
     "size": "50/20", "offers": {"price": 65}}
    """
    try:
        name = variant.get('name', '')
        size = variant.get('size', '')
        description = variant.get('description', '')
        offers = variant.get('offers', {})
        price = float(offers.get('price', 0))
        
        # Parse download/upload from size field (e.g. "50/20")
        download_speed = 0
        upload_speed = 0
        if size:
            parts = size.split('/')
            if len(parts) == 2:
                download_speed = int(parts[0])
                upload_speed = int(parts[1])
        
        # Parse typical evening speed from description
        typical_dl = 0
        typical_ul = 0
        typical_match = re.search(r'Typical evening speed is (\d+)/(\d+)', description)
        if typical_match:
            typical_dl = int(typical_match.group(1))
            typical_ul = int(typical_match.group(2))
        
        # Connection types from material field
        materials = variant.get('material', [])
        connection_types = ', '.join(materials) if materials else 'NBN'
        
        if not name or price <= 0:
            return None
        
        return {
            'provider_id': config.PROVIDERS['superloop']['id'],
            'plan_name': name,
            'network_type': 'NBN',
            'speed': download_speed,
            'download_speed': download_speed,
            'upload_speed': upload_speed,
            'typical_evening_dl': typical_dl,
            'typical_evening_ul': typical_ul,
            'price': price,
            'promo_price': None,
            'promo_period': None,
            'contract': 'No Contract',
            'connection_types': connection_types,
            'source_url': SUPERLOOP_WEBSITE_URL
        }
        
    except Exception as e:
        log_error(f"Failed to parse JSON-LD variant: {str(e)}", provider="superloop")
        return None


def extract_from_plan_cards(page) -> List[Dict[str, Any]]:
    """
    Fallback: extract plan data from visible plan card elements.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    try:
        # Plan cards are inside the #plans section
        cards = page.query_selector_all('#plans .border.rounded-\\[1\\.25rem\\]')
        
        for card in cards:
            # Plan name
            name_elem = card.query_selector('h3.text-body-1.font-Avenir95Black.font-bold')
            plan_name = name_elem.inner_text().strip() if name_elem else ''
            
            # Download speed - first p with font-Avenir95Black after "Download"
            dl_elem = card.query_selector('div:has(> div:has-text("Download")) p.font-Avenir95Black')
            dl_text = dl_elem.inner_text().strip() if dl_elem else '0'
            download_speed = extract_speed_from_text(dl_text)
            
            # Upload speed
            ul_elem = card.query_selector('div:has(> div:has-text("Upload")) p.font-Avenir95Black')
            ul_text = ul_elem.inner_text().strip() if ul_elem else '0'
            upload_speed = extract_speed_from_text(ul_text)
            
            # Price - green promo price or regular
            promo_elem = card.query_selector('span.text-green-500')
            regular_elem = card.query_selector('span.line-through')
            
            price = 0
            promo_price = None
            if promo_elem:
                promo_price = extract_price_from_text(promo_elem.inner_text())
                if regular_elem:
                    price = extract_price_from_text(regular_elem.inner_text())
                else:
                    price = promo_price
            
            if plan_name and (price > 0 or (promo_price and promo_price > 0)):
                plans.append({
                    'provider_id': config.PROVIDERS['superloop']['id'],
                    'plan_name': plan_name,
                    'network_type': 'NBN',
                    'speed': download_speed,
                    'download_speed': download_speed,
                    'upload_speed': upload_speed,
                    'price': price if price > 0 else promo_price,
                    'promo_price': promo_price,
                    'promo_period': '6 months',
                    'contract': 'No Contract',
                    'source_url': SUPERLOOP_WEBSITE_URL
                })
                
    except Exception as e:
        log_error(f"Card extraction failed: {str(e)}", provider="superloop")
    
    return plans


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
