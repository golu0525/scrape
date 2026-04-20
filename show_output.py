"""Show scraper output for all working providers."""
import sys
sys.path.insert(0, 'c:/xampp/htdocs/staging/scrape')
from providers.telstra import scrape_telstra_plans

plans = scrape_telstra_plans()
print(f"\n{'='*80}")
print(f"  TELSTRA — {len(plans)} plans scraped")
print(f"{'='*80}")
print(f"  {'Plan Name':<40} {'Speed':>12} {'Price':>10} {'Type':<5}")
print(f"  {'-'*40} {'-'*12} {'-'*10} {'-'*5}")
for p in plans:
    name = p['plan_name']
    speed = f"{p['download_speed']}/{p['upload_speed']} Mbps"
    price = f"${p['price']:.0f}/mth"
    ntype = p['network_type']
    print(f"  {name:<40} {speed:>12} {price:>10} {ntype:<5}")

print(f"\n{'='*80}")
print(f"  SUMMARY")
print(f"{'='*80}")
print(f"  Total plans: {len(plans)}")
prices = [p['price'] for p in plans]
print(f"  Price range: ${min(prices):.0f} - ${max(prices):.0f}/mth")
speeds = [p['download_speed'] for p in plans]
print(f"  Speed range: {min(speeds)} - {max(speeds)} Mbps")
