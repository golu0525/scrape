"""Show scraper output for all working providers."""
import sys
sys.path.insert(0, 'c:/xampp/htdocs/staging/scrape')


def print_plans(provider_name, plans):
    print(f"\n{'='*90}")
    print(f"  {provider_name} — {len(plans)} plans scraped")
    print(f"{'='*90}")
    print(f"  {'Plan Name':<40} {'Speed':>12} {'Typical Eve':>12} {'Price':>10}")
    print(f"  {'-'*40} {'-'*12} {'-'*12} {'-'*10}")
    for p in plans:
        name = p['plan_name'][:40]
        speed = f"{p['download_speed']}/{p['upload_speed']} Mbps"
        typical_dl = p.get('typical_evening_dl', 0)
        typical_ul = p.get('typical_evening_ul', 0)
        typical = f"{typical_dl}/{typical_ul} Mbps" if typical_dl else "-"
        price = f"${p['price']:.0f}/mth"
        print(f"  {name:<40} {speed:>12} {typical:>12} {price:>10}")

    print(f"\n  Total plans: {len(plans)}")
    if plans:
        prices = [p['price'] for p in plans]
        print(f"  Price range: ${min(prices):.0f} - ${max(prices):.0f}/mth")
        speeds = [p['download_speed'] for p in plans]
        print(f"  Speed range: {min(speeds)} - {max(speeds)} Mbps")


# Telstra
from providers.telstra import scrape_telstra_plans
telstra_plans = scrape_telstra_plans()
print_plans("TELSTRA", telstra_plans)

# Superloop
from providers.superloop import scrape_superloop_plans
superloop_plans = scrape_superloop_plans()
print_plans("SUPERLOOP", superloop_plans)

# Occom
from providers.occom import scrape_occom_plans
occom_plans = scrape_occom_plans()
print_plans("OCCOM", occom_plans)
