"""
Occom ISP plan scraper.
Scrapes nbn plans from the Occom staging website using Playwright.
Plan data is extracted from .plan-card elements in an owl-carousel.
"""

import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
import config
from utils.logger import log_info, log_error, log_success
from utils.stealth import create_stealth_browser, create_stealth_page


OCCOM_WEBSITE_URL = "https://staging.occominternet.com/nbn-plans/"


def scrape_occom_plans() -> List[Dict[str, Any]]:
    """
    Scrape Occom nbn plans using Playwright.
    
    Returns:
        List of plan dictionaries
    """
    log_info("Starting Occom scraper", provider="occom")
    
    try:
        plans = scrape_via_playwright()
        if plans:
            log_success(f"Successfully scraped {len(plans)} plans", provider="occom")
            return plans
    except Exception as e:
        log_error(f"Scraping failed: {str(e)}", provider="occom")
    
    log_error("All scraping methods failed for Occom", provider="occom")
    return []


def scrape_via_playwright() -> List[Dict[str, Any]]:
    """
    Scrape Occom plans from .plan-card elements inside the owl-carousel.
    
    Returns:
        List of plan dictionaries
    """
    plans = []
    
    with sync_playwright() as p:
        browser = create_stealth_browser(p)
        page = create_stealth_page(browser)
        
        try:
            page.goto(OCCOM_WEBSITE_URL, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # Wait for plan cards to load
            page.wait_for_selector('.plan-card.newPlanDesign', timeout=15000, state='attached')
            
            # Get all plan cards
            cards = page.query_selector_all('.plan-card.newPlanDesign')
            log_info(f"Found {len(cards)} plan cards", provider="occom")
            
            seen = set()
            for card in cards:
                plan = extract_plan_from_card(card)
                if plan:
                    # Deduplicate by name+price
                    key = f"{plan['plan_name']}_{plan['price']}"
                    if key not in seen:
                        seen.add(key)
                        plans.append(plan)
            
        except Exception as e:
            log_error(f"Playwright scraping error: {str(e)}", provider="occom")
        finally:
            browser.close()
    
    return plans


def extract_plan_from_card(card) -> Dict[str, Any]:
    """
    Extract plan data from an Occom .plan-card element.
    
    Structure:
        .plans-name         -> plan name (e.g. "Hyper")
        .plan-speed         -> nbn tier (e.g. "(nbn2000)")
        .amount-price       -> download/upload speeds (two elements)
        .prices-regulars    -> promo price
        strike              -> original price
        .speeds             -> promo details text
    """
    try:
        # Plan name
        name_elem = card.query_selector('.plans-name')
        plan_name = name_elem.inner_text().strip() if name_elem else ''
        
        # NBN tier (e.g. "(nbn2000)")
        tier_elem = card.query_selector('.plan-speed')
        tier_text = tier_elem.inner_text().strip() if tier_elem else ''
        
        # Download and upload speeds from .amount-price elements
        speed_elems = card.query_selector_all('.amount-price')
        download_speed = 0
        upload_speed = 0
        if len(speed_elems) >= 1:
            download_speed = extract_speed(speed_elems[0].inner_text())
        if len(speed_elems) >= 2:
            upload_speed = extract_speed(speed_elems[1].inner_text())
        
        # Promo price from .prices-regulars
        promo_elem = card.query_selector('.prices-regulars')
        promo_price = 0
        if promo_elem:
            promo_price = extract_price(promo_elem.inner_text())
        
        # Original price from strike element
        strike_elem = card.query_selector('.price strike')
        original_price = 0
        if strike_elem:
            original_price = extract_price(strike_elem.inner_text())
        
        # Promo details text
        promo_details_elem = card.query_selector('.speeds')
        promo_period = ''
        if promo_details_elem:
            promo_text = promo_details_elem.inner_text().strip()
            period_match = re.search(r'For (\d+) months', promo_text)
            if period_match:
                promo_period = f"{period_match.group(1)} months"
        
        # Use original price as the standard price, promo as discount
        price = original_price if original_price > 0 else promo_price
        
        # Combine name with tier
        full_name = f"{plan_name} {tier_text}".strip()
        
        if not plan_name or price <= 0:
            return None
        
        return {
            'provider_id': config.PROVIDERS.get('occom', {}).get('id', 5),
            'plan_name': full_name,
            'network_type': 'NBN',
            'speed': download_speed,
            'download_speed': download_speed,
            'upload_speed': upload_speed,
            'price': price,
            'promo_price': promo_price if promo_price != price else None,
            'promo_period': promo_period,
            'contract': 'No Contract',
            'source_url': OCCOM_WEBSITE_URL
        }
        
    except Exception as e:
        log_error(f"Error extracting plan from card: {str(e)}", provider="occom")
        return None


def extract_speed(text: str) -> int:
    """Extract numeric speed value from text like '2000 Mbps'."""
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0


def extract_price(text: str) -> float:
    """Extract price value from text like '$165/mth'."""
    match = re.search(r'\$?([\d.]+)', text)
    return float(match.group(1)) if match else 0.0
