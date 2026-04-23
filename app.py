"""
Flask API backend for ISP scraper frontend dashboard.
Provides REST endpoints for scraping, viewing results, and downloading files.
"""
from flask import Flask, jsonify, request, send_file, render_template
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_service import (
    scrape_provider,
    save_output,
    get_saved_results,
    get_provider_list,
    download_json,
    download_csv
)

app = Flask(__name__, template_folder='templates')

# API Routes


@app.route('/')
def index():
    """Serve the frontend dashboard."""
    return render_template('index.html')


@app.route('/api/providers', methods=['GET'])
def api_get_providers():
    """Get list of all providers with their status."""
    providers = get_provider_list()
    return jsonify({
        'success': True,
        'providers': providers,
        'total': len(providers)
    })


@app.route('/api/scrape/<provider_name>', methods=['POST'])
def api_scrape_provider(provider_name):
    """
    Scrape a specific provider.
    Returns scraped plans and saves to JSON/CSV.
    """
    result = scrape_provider(provider_name)
    
    if result['success']:
        # Save output
        files = save_output(provider_name, result['plans'])
        result['files'] = files
    
    return jsonify(result)


@app.route('/api/scrape/all', methods=['POST'])
def api_scrape_all():
    """Scrape all enabled providers."""
    results = {}
    total_plans = 0
    
    for provider in get_provider_list():
        if provider['enabled']:
            result = scrape_provider(provider['key'])
            if result['success']:
                files = save_output(provider['key'], result['plans'])
                result['files'] = files
            results[provider['key']] = result
            total_plans += result.get('total_plans', 0)
    
    return jsonify({
        'success': True,
        'results': results,
        'total_plans': total_plans,
        'providers_scraped': len(results)
    })


@app.route('/api/results', methods=['GET'])
def api_get_all_results():
    """Get all saved results from all providers."""
    results = get_saved_results()
    total_plans = sum(
        len(data.get('all_plans', []) if isinstance(data, dict) else data)
        for provider_data in results.values()
        for data in provider_data.values()
    )
    
    return jsonify({
        'success': True,
        'results': results,
        'total_plans': total_plans,
        'providers': list(results.keys())
    })


@app.route('/api/results/<provider_name>', methods=['GET'])
def api_get_provider_results(provider_name):
    """Get saved results for a specific provider."""
    results = get_saved_results(provider_name)
    
    if not results:
        return jsonify({
            'success': False,
            'error': f'No saved results found for {provider_name}'
        }), 404
    
    total_plans = sum(
        len(data) for data in results.values() if isinstance(data, list)
    )
    
    return jsonify({
        'success': True,
        'results': results,
        'total_plans': total_plans,
        'provider': provider_name
    })


@app.route('/api/download/<provider_name>/<filename>.json', methods=['GET'])
def api_download_json(provider_name, filename):
    """Download JSON file."""
    filepath = download_json(provider_name, filename)
    if filepath:
        return send_file(filepath, as_attachment=True, download_name=f"{filename}.json")
    return jsonify({'success': False, 'error': 'File not found'}), 404


@app.route('/api/download/<provider_name>/<filename>.csv', methods=['GET'])
def api_download_csv(provider_name, filename):
    """Download CSV file."""
    filepath = download_csv(provider_name, filename)
    if filepath:
        return send_file(filepath, as_attachment=True, download_name=f"{filename}.csv")
    return jsonify({'success': False, 'error': 'File not found'}), 404


@app.route('/api/status', methods=['GET'])
def api_status():
    """Get system status."""
    providers = get_provider_list()
    working = [p for p in providers if p['has_saved_data']]
    
    return jsonify({
        'success': True,
        'status': 'operational',
        'total_providers': len(providers),
        'working_providers': len(working),
        'blocked_providers': len(providers) - len(working)
    })


if __name__ == '__main__':
    print("Starting ISP Scraper API Server...")
    print("Access dashboard at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
