"""
PEG Stock Valuation Microservice
REST API for calculating fair value using PEG-based valuation model

Base URL: http://localhost:3000

Endpoints:
- POST /api/valuation - Calculate stock fair value
- GET /health - Health check
- GET /api/docs - API documentation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import time
from dotenv import load_dotenv
from app.valuation import (
    calculate_stock_valuation,
    calculate_earnings_track_valuation,
    calculate_asset_based_valuation,
    calculate_dividend_valuation,
    fetch_financial_data
)

load_dotenv()

app = Flask(__name__)
CORS(app)

PORT = int(os.getenv('PORT', 3000))
START_TIME = time.time()

# Request logging middleware
@app.before_request
def log_request():
    print(f"{datetime.now().isoformat()} - {request.method} {request.path}")


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    GET /health
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - START_TIME
    })


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """
    API Documentation endpoint
    GET /api/docs
    """
    return jsonify({
        'service': 'PEG Stock Valuation Microservice',
        'version': '1.0.0',
        'baseUrl': f'http://localhost:{PORT}',
        'endpoints': {
            'GET /api/valuation/peg': {
                'description': 'Calculate fair value of a stock using PEG-based valuation',
                'requestBody': {
                    'required': ['symbol'],
                    'optional': ['finnhubApiKey', 'alphaVantageApiKey', 'market', 'marketGrowthRatePercent'],
                    'notes': [
                        'finnhubApiKey: provide in request OR set FINNHUB_API_KEY environment variable',
                        'alphaVantageApiKey: provide in request OR set ALPHA_VANTAGE_API_KEY environment variable'
                    ],
                    'exampleWithApiKeys': {
                        'symbol': 'AAPL',
                        'finnhubApiKey': 'your-key',
                        'alphaVantageApiKey': 'your-key',
                        'market': 'US',
                        'marketGrowthRatePercent': 10
                    },
                    'exampleWithEnvironmentVars': {
                        'symbol': 'AAPL'
                    }
                },
                'response': {
                    'symbol': 'string',
                    'market': 'string',
                    'fairValue': 'number | null',
                    'currentPrice': 'number',
                    'beta': 'number',
                    'actualEps': 'number',
                    'estimatedEps': 'number',
                    'stockPe': 'number',
                    'stockPeg': 'number',
                    'growthRate': 'number',
                    'marketPe': 'number',
                    'marketPeg': 'number',
                    'valuationPossible': 'boolean',
                    'warnings': 'string[]',
                    'assumptions': 'object'
                }
            },
            'GET /api/valuation/earning_track': {
                'description': 'Calculate fair value of a stock using Earnings Track method',
                'requestBody': {
                    'required': ['symbol'],
                    'optional': ['finnhubApiKey', 'alphaVantageApiKey', 'market', 'marketGrowthRatePercent'],
                    'notes': [
                        'finnhubApiKey: provide in request OR set FINNHUB_API_KEY environment variable',
                        'alphaVantageApiKey: provide in request OR set ALPHA_VANTAGE_API_KEY environment variable'
                    ],
                    'exampleWithEnvironmentVars': {
                        'symbol': 'AAPL'
                    }
                }
            },
            'GET /api/valuation/asset': {
                'description': 'Calculate fair value of a stock using Asset-based valuation method',
                'requestBody': {
                    'required': ['symbol'],
                    'optional': ['finnhubApiKey', 'alphaVantageApiKey', 'market', 'marketGrowthRatePercent'],
                    'notes': [
                        'finnhubApiKey: provide in request OR set FINNHUB_API_KEY environment variable',
                        'alphaVantageApiKey: provide in request OR set ALPHA_VANTAGE_API_KEY environment variable'
                    ],
                    'exampleWithEnvironmentVars': {
                        'symbol': 'AAPL'
                    }
                }
            },
            'GET /api/valuation/dividend': {
                'description': 'Calculate fair value of a dividend stock using Dividend Valuation method',
                'requestBody': {
                    'required': ['symbol'],
                    'optional': ['finnhubApiKey', 'alphaVantageApiKey'],
                    'notes': [
                        'finnhubApiKey: provide in request OR set FINNHUB_API_KEY environment variable',
                        'alphaVantageApiKey: REQUIRED - provide in request OR set ALPHA_VANTAGE_API_KEY environment variable',
                        'Method requires dividend history from Alpha Vantage API'
                    ],
                    'exampleWithEnvironmentVars': {
                        'symbol': 'JNJ'
                    }
                }
            },
            'GET /health': {
                'description': 'Service health check',
                'response': {
                    'status': 'string',
                    'timestamp': 'string',
                    'uptime': 'number'
                }
            },
            'GET /api/data': {
                'description': 'Fetch comprehensive financial data from Finnhub API',
                'requestBody': {
                    'required': ['symbol'],
                    'optional': ['finnhubApiKey'],
                    'notes': [
                        'finnhubApiKey: provide in request OR set FINNHUB_API_KEY environment variable',
                        'Returns: Financials Reported (balance sheet, income statement, cash flow) and Basic Financials (EPS, ROE)'
                    ],
                    'exampleWithApiKey': {
                        'symbol': 'AAPL',
                        'finnhubApiKey': 'your-key'
                    },
                    'exampleWithEnvironmentVar': {
                        'symbol': 'AAPL'
                    }
                },
                'response': {
                    'symbol': 'string',
                    'timestamp': 'string',
                    'financialsReported': {
                        'balanceSheet': 'array',
                        'incomeStatement': 'array',
                        'cashFlow': 'array'
                    },
                    'basicFinancials': {
                        'eps': 'array',
                        'roe': 'array'
                    },
                    'warnings': 'string[]'
                }
            },
            'GET /api/docs': {
                'description': 'API documentation (this endpoint)'
            }
        }
    })


@app.route('/api/valuation/peg', methods=['GET'])
def valuation_peg():
    """
    Calculate stock valuation using PEG method
    GET /api/valuation/peg
    """
    try:
        symbol = request.args.get('symbol')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')
        alpha_vantage_api_key = request.args.get('alphaVantageApiKey') or os.getenv('ALPHA_VANTAGE_API_KEY')
        market = request.args.get('market', 'US')
        market_growth_rate_percent = request.args.get('marketGrowthRatePercent', type=float, default=10)

        # Validate required fields
        if not symbol or not finnhub_api_key:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbol is required, and finnhubApiKey must be provided in request or FINNHUB_API_KEY environment variable',
                'receivedFields': {
                    'symbol': 'provided' if symbol else 'missing',
                    'finnhubApiKey': 'provided in query' if request.args.get('finnhubApiKey') else ('using environment variable' if os.getenv('FINNHUB_API_KEY') else 'missing')
                }
            }), 400

        # Validate market
        if market not in ['US', 'HK']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid market. Must be "US" or "HK"',
                'received': market
            }), 400

        # Validate market growth rate
        if market_growth_rate_percent <= 0:
            return jsonify({
                'error': 'Bad Request',
                'message': 'marketGrowthRatePercent must be a positive number',
                'received': market_growth_rate_percent
            }), 400

        result = calculate_stock_valuation({
            'symbol': symbol.upper(),
            'finnhubApiKey': finnhub_api_key,
            'alphaVantageApiKey': alpha_vantage_api_key,
            'market': market,
            'marketGrowthRatePercent': market_growth_rate_percent
        })

        return jsonify(result)

    except Exception as error:
        print(f'Valuation error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/valuation/earning_track', methods=['GET'])
def valuation_earning_track():
    """
    Calculate stock valuation using Earnings Track method
    GET /api/valuation/earning_track
    """
    try:
        symbol = request.args.get('symbol')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')
        alpha_vantage_api_key = request.args.get('alphaVantageApiKey') or os.getenv('ALPHA_VANTAGE_API_KEY')
        market = request.args.get('market', 'US')
        market_growth_rate_percent = request.args.get('marketGrowthRatePercent', type=float, default=10)

        # Validate required fields
        if not symbol or not finnhub_api_key:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbol is required, and finnhubApiKey must be provided in request or FINNHUB_API_KEY environment variable',
                'receivedFields': {
                    'symbol': 'provided' if symbol else 'missing',
                    'finnhubApiKey': 'provided in query' if request.args.get('finnhubApiKey') else ('using environment variable' if os.getenv('FINNHUB_API_KEY') else 'missing')
                }
            }), 400

        # Validate market
        if market not in ['US', 'HK']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid market. Must be "US" or "HK"',
                'received': market
            }), 400

        # Validate market growth rate
        if market_growth_rate_percent <= 0:
            return jsonify({
                'error': 'Bad Request',
                'message': 'marketGrowthRatePercent must be a positive number',
                'received': market_growth_rate_percent
            }), 400

        result = calculate_earnings_track_valuation({
            'symbol': symbol.upper(),
            'finnhubApiKey': finnhub_api_key,
            'alphaVantageApiKey': alpha_vantage_api_key,
            'market': market,
            'marketGrowthRatePercent': market_growth_rate_percent
        })

        return jsonify(result)

    except Exception as error:
        print(f'Earnings Track valuation error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/valuation/asset', methods=['GET'])
def valuation_asset():
    """
    Calculate stock valuation using Asset-based method
    GET /api/valuation/asset
    """
    try:
        symbol = request.args.get('symbol')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')
        alpha_vantage_api_key = request.args.get('alphaVantageApiKey') or os.getenv('ALPHA_VANTAGE_API_KEY')
        market = request.args.get('market', 'US')
        market_growth_rate_percent = request.args.get('marketGrowthRatePercent', type=float, default=10)

        # Validate required fields
        if not symbol or not finnhub_api_key:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbol is required, and finnhubApiKey must be provided in request or FINNHUB_API_KEY environment variable',
                'receivedFields': {
                    'symbol': 'provided' if symbol else 'missing',
                    'finnhubApiKey': 'provided in query' if request.args.get('finnhubApiKey') else ('using environment variable' if os.getenv('FINNHUB_API_KEY') else 'missing')
                }
            }), 400

        # Validate market
        if market not in ['US', 'HK']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid market. Must be "US" or "HK"',
                'received': market
            }), 400

        # Validate market growth rate
        if market_growth_rate_percent <= 0:
            return jsonify({
                'error': 'Bad Request',
                'message': 'marketGrowthRatePercent must be a positive number',
                'received': market_growth_rate_percent
            }), 400

        result = calculate_asset_based_valuation({
            'symbol': symbol.upper(),
            'finnhubApiKey': finnhub_api_key,
            'alphaVantageApiKey': alpha_vantage_api_key,
            'market': market,
            'marketGrowthRatePercent': market_growth_rate_percent
        })

        return jsonify(result)

    except Exception as error:
        print(f'Asset-based valuation error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/valuation/dividend', methods=['GET'])
def valuation_dividend():
    """
    Calculate stock valuation using Dividend method
    GET /api/valuation/dividend
    """
    try:
        symbol = request.args.get('symbol')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')
        alpha_vantage_api_key = request.args.get('alphaVantageApiKey') or os.getenv('ALPHA_VANTAGE_API_KEY')
        market = request.args.get('market', 'US')
        market_growth_rate_percent = request.args.get('marketGrowthRatePercent', type=float, default=10)

        # Validate required fields
        if not symbol or not finnhub_api_key or not alpha_vantage_api_key:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbol, finnhubApiKey, and alphaVantageApiKey are required',
                'receivedFields': {
                    'symbol': 'provided' if symbol else 'missing',
                    'finnhubApiKey': 'provided in query' if request.args.get('finnhubApiKey') else ('using environment variable' if os.getenv('FINNHUB_API_KEY') else 'missing'),
                    'alphaVantageApiKey': 'provided in query' if request.args.get('alphaVantageApiKey') else ('using environment variable' if os.getenv('ALPHA_VANTAGE_API_KEY') else 'missing')
                }
            }), 400

        # Validate market
        if market not in ['US', 'HK']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid market. Must be "US" or "HK"',
                'received': market
            }), 400

        # Validate market growth rate
        if market_growth_rate_percent <= 0:
            return jsonify({
                'error': 'Bad Request',
                'message': 'marketGrowthRatePercent must be a positive number',
                'received': market_growth_rate_percent
            }), 400

        result = calculate_dividend_valuation({
            'symbol': symbol.upper(),
            'finnhubApiKey': finnhub_api_key,
            'alphaVantageApiKey': alpha_vantage_api_key,
            'market': market,
            'marketGrowthRatePercent': market_growth_rate_percent
        })

        return jsonify(result)

    except Exception as error:
        print(f'Dividend valuation error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/valuation/peg/batch', methods=['GET'])
def valuation_batch():
    """
    Batch valuation endpoint
    GET /api/valuation/peg/batch
    """
    try:
        symbols = request.args.get('symbols')
        markets = request.args.get('markets')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')
        alpha_vantage_api_key = request.args.get('alphaVantageApiKey') or os.getenv('ALPHA_VANTAGE_API_KEY')
        market_growth_rate_percent = request.args.get('marketGrowthRatePercent', type=float, default=10)

        if not finnhub_api_key or not symbols:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbols query parameter is required, and finnhubApiKey must be provided in query or FINNHUB_API_KEY environment variable'
            }), 400

        # Parse comma-separated symbols
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        if not symbol_list:
            return jsonify({
                'error': 'Bad Request',
                'message': 'symbols cannot be empty'
            }), 400

        # Parse comma-separated markets (if provided)
        market_list = [m.strip() for m in markets.split(',')] if markets else ['US'] * len(symbol_list)

        # Process all valuations
        results = []
        for i, symbol in enumerate(symbol_list):
            try:
                result = calculate_stock_valuation({
                    'symbol': symbol.upper(),
                    'finnhubApiKey': finnhub_api_key,
                    'alphaVantageApiKey': alpha_vantage_api_key,
                    'market': market_list[i] if i < len(market_list) else 'US',
                    'marketGrowthRatePercent': market_growth_rate_percent
                })
                results.append(result)
            except Exception as error:
                results.append({
                    'symbol': symbol,
                    'error': str(error),
                    'valuationPossible': False
                })

        return jsonify({
            'processingTime': datetime.now().isoformat(),
            'count': len(results),
            'results': results
        })

    except Exception as error:
        print(f'Batch valuation error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/data', methods=['GET'])
def fetch_data():
    """
    Fetch comprehensive financial data from Finnhub API
    GET /api/data
    """
    try:
        symbol = request.args.get('symbol')
        finnhub_api_key = request.args.get('finnhubApiKey') or os.getenv('FINNHUB_API_KEY')

        # Validate required fields
        if not symbol or not finnhub_api_key:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing required fields: symbol is required, and finnhubApiKey must be provided in request or FINNHUB_API_KEY environment variable',
                'receivedFields': {
                    'symbol': 'provided' if symbol else 'missing',
                    'finnhubApiKey': 'provided in query' if request.args.get('finnhubApiKey') else ('using environment variable' if os.getenv('FINNHUB_API_KEY') else 'missing')
                }
            }), 400

        result = fetch_financial_data({
            'symbol': symbol.upper(),
            'finnhubApiKey': finnhub_api_key
        })

        return jsonify(result)

    except Exception as error:
        print(f'Financial data fetch error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({
        'error': 'Not Found',
        'message': f'Endpoint {request.method} {request.path} not found',
        'availableEndpoints': [
            'GET /health',
            'GET /api/docs',
            'GET /api/data',
            'GET /api/valuation/peg',
            'GET /api/valuation/peg/batch',
            'GET /api/valuation/earning_track',
            'GET /api/valuation/asset',
            'GET /api/valuation/dividend'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Error handler"""
    print(f'Unhandled error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }), 500


if __name__ == '__main__':
    print(f'🚀 PEG Stock Valuation Microservice running on http://localhost:{PORT}')
    print(f'📚 API Documentation: http://localhost:{PORT}/api/docs')
    print(f'❤️  Health check: http://localhost:{PORT}/health')
    app.run(host='0.0.0.0', port=PORT, debug=False)
