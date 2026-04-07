"""
Stock Fair Value Calculator Module
Calculates fair value using PEG-based valuation model
Supports US (S&P 500) and HK (Hang Seng) markets
"""

import requests
from datetime import datetime, timedelta
import math
import yfinance as yf


def fetch_finnhub(url):
    """Helper function to fetch JSON from Finnhub API"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as error:
        raise Exception(f'Finnhub API call failed: {str(error)}')


def fetch_alpha_vantage(url):
    """Helper function to fetch JSON from Alpha Vantage API"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'Note' in data:
            raise Exception(f'API rate limit exceeded: {data["Note"]}')
        
        if 'Error' in data and data['Error'] != 'None':
            raise Exception(data['Error'])
        
        return data
    except Exception as error:
        raise Exception(f'Alpha Vantage API call failed: {str(error)}')


def fetch_price_from_yfinance(symbol):
    """Helper function to fetch previous close price from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get previous close price
        previous_close = info.get('previousClose')
        
        if previous_close is None:
            raise Exception(f'Previous close price not available for {symbol}')
        
        price = float(previous_close)
        if not isinstance(price, (int, float)) or price <= 0:
            raise Exception(f'Invalid price for {symbol}: {previous_close}')
        
        return price
    except Exception as error:
        raise Exception(f'Failed to get price from yfinance for {symbol}: {str(error)}')


def get_market_pe(market, api_key):
    """Get market PE ratio via ETF (SPY for US, 2800.HK for HK)"""
    etf_symbol = '2800' if market == 'HK' else 'SPY'
    url = f'https://finnhub.io/api/v1/stock/metric?symbol={etf_symbol}&metric=all&token={api_key}'
    
    try:
        data = fetch_finnhub(url)
        
        pe = None
        if 'metric' in data:
            # Try peNormalizedAnnual first, then peAnnual
            if 'peNormalizedAnnual' in data['metric'] and data['metric']['peNormalizedAnnual'] is not None:
                pe = float(data['metric']['peNormalizedAnnual'])
            elif 'peAnnual' in data['metric'] and data['metric']['peAnnual'] is not None:
                pe = float(data['metric']['peAnnual'])
        
        if not isinstance(pe, (int, float)) or pe <= 0:
            raise Exception(f'Invalid PE ratio for {etf_symbol}: {pe}')
        
        return pe
    except Exception as error:
        raise Exception(f'Failed to get market PE for {market}: {str(error)}')


def get_stock_data(symbol, finnhub_api_key):
    """Get stock data including beta, EPS, and price"""
    warnings = []
    beta = None
    actual_eps = None
    estimated_eps = None
    price = None
    pe = None
    
    # Fetch current price via yfinance
    try:
        price = fetch_price_from_yfinance(symbol)
    except Exception as error:
        raise Exception(f'Failed to get quote for {symbol}: {str(error)}')
    
    # Fetch metrics (beta, PE, and other fundamentals)
    try:
        metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={finnhub_api_key}'
        metrics_data = fetch_finnhub(metrics_url)
        
        if 'metric' in metrics_data:
            metrics = metrics_data['metric']
            
            # Extract PE ratio
            if 'peTTM' in metrics and metrics['peTTM'] is not None:
                pe = float(metrics['peTTM'])
            elif 'peExclExtraTTM' in metrics and metrics['peExclExtraTTM'] is not None:
                pe = float(metrics['peExclExtraTTM'])
            elif 'peAnnual' in metrics and metrics['peAnnual'] is not None:
                pe = float(metrics['peAnnual'])
            
            # Extract EPS TTM
            if 'epsTTM' in metrics and metrics['epsTTM'] is not None:
                actual_eps = float(metrics['epsTTM'])
            elif 'epsExclExtraItemsTTM' in metrics and metrics['epsExclExtraItemsTTM'] is not None:
                actual_eps = float(metrics['epsExclExtraItemsTTM'])
            elif 'epsAnnual' in metrics and metrics['epsAnnual'] is not None:
                actual_eps = float(metrics['epsAnnual'])
            
            if isinstance(pe, (int, float)) and pe <= 0:
                pe = None
            
            if not isinstance(actual_eps, (int, float)):
                actual_eps = None
            
            # Extract Beta
            if 'beta' in metrics and metrics['beta']:
                beta = float(metrics['beta'])
                if not isinstance(beta, (int, float)) or beta < 0:
                    beta = None
                    warnings.append('Beta value was invalid; using fallback.')
    except Exception as error:
        warnings.append(f'Could not fetch metrics; some data may be unavailable: {str(error)}')
    
    # If we don't have EPS from metrics, try financials endpoint
    if not isinstance(actual_eps, (int, float)):
        try:
            financials_url = f'https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&freq=annual&token={finnhub_api_key}'
            financials_data = fetch_finnhub(financials_url)
            
            if 'data' in financials_data and len(financials_data['data']) > 0:
                latest_filing = financials_data['data'][0]
                if 'report' in latest_filing:
                    # Calculate EPS from net income if available
                    if 'ic' in latest_filing['report'] and 'NetIncomeLoss' in latest_filing['report']['ic']:
                        net_income = float(latest_filing['report']['ic']['NetIncomeLoss'])
                        if isinstance(net_income, (int, float)) and net_income != 0:
                            actual_eps = net_income
                            warnings.append('Actual EPS derived from reported net income (not per share basis).')
        except Exception as error:
            warnings.append(f'Could not fetch financials: {str(error)}')
    
    estimated_eps = None
    
    # Use default beta if not available
    if beta is None:
        beta = 1.0
        warnings.append('Beta value unavailable; using default beta = 1.0')
    
    return {
        'beta': beta,
        'actualEps': actual_eps,
        'estimatedEps': estimated_eps,
        'price': price,
        'pe': pe,
        'warnings': warnings
    }


def calculate_peg(pe, growth_rate_decimal):
    """Calculate PEG ratio"""
    if growth_rate_decimal <= 0 or not isinstance(pe, (int, float)) or pe <= 0:
        return None
    return pe / (growth_rate_decimal * 100)


def get_estimated_eps_from_alpha_vantage(symbol, api_key):
    """Get estimated EPS from Alpha Vantage"""
    try:
        url = f'https://www.alphavantage.co/query?function=EARNINGS_ESTIMATES&symbol={symbol}&apikey={api_key}'
        data = fetch_alpha_vantage(url)
        
        if 'estimates' in data and len(data['estimates']) > 0:
            # Get the most recent annual estimate if available
            for estimate in data['estimates']:
                if 'date' in estimate and 'eps_estimate_average' in estimate:
                    estimated_eps = float(estimate['eps_estimate_average'])
                    if isinstance(estimated_eps, (int, float)) and estimated_eps > 0:
                        return {'eps': estimated_eps, 'period': estimate['date']}
        
        return None
    except Exception as error:
        return None


def calculate_stock_valuation(params):
    """
    Calculate fair value for a stock using PEG method
    
    Args:
        params: Dictionary with keys:
            - symbol: Stock symbol
            - finnhubApiKey: Finnhub API key
            - alphaVantageApiKey: Alpha Vantage API key (optional)
            - market: Market ('US' or 'HK', default 'US')
            - marketGrowthRatePercent: Market growth rate (default 10)
    
    Returns:
        Dictionary with valuation result
    """
    symbol = params['symbol']
    finnhub_api_key = params['finnhubApiKey']
    alpha_vantage_api_key = params.get('alphaVantageApiKey')
    market = params.get('market', 'US')
    market_growth_rate_percent = params.get('marketGrowthRatePercent', 10)
    
    result = {
        'symbol': symbol,
        'market': market,
        'marketPe': None,
        'marketPeg': None,
        'beta': None,
        'actualEps': None,
        'estimatedEps': None,
        'stockPe': None,
        'growthRate': None,
        'stockPeg': None,
        'currentPrice': None,
        'fairValue': None,
        'assumptions': {
            'marketGrowthRatePercent': market_growth_rate_percent,
            'notes': [
                f'Market PE obtained from {("2800" if market == "HK" else "SPY")} ETF via Finnhub',
                'Growth rate calculated as estimatedEps / actualEps - 1',
                'PEG formulas follow standard definition (PE divided by earnings growth in percent)',
                'Fair value = price * (market PEG * beta / stock PEG)',
                'Stock metrics from Finnhub API (https://finnhub.io/docs/api/)',
                'Estimated EPS from Alpha Vantage (https://www.alphavantage.co/documentation/#earnings-estimates)'
            ]
        },
        'warnings': [],
        'hasForwardEps': False,
        'betaFallbackUsed': False,
        'valuationPossible': False
    }
    
    try:
        # Step 1: Get market PE
        result['marketPe'] = 29
        result['marketPeg'] = result['marketPe'] / 13.5
        
        # Step 2: Get stock data from Finnhub
        stock_data = get_stock_data(symbol, finnhub_api_key)
        result['beta'] = stock_data['beta']
        result['actualEps'] = stock_data['actualEps']
        result['estimatedEps'] = stock_data['estimatedEps']
        result['currentPrice'] = stock_data['price']
        result['warnings'].extend(stock_data['warnings'])
        
        # Step 2b: Get estimated EPS from Alpha Vantage if not found
        if not isinstance(result['estimatedEps'], (int, float)) and alpha_vantage_api_key:
            alpha_estimate = get_estimated_eps_from_alpha_vantage(symbol, alpha_vantage_api_key)
            if alpha_estimate:
                result['estimatedEps'] = alpha_estimate['eps']
                result['warnings'].append(f'Estimated EPS from Alpha Vantage for period {alpha_estimate["period"]}')
        
        if stock_data['beta'] != 1.0 or any('default' in w for w in stock_data['warnings']):
            if any('default beta' in w for w in stock_data['warnings']):
                result['betaFallbackUsed'] = True
        
        # Validate EPS data
        if not isinstance(result['actualEps'], (int, float)) or not isinstance(result['estimatedEps'], (int, float)):
            result['warnings'].append('Missing or invalid EPS data; valuation cannot be completed. Finnhub free API may not provide detailed EPS estimates.')
            result['valuationPossible'] = False
            return result
        
        result['hasForwardEps'] = True
        
        # Step 3: Calculate stock growth rate
        result['growthRate'] = (result['estimatedEps'] / result['actualEps']) - 1
        
        # Step 4: Determine stock PE
        if stock_data['pe'] is not None:
            result['stockPe'] = stock_data['pe']
        elif result['currentPrice'] and result['actualEps']:
            result['stockPe'] = result['currentPrice'] / result['actualEps']
            result['warnings'].append('PE calculated from price / actualEps (not from API).')
        else:
            result['warnings'].append('Cannot calculate PE; price or EPS missing.')
            result['valuationPossible'] = False
            return result
        
        # Step 5: Calculate stock PEG
        if result['growthRate'] <= 0 or result['stockPe'] <= 0:
            result['warnings'].append('Growth rate or PE is non-positive; PEG-based valuation not meaningful.')
            result['valuationPossible'] = False
            return result
        
        result['stockPeg'] = calculate_peg(result['stockPe'], result['growthRate'])
        
        if result['stockPeg'] is None or result['stockPeg'] <= 0:
            result['warnings'].append('PEG calculation resulted in non-positive value; valuation not possible.')
            result['valuationPossible'] = False
            return result
        
        # Step 6: Calculate fair value
        result['fairValue'] = result['currentPrice'] * ((result['marketPeg'] + (result['beta'] - 1) * 0.7 * result['marketPeg']) / result['stockPeg'])
        result['valuationPossible'] = True
        
    except Exception as error:
        result['warnings'].append(f'Error during calculation: {str(error)}')
        result['valuationPossible'] = False
    
    return result


def calculate_earnings_track_valuation(params):
    """
    Calculate stock valuation using Earnings Track method
    Analyzes 5-year EPS trends and historical PE ratios
    """
    symbol = params['symbol']
    finnhub_api_key = params['finnhubApiKey']
    alpha_vantage_api_key = params.get('alphaVantageApiKey')
    market = params.get('market', 'US')
    market_growth_rate_percent = params.get('marketGrowthRatePercent', 10)
    
    result = {
        'symbol': symbol,
        'market': market,
        'fairValue': None,
        'currentPrice': None,
        'estimatedEpsT1': None,
        'referenceAveragePe': None,
        'epsGrowthRate': None,
        'expectedPriceTp1': None,
        'requiredRateOfReturn': 0.10,
        'valuationPossible': False,
        'warnings': [],
        'assumptions': {
            'method': 'Earnings Track',
            'requiredRateOfReturn': '10%',
            'notes': [
                'Analysis based on 5-year EPS track record',
                'EPS must be positive and non-decreasing across all years',
                'Fair value calculated using forward earnings and historical PE average'
            ]
        },
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Get current price from yfinance
        try:
            result['currentPrice'] = fetch_price_from_yfinance(symbol)
        except Exception as error:
            result['warnings'].append(f'Failed to get current price from yfinance: {str(error)}')
            return result
        
        if not isinstance(result['currentPrice'], (int, float)) or result['currentPrice'] <= 0:
            result['warnings'].append(f'Invalid current price: {result["currentPrice"]}')
            return result
        
        # Get historical financial data
        metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={finnhub_api_key}'
        metrics_data = fetch_finnhub(metrics_url)
        
        if 'series' not in metrics_data or 'annual' not in metrics_data['series']:
            result['warnings'].append('No historical series data available from Finnhub')
            return result
        
        # Extract EPS series
        eps_series = []
        pe_series = []
        
        if 'annual' in metrics_data['series'] and 'eps' in metrics_data['series']['annual']:
            eps_array = metrics_data['series']['annual']['eps']
            if isinstance(eps_array, list):
                for i in range(min(5, len(eps_array))):
                    if eps_array[i] and 'v' in eps_array[i] and eps_array[i]['v'] is not None:
                        eps_series.append(float(eps_array[i]['v']))
        
        if 'annual' in metrics_data['series'] and 'pe' in metrics_data['series']['annual']:
            pe_array = metrics_data['series']['annual']['pe']
            if isinstance(pe_array, list):
                for i in range(min(5, len(pe_array))):
                    if pe_array[i] and 'v' in pe_array[i] and pe_array[i]['v'] is not None:
                        pe_series.append(float(pe_array[i]['v']))
        
        # Validate data
        if len(eps_series) < 5:
            result['warnings'].append(f'Insufficient historical EPS data available (only {len(eps_series)} years instead of 5)')
            return result
        
        if len(pe_series) < 5:
            result['warnings'].append(f'Insufficient historical PE data available (only {len(pe_series)} years instead of 5)')
            return result
        
        # Reverse to have oldest first
        eps_series = eps_series[::-1]
        pe_series = pe_series[::-1]
        
        # STEP 1: Validate EPS track record
        for i in range(len(eps_series)):
            if eps_series[i] <= 0:
                result['warnings'].append('The stock does not have stable earnings track records for estimating fair value. (negative EPS detected)')
                return result
        
        # Check for consecutive decreases
        consecutive_decreases = 0
        for i in range(1, len(eps_series)):
            if eps_series[i] < eps_series[i - 1]:
                consecutive_decreases += 1
                if consecutive_decreases >= 2:
                    result['warnings'].append('The stock does not have stable earnings track records for estimating fair value. (2+ years of EPS decrease)')
                    return result
            else:
                consecutive_decreases = 0
        
        # STEP 2: Calculate 5-year EPS CAGR
        eps_t5 = eps_series[0]
        eps_t1 = eps_series[4]
        result['epsGrowthRate'] = (eps_t1 / eps_t5) ** (1 / 4) - 1
        
        if not isinstance(result['epsGrowthRate'], (int, float)):
            result['warnings'].append('Failed to calculate valid EPS growth rate')
            return result
        
        # STEP 3: Estimate EPS for next financial year
        result['estimatedEpsT1'] = eps_t1 * (1 + result['epsGrowthRate'])
        
        # STEP 4: Get reference PE level
        for i in range(len(pe_series)):
            if not isinstance(pe_series[i], (int, float)) or pe_series[i] <= 0:
                result['warnings'].append(f'Invalid PE ratio found in historical data: {pe_series[i]}')
                return result
        
        result['referenceAveragePe'] = sum(pe_series) / len(pe_series)
        
        # STEP 5: Calculate expected price for next financial year
        result['expectedPriceTp1'] = result['referenceAveragePe'] * result['estimatedEpsT1']
        
        # STEP 6: Discount expected price
        result['fairValue'] = result['expectedPriceTp1'] / (1 + result['requiredRateOfReturn'])
        
        result['valuationPossible'] = True
        result['assumptions']['actualEpsUsed'] = eps_t1
        result['assumptions']['epsGrowthRatePercent'] = f'{result["epsGrowthRate"] * 100:.2f}'
        result['assumptions']['historicalPeValues'] = pe_series
        result['assumptions']['historicalEpsValues'] = eps_series
        
        return result
        
    except Exception as error:
        result['warnings'].append(f'Error during earnings track valuation: {str(error)}')
        return result


def calculate_asset_based_valuation(params):
    """
    Calculate stock valuation using Asset-based method
    Analyzes 5-year ROE trends and historical PB ratios
    """
    symbol = params['symbol']
    finnhub_api_key = params['finnhubApiKey']
    alpha_vantage_api_key = params.get('alphaVantageApiKey')
    market = params.get('market', 'US')
    market_growth_rate_percent = params.get('marketGrowthRatePercent', 10)
    
    result = {
        'symbol': symbol,
        'market': market,
        'fairValue': None,
        'currentPrice': None,
        'estimatedBookValueT1': None,
        'referencePbLevel': None,
        'averageRoe': None,
        'expectedPriceTp1': None,
        'requiredRateOfReturn': 0.10,
        'valuationPossible': False,
        'warnings': [],
        'assumptions': {
            'method': 'Asset-based (ROE)',
            'requiredRateOfReturn': '10%',
            'notes': [
                'Analysis based on 5-year ROE track record',
                'ROE must be positive across all years',
                'Fair value calculated using forward book value and historical PB average'
            ]
        },
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Get current price from yfinance
        try:
            result['currentPrice'] = fetch_price_from_yfinance(symbol)
        except Exception as error:
            result['warnings'].append(f'Failed to get current price from yfinance: {str(error)}')
            return result
        
        if not isinstance(result['currentPrice'], (int, float)) or result['currentPrice'] <= 0:
            result['warnings'].append(f'Invalid current price: {result["currentPrice"]}')
            return result
        
        # Get historical financial data
        metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={finnhub_api_key}'
        metrics_data = fetch_finnhub(metrics_url)
        
        if 'series' not in metrics_data or 'annual' not in metrics_data['series']:
            result['warnings'].append('No historical series data available from Finnhub')
            return result
        
        # Get current book value per share
        current_metrics = metrics_data.get('metric', {})
        book_value_per_share = None
        
        if 'bookValuePerShareAnnual' in current_metrics and current_metrics['bookValuePerShareAnnual'] is not None:
            book_value_per_share = float(current_metrics['bookValuePerShareAnnual'])
        
        if not isinstance(book_value_per_share, (int, float)) or book_value_per_share <= 0:
            result['warnings'].append('Cannot obtain valid book value per share for valuation')
            return result
        
        # Extract ROE and PB series
        roe_series = []
        pb_series = []
        
        if 'annual' in metrics_data['series'] and 'roe' in metrics_data['series']['annual']:
            roe_array = metrics_data['series']['annual']['roe']
            if isinstance(roe_array, list):
                for i in range(min(5, len(roe_array))):
                    if roe_array[i] and 'v' in roe_array[i] and roe_array[i]['v'] is not None:
                        roe_series.append(float(roe_array[i]['v']))
        
        if 'annual' in metrics_data['series'] and 'pb' in metrics_data['series']['annual']:
            pb_array = metrics_data['series']['annual']['pb']
            if isinstance(pb_array, list):
                for i in range(min(5, len(pb_array))):
                    if pb_array[i] and 'v' in pb_array[i] and pb_array[i]['v'] is not None:
                        pb_series.append(float(pb_array[i]['v']))
        
        # Validate data
        if len(roe_series) < 5:
            result['warnings'].append(f'Insufficient historical ROE data available (only {len(roe_series)} years instead of 5)')
            return result
        
        if len(pb_series) < 5:
            result['warnings'].append(f'Insufficient historical PB data available (only {len(pb_series)} years instead of 5)')
            return result
        
        # Reverse to have oldest first
        roe_series = roe_series[::-1]
        pb_series = pb_series[::-1]
        
        # STEP 1: Validate ROE track record
        for i in range(len(roe_series)):
            if roe_series[i] <= 0:
                result['warnings'].append('The stock does not have stable return on equity track records for estimating fair value.')
                return result
        
        # STEP 2: Calculate average ROE
        result['averageRoe'] = sum(roe_series) / len(roe_series)
        
        if not isinstance(result['averageRoe'], (int, float)) or result['averageRoe'] <= 0:
            result['warnings'].append('Failed to calculate valid average ROE')
            return result
        
        # STEP 3: Estimate book value per share for T+1
        result['estimatedBookValueT1'] = (result['averageRoe'] + 1) * book_value_per_share
        
        # STEP 4: Get reference PB level
        for i in range(len(pb_series)):
            if not isinstance(pb_series[i], (int, float)) or pb_series[i] <= 0:
                result['warnings'].append(f'Invalid PB ratio found in historical data: {pb_series[i]}')
                return result
        
        result['referencePbLevel'] = sum(pb_series) / len(pb_series)
        
        # STEP 5: Calculate expected price for T+1
        result['expectedPriceTp1'] = result['referencePbLevel'] * result['estimatedBookValueT1']
        
        # STEP 6: Discount expected price
        result['fairValue'] = result['expectedPriceTp1'] / (1 + result['requiredRateOfReturn'])
        
        result['valuationPossible'] = True
        result['assumptions']['bookValuePerShareUsed'] = book_value_per_share
        result['assumptions']['averageRoePercent'] = f'{result["averageRoe"]:.2f}'
        result['assumptions']['historicalPbValues'] = pb_series
        result['assumptions']['historicalRoeValues'] = roe_series
        
        return result
        
    except Exception as error:
        result['warnings'].append(f'Error during asset-based valuation: {str(error)}')
        return result


def calculate_dividend_valuation(params):
    """
    Calculate stock valuation using Dividend Valuation method
    Analyzes dividend history and projects future dividends
    """
    symbol = params['symbol']
    finnhub_api_key = params['finnhubApiKey']
    alpha_vantage_api_key = params.get('alphaVantageApiKey')
    market = params.get('market', 'US')
    market_growth_rate_percent = params.get('marketGrowthRatePercent', 10)
    
    result = {
        'symbol': symbol,
        'market': market,
        'fairValue': None,
        'currentPrice': None,
        'historicalDividends': [],
        'dividendGrowthRate': None,
        'estimatedDividendT1': None,
        'federalFundsRate': None,
        'riskPremium': None,
        'referenceDividendYield': None,
        'estimatedPriceTp1': None,
        'requiredRateOfReturn': 0.10,
        'valuationPossible': False,
        'warnings': [],
        'assumptions': {
            'method': 'Dividend Valuation',
            'requiredRateOfReturn': '10%',
            'notes': [
                'Analysis based on 5-year dividend track record (T-5 to T-1)',
                'Dividends consolidated by financial year',
                'Dividend yield = Federal Funds Rate + Risk Premium',
                'Risk Premium = 0 if growth rate > 3%, else 3% - growth rate',
                'Fair value calculated using forward dividend and dividend yield'
            ]
        },
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # STEP 1: Get current price from yfinance
        try:
            result['currentPrice'] = fetch_price_from_yfinance(symbol)
        except Exception as error:
            result['warnings'].append(f'Failed to get current price from yfinance: {str(error)}')
            return result
        
        if not isinstance(result['currentPrice'], (int, float)) or result['currentPrice'] <= 0:
            result['warnings'].append(f'Invalid current price: {result["currentPrice"]}')
            return result
        
        # STEP 2: Get dividend data from Alpha Vantage
        if not alpha_vantage_api_key:
            result['warnings'].append('Alpha Vantage API key required for dividend valuation')
            return result
        
        dividend_url = f'https://www.alphavantage.co/query?function=DIVIDENDS&symbol={symbol}&apikey={alpha_vantage_api_key}'
        dividend_data = fetch_alpha_vantage(dividend_url)
        
        if 'data' not in dividend_data or not isinstance(dividend_data['data'], list) or len(dividend_data['data']) == 0:
            result['warnings'].append('No dividend data available from Alpha Vantage')
            return result
        
        # STEP 3: Get earnings history to determine fiscal year
        fiscal_year_ends = []
        
        try:
            # Use Finnhub API to get fiscal year end dates (avoids Alpha Vantage rate limiting)
            metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=series&token={finnhub_api_key}'
            metrics_series_data = fetch_finnhub(metrics_url)
            
            # Extract fiscal year ends from any annual series data
            if 'series' in metrics_series_data and 'annual' in metrics_series_data['series']:
                annual_data = metrics_series_data['series']['annual']
                # Get periods from the first available annual metric with valid data
                for metric_name, metric_array in annual_data.items():
                    if isinstance(metric_array, list) and len(metric_array) > 0:
                        for item in metric_array:
                            if 'period' in item and item['period']:
                                fiscal_year_ends.append(item['period'])
                        # Use the first metric's periods
                        if len(fiscal_year_ends) > 0:
                            break
                
                # Sort fiscal year ends in chronological order
                fiscal_year_ends = sorted(list(set(fiscal_year_ends)))
        except Exception as error:
            result['warnings'].append(f'Failed to fetch fiscal year dates from Finnhub: {str(error)}')
            return result
        
        if len(fiscal_year_ends) == 0:
            result['warnings'].append('No fiscal year end dates found from Finnhub; cannot properly consolidate dividends by fiscal year')
            return result
        
        # STEP 4: Consolidate dividends by fiscal year
        dividends_by_fiscal_year = {}
        
        # Log available fields from first dividend for debugging
        if dividend_data.get('data') and len(dividend_data['data']) > 0:
            first_dividend_keys = list(dividend_data['data'][0].keys())
            result['warnings'].append(f'Dividend data structure - available fields: {first_dividend_keys}')
        
        for dividend in dividend_data['data']:
            if 'amount' in dividend and 'ex_dividend_date' in dividend:
                try:
                    amount = float(dividend['amount'])
                    if isinstance(amount, (int, float)) and amount > 0:
                        dividend_date = datetime.strptime(dividend['ex_dividend_date'], '%Y-%m-%d')
                        
                        # Find the fiscal year end that this dividend belongs to
                        matched = False
                        for fiscal_year_end in fiscal_year_ends:
                            try:
                                fiscal_end_date = datetime.strptime(fiscal_year_end, '%Y-%m-%d')
                                one_year_before = fiscal_end_date - timedelta(days=365)
                                
                                if one_year_before < dividend_date <= fiscal_end_date:
                                    if fiscal_year_end not in dividends_by_fiscal_year:
                                        dividends_by_fiscal_year[fiscal_year_end] = 0
                                    dividends_by_fiscal_year[fiscal_year_end] += amount
                                    matched = True
                                    break
                            except ValueError:
                                # Skip malformed dates
                                continue
                except (ValueError, TypeError) as e:
                    # Skip dividends with invalid amount or date format
                    continue
            else:
                # Log available fields if expected fields are missing
                if dividend:
                    result['warnings'].append(f'Dividend record missing expected fields (amount or ex_dividend_date). Available: {list(dividend.keys())}')
        
        # Get sorted fiscal years
        sorted_fiscal_years = sorted(dividends_by_fiscal_year.keys())
        
        if len(sorted_fiscal_years) < 5:
            # Build diagnostic message safely
            dividend_date_range = "N/A"
            if dividend_data.get('data'):
                try:
                    earliest = dividend_data['data'][-1].get('ex_dividend_date', 'N/A')
                    latest = dividend_data['data'][0].get('ex_dividend_date', 'N/A')
                    dividend_date_range = f"{earliest} to {latest}"
                except (IndexError, KeyError, TypeError):
                    dividend_date_range = "Unable to determine"
            
            result['warnings'].append(f'Insufficient historical dividend data available (only {len(sorted_fiscal_years)} fiscal years instead of 5). Fiscal years matched: {sorted_fiscal_years}. Dividend dates range: {dividend_date_range}')
            return result
        
        # Extract last 5 fiscal years
        last_5_fiscal_years = sorted(sorted_fiscal_years[-5:])
        result['historicalDividends'] = [
            {'fiscalYearEnding': fy, 'totalDividend': dividends_by_fiscal_year[fy]}
            for fy in last_5_fiscal_years
        ]
        
        dividend_values = [dividends_by_fiscal_year[fy] for fy in last_5_fiscal_years]
        
        # STEP 5: Calculate 4-year dividend CAGR
        dividend_t5 = dividend_values[0]
        dividend_t1 = dividend_values[4]
        
        if dividend_t5 <= 0:
            result['warnings'].append('Initial dividend value is non-positive; cannot calculate valid growth rate')
            return result
        
        result['dividendGrowthRate'] = (dividend_t1 / dividend_t5) ** (1 / 4) - 1
        
        if not isinstance(result['dividendGrowthRate'], (int, float)):
            result['warnings'].append('Failed to calculate valid dividend growth rate')
            return result
        
        # STEP 6: Estimate dividend for T+1
        result['estimatedDividendT1'] = dividend_t1 * (1 + result['dividendGrowthRate'])
        
        # STEP 7: Get Federal Funds Rate
        fed_rates_url = f'https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey={alpha_vantage_api_key}'
        fed_rates_data = fetch_alpha_vantage(fed_rates_url)
        
        current_fed_rate = 0.04
        if fed_rates_data and 'data' in fed_rates_data and isinstance(fed_rates_data['data'], list) and len(fed_rates_data['data']) > 0:
            latest_rate = float(fed_rates_data['data'][0]['value'])
            if isinstance(latest_rate, (int, float)) and latest_rate >= 0:
                current_fed_rate = latest_rate / 100
            else:
                result['warnings'].append('Invalid federal funds rate data; using default 4%')
        else:
            result['warnings'].append('Could not fetch federal funds rate; using default 4%')
        
        result['federalFundsRate'] = current_fed_rate
        
        # STEP 8: Calculate risk premium
        growth_rate_percent = result['dividendGrowthRate'] * 100
        if growth_rate_percent > 3:
            result['riskPremium'] = 0
        else:
            result['riskPremium'] = 0.03 - result['dividendGrowthRate']
        
        # STEP 9: Calculate reference dividend yield
        result['referenceDividendYield'] = result['federalFundsRate'] + result['riskPremium']
        
        if result['referenceDividendYield'] <= 0:
            result['warnings'].append('Dividend yield is non-positive; valuation not possible')
            return result
        
        # STEP 10: Calculate estimated price at T+1
        result['estimatedPriceTp1'] = result['estimatedDividendT1'] / result['referenceDividendYield']
        
        # STEP 11: Discount estimated price
        result['fairValue'] = result['estimatedPriceTp1'] / (1 + result['requiredRateOfReturn'])
        
        result['valuationPossible'] = True
        result['assumptions']['historicalDividendValues'] = dividend_values
        result['assumptions']['dividendGrowthRatePercent'] = f'{result["dividendGrowthRate"] * 100:.2f}'
        result['assumptions']['federalFundsRatePercent'] = f'{result["federalFundsRate"] * 100:.2f}'
        result['assumptions']['riskPremiumPercent'] = f'{result["riskPremium"] * 100:.2f}'
        result['assumptions']['fiscalYearEnds'] = last_5_fiscal_years
        
        return result
        
    except Exception as error:
        result['warnings'].append(f'Error during dividend valuation: {str(error)}')
        return result


def fetch_financial_data(params):
    """
    Fetch comprehensive financial data from Finnhub API
    
    Args:
        params: Dictionary with keys:
            - symbol: Stock symbol
            - finnhubApiKey: Finnhub API key
    
    Returns:
        Dictionary with organized financial data including:
        - financialsReported: Balance sheet, cash flow, and income statement data
        - basicFinancials: EPS and ROE series
    """
    symbol = params['symbol']
    finnhub_api_key = params['finnhubApiKey']
    
    result = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'financialsReported': {
            'balanceSheet': [],
            'incomeStatement': [],
            'cashFlow': []
        },
        'basicFinancials': {
            'eps': [],
            'roe': []
        },
        'warnings': []
    }
    
    try:
        # Fetch Financials Reported data
        financials_url = f'https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&freq=annual&token={finnhub_api_key}'
        financials_data = None
        financials_error = None
        
        try:
            financials_data = fetch_finnhub(financials_url)
        except Exception as e:
            financials_error = str(e)
            result['warnings'].append(f'Error fetching financials-reported: {financials_error}')
        
        if financials_data:
            # Check if response has expected structure
            if 'data' in financials_data and isinstance(financials_data['data'], list) and len(financials_data['data']) > 0:
                data_extracted = False
                for filing in financials_data['data']:
                    if 'report' in filing and isinstance(filing['report'], dict):
                        report = filing['report']
                        fiscal_date = filing.get('endDate', 'N/A')
                        
                        # Extract Balance Sheet data - handle both dict and list formats
                        # if 'bs' in report:
                        #     bs_data = report['bs']
                        #     if isinstance(bs_data, (dict, list)):
                        #         result['financialsReported']['balanceSheet'].append({
                        #             'fiscalDate': fiscal_date,
                        #             'data': bs_data
                        #         })
                        #         data_extracted = True
                        
                        # Extract Income Statement data - handle both dict and list formats
                        # if 'ic' in report:
                        #     ic_data = report['ic']
                        #     if isinstance(ic_data, (dict, list)):
                        #         result['financialsReported']['incomeStatement'].append({
                        #             'fiscalDate': fiscal_date,
                        #             'data': ic_data
                        #         })
                        #         data_extracted = True
                        
                        # Extract Cash Flow Statement data with specific concepts (CFO, CFI, CFF only)
                        if 'cf' in report:
                            cf_data = report['cf']
                            if isinstance(cf_data, (dict, list)):
                                filtered_cf = {}
                                
                                # Map common concept names to user-friendly names
                                concept_mapping = {
                                    'us-gaap_NetCashProvidedByUsedInOperatingActivities': 'operatingActivities',
                                    'us-gaap_NetCashProvidedByUsedInInvestingActivities': 'investingActivities',
                                    'us-gaap_NetCashProvidedByUsedInFinancingActivities': 'financingActivities',
                                    'NetCashProvidedByOperatingActivities': 'operatingActivities',
                                    'NetCashUsedInInvestingActivities': 'investingActivities',
                                    'NetCashUsedInFinancingActivities': 'financingActivities',
                                    'NetCashProvidedByFinancingActivities': 'financingActivities',
                                    'OperatingActivities': 'operatingActivities',
                                    'InvestingActivities': 'investingActivities',
                                    'FinancingActivities': 'financingActivities'
                                }
                                
                                # If cf_data is a dict, extract concept values directly
                                if isinstance(cf_data, dict):
                                    for concept_key, user_name in concept_mapping.items():
                                        if concept_key in cf_data:
                                            filtered_cf[user_name] = cf_data[concept_key]
                                
                                # If cf_data is a list, filter items by concept
                                elif isinstance(cf_data, list):
                                    for item in cf_data:
                                        if isinstance(item, dict):
                                            # Check if item has a concept field that matches our mapping
                                            item_concept = item.get('concept', '')
                                            if item_concept in concept_mapping:
                                                user_name = concept_mapping[item_concept]
                                                item_value = item.get('value')
                                                if item_value is not None:
                                                    filtered_cf[user_name] = item_value
                                
                                # Only include if we found at least one cash flow component
                                if filtered_cf:
                                    result['financialsReported']['cashFlow'].append({
                                        'fiscalDate': fiscal_date,
                                        'data': filtered_cf
                                    })
                                    data_extracted = True
                
                if not data_extracted:
                    # Data list exists but no report found or reports not dictionaries
                    first_filing_keys = list(financials_data['data'][0].keys()) if financials_data['data'] else []
                    first_report = financials_data['data'][0].get('report', {}) if financials_data['data'] else {}
                    first_report_keys = list(first_report.keys()) if isinstance(first_report, dict) else []
                    
                    # Check if report exists but is empty or malformed
                    report_info = ""
                    if first_report:
                        for key in ['bs', 'ic', 'cf']:
                            if key in first_report:
                                report_info += f"{key}: {type(first_report[key]).__name__} with {len(first_report[key]) if isinstance(first_report[key], (dict, list)) else 'N/A'} items; "
                    
                    result['warnings'].append(f'Financials data found but no usable content. Filing keys: {first_filing_keys}, Report keys: {first_report_keys}. {report_info}')
            else:
                # Provide diagnostic info about response structure
                if financials_data:
                    response_keys = list(financials_data.keys())
                    data_info = f"Response keys: {response_keys}"
                    if 'data' in financials_data:
                        if isinstance(financials_data['data'], list):
                            data_info += f", Data list length: {len(financials_data['data'])}"
                            if len(financials_data['data']) > 0:
                                data_info += f", First item keys: {list(financials_data['data'][0].keys())}"
                        else:
                            data_info += f", Data type: {type(financials_data['data']).__name__}"
                    result['warnings'].append(f'No valid financials-reported data found. {data_info}')
        else:
            result['warnings'].append('No financials-reported data retrieved from Finnhub')
        
        # Fetch Basic Financials data (EPS and ROE)
        metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={finnhub_api_key}'
        metrics_data = fetch_finnhub(metrics_url)
        
        # Try to extract from series.annual first (preferred structure)
        eps_extracted = False
        roe_extracted = False
        
        if 'series' in metrics_data and isinstance(metrics_data['series'], dict):
            series = metrics_data['series']
            
            # Check for annual data structure
            if 'annual' in series and isinstance(series['annual'], dict):
                annual_data = series['annual']
                
                # Extract EPS data from different possible keys
                for eps_key in ['epsAnnual', 'eps']:
                    if eps_key in annual_data and isinstance(annual_data[eps_key], list):
                        result['basicFinancials']['eps'] = [
                            {
                                'period': item.get('period', 'N/A'),
                                'value': item.get('v', None)
                            }
                            for item in annual_data[eps_key]
                        ]
                        eps_extracted = len(result['basicFinancials']['eps']) > 0
                        if eps_extracted:
                            break
                
                # Extract ROE data from different possible keys
                for roe_key in ['roeAnnual', 'roe', 'returnOnEquity']:
                    if roe_key in annual_data and isinstance(annual_data[roe_key], list):
                        result['basicFinancials']['roe'] = [
                            {
                                'period': item.get('period', 'N/A'),
                                'value': item.get('v', None)
                            }
                            for item in annual_data[roe_key]
                        ]
                        roe_extracted = len(result['basicFinancials']['roe']) > 0
                        if roe_extracted:
                            break
            
            # Try top-level series keys as fallback
            if not eps_extracted:
                for eps_key in ['epsAnnual', 'eps']:
                    if eps_key in series and isinstance(series[eps_key], dict):
                        eps_dict = series[eps_key]
                        if 'data' in eps_dict and isinstance(eps_dict['data'], list):
                            result['basicFinancials']['eps'] = [
                                {
                                    'period': item.get('period', 'N/A'),
                                    'value': item.get('v', None)
                                }
                                for item in eps_dict['data']
                            ]
                            eps_extracted = len(result['basicFinancials']['eps']) > 0
                            if eps_extracted:
                                break
            
            if not roe_extracted:
                for roe_key in ['roeAnnual', 'roe', 'returnOnEquity']:
                    if roe_key in series and isinstance(series[roe_key], dict):
                        roe_dict = series[roe_key]
                        if 'data' in roe_dict and isinstance(roe_dict['data'], list):
                            result['basicFinancials']['roe'] = [
                                {
                                    'period': item.get('period', 'N/A'),
                                    'value': item.get('v', None)
                                }
                                for item in roe_dict['data']
                            ]
                            roe_extracted = len(result['basicFinancials']['roe']) > 0
                            if roe_extracted:
                                break
        
        # Fallback: Try metrics (point-in-time values)
        if 'metric' in metrics_data:
            metric = metrics_data['metric']
            
            if not eps_extracted:
                # Try different EPS keys
                for eps_key in ['epsAnnual', 'epsTTM', 'epsExclExtraItemsTTM', 'eps']:
                    if eps_key in metric and metric[eps_key] is not None:
                        result['basicFinancials']['eps'].append({
                            'period': 'current',
                            'value': metric[eps_key],
                            'source': eps_key
                        })
                        eps_extracted = True
                        break
            
            if not roe_extracted:
                # Try different ROE keys
                for roe_key in ['roeAnnual', 'roe', 'returnOnEquity']:
                    if roe_key in metric and metric[roe_key] is not None:
                        result['basicFinancials']['roe'].append({
                            'period': 'current',
                            'value': metric[roe_key],
                            'source': roe_key
                        })
                        roe_extracted = True
                        break
        
        # Add detailed warnings if data not found
        if not eps_extracted:
            result['warnings'].append('EPS data not found in expected Finnhub response structure. Available series keys: ' + str(list(metrics_data.get('series', {}).keys()) if 'series' in metrics_data else 'N/A'))
        
        if not roe_extracted:
            result['warnings'].append('ROE data not found in expected Finnhub response structure. Available metric keys: ' + str(list(metrics_data.get('metric', {}).keys())[:10]) if 'metric' in metrics_data else 'N/A')
        
        return result
        
    except Exception as error:
        result['warnings'].append(f'Error fetching financial data: {str(error)}')
        result['error'] = str(error)
        return result
