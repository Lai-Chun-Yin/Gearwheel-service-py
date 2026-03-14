"""
Example API Testing Guide for Python

This file contains example requests for testing the PEG Stock Valuation Microservice
You can use these with curl or the Python requests library
"""

import requests

BASE_URL = 'http://localhost:3000'


def check_health():
    """Health check"""
    response = requests.get(f'{BASE_URL}/health')
    data = response.json()
    print('Health:', data)
    return data


def get_api_docs():
    """Get API documentation"""
    response = requests.get(f'{BASE_URL}/api/docs')
    data = response.json()
    return data


def get_valuation(symbol, market='US', finnhub_key=None, alpha_vantage_key=None):
    """
    Get valuation for a single stock
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        market: Market ('US' or 'HK'), default 'US'
        finnhub_key: Finnhub API key (optional if set in .env)
        alpha_vantage_key: Alpha Vantage API key (optional if set in .env)
    """
    params = {
        'symbol': symbol,
        'market': market,
        'marketGrowthRatePercent': 10
    }
    
    if finnhub_key:
        params['finnhubApiKey'] = finnhub_key
    if alpha_vantage_key:
        params['alphaVantageApiKey'] = alpha_vantage_key
    
    response = requests.get(f'{BASE_URL}/api/valuation/peg', params=params)
    return response.json()


def get_earnings_track_valuation(symbol, market='US', finnhub_key=None, alpha_vantage_key=None):
    """
    Get earnings track valuation for a single stock
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        market: Market ('US' or 'HK'), default 'US'
        finnhub_key: Finnhub API key (optional if set in .env)
        alpha_vantage_key: Alpha Vantage API key (optional if set in .env)
    """
    params = {
        'symbol': symbol,
        'market': market
    }
    
    if finnhub_key:
        params['finnhubApiKey'] = finnhub_key
    if alpha_vantage_key:
        params['alphaVantageApiKey'] = alpha_vantage_key
    
    response = requests.get(f'{BASE_URL}/api/valuation/earning_track', params=params)
    return response.json()


def get_asset_based_valuation(symbol, market='US', finnhub_key=None, alpha_vantage_key=None):
    """
    Get asset-based valuation for a single stock
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        market: Market ('US' or 'HK'), default 'US'
        finnhub_key: Finnhub API key (optional if set in .env)
        alpha_vantage_key: Alpha Vantage API key (optional if set in .env)
    """
    params = {
        'symbol': symbol,
        'market': market
    }
    
    if finnhub_key:
        params['finnhubApiKey'] = finnhub_key
    if alpha_vantage_key:
        params['alphaVantageApiKey'] = alpha_vantage_key
    
    response = requests.get(f'{BASE_URL}/api/valuation/asset', params=params)
    return response.json()


def get_dividend_valuation(symbol, market='US', finnhub_key=None, alpha_vantage_key=None):
    """
    Get dividend valuation for a single stock
    
    Args:
        symbol: Stock symbol (e.g., 'JNJ')
        market: Market ('US' or 'HK'), default 'US'
        finnhub_key: Finnhub API key (optional if set in .env)
        alpha_vantage_key: Alpha Vantage API key (REQUIRED for dividend valuation)
    """
    params = {
        'symbol': symbol,
        'market': market
    }
    
    if finnhub_key:
        params['finnhubApiKey'] = finnhub_key
    if alpha_vantage_key:
        params['alphaVantageApiKey'] = alpha_vantage_key
    
    response = requests.get(f'{BASE_URL}/api/valuation/dividend', params=params)
    return response.json()


def batch_valuation(symbols, markets=None, finnhub_key=None, alpha_vantage_key=None):
    """
    Get batch valuation for multiple stocks
    
    Args:
        symbols: List of stock symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])
        markets: List of markets corresponding to symbols (e.g., ['US', 'US', 'US'])
        finnhub_key: Finnhub API key (optional if set in .env)
        alpha_vantage_key: Alpha Vantage API key (optional if set in .env)
    """
    params = {
        'symbols': ','.join(symbols),
        'marketGrowthRatePercent': 10
    }
    
    if markets:
        params['markets'] = ','.join(markets)
    
    if finnhub_key:
        params['finnhubApiKey'] = finnhub_key
    if alpha_vantage_key:
        params['alphaVantageApiKey'] = alpha_vantage_key
    
    response = requests.get(f'{BASE_URL}/api/valuation/peg/batch', params=params)
    return response.json()


# Example usage
if __name__ == '__main__':
    print("=== PEG Stock Valuation Microservice - Python Test Examples ===\n")
    
    # Test 1: Health Check
    print("1. Health Check:")
    try:
        health = check_health()
        print(f"   Status: {health['status']}")
        print(f"   Uptime: {health['uptime']:.2f} seconds\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Test 2: Get API documentation
    print("2. API Documentation:")
    try:
        docs = get_api_docs()
        print(f"   Service: {docs['service']}")
        print(f"   Version: {docs['version']}")
        print(f"   Available endpoints: {len(docs['endpoints'])}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Test 3: Get valuation for Apple
    print("3. Get valuation for Apple (AAPL):")
    print("   Note: Set FINNHUB_API_KEY in .env or pass finnhub_key parameter\n")
    
    # Test 4: Batch valuation for multiple stocks
    print("4. Batch valuation example:")
    print("   batch_valuation(['AAPL', 'MSFT', 'GOOGL'])\n")
    
    # Test 5: Dividend valuation
    print("5. Dividend valuation example:")
    print("   get_dividend_valuation('JNJ')")
    print("   Note: Requires both FINNHUB_API_KEY and ALPHA_VANTAGE_API_KEY\n")
    
    print("=== End of Examples ===")
