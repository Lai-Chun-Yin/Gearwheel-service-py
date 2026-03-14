# Python Setup Guide

This directory contains the Python version of the PEG Stock Valuation Microservice.

**Language**: Python 3.8+  
**Framework**: Flask  
**Dependencies**: See `requirements.txt`

## Quick Start

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys

# Run the server
python app.py
```

### Option 2: Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys

# Run the server
python app.py
```

## API Endpoints

All endpoints return JSON responses and follow the same structure as the JavaScript version.

### 1. Health Check
```
GET /health
```

### 2. API Documentation
```
GET /api/docs
```

### 3. PEG Valuation (Single Stock)
```
GET /api/valuation/peg?symbol=AAPL&market=US
```

### 4. Earnings Track Valuation
```
GET /api/valuation/earning_track?symbol=AAPL
```

### 5. Asset-Based Valuation
```
GET /api/valuation/asset?symbol=AAPL
```

### 6. Dividend Valuation
```
GET /api/valuation/dividend?symbol=JNJ
```

### 7. Batch Valuation (Multiple Stocks)
```
GET /api/valuation/peg/batch?symbols=AAPL,MSFT,GOOGL
```

## Testing

### Using Python Script
```python
python TESTING_EXAMPLES.py
```

### Using curl
```bash
# Health check
curl http://localhost:3000/health

# API documentation
curl http://localhost:3000/api/docs

# Single valuation
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL"

# Batch valuation
curl "http://localhost:3000/api/valuation/peg/batch?symbols=AAPL,MSFT,GOOGL"
```

### Using Python Requests
```python
import requests

# Health check
response = requests.get('http://localhost:3000/health')
print(response.json())

# Get valuation
response = requests.get('http://localhost:3000/api/valuation/peg', params={'symbol': 'AAPL'})
print(response.json())
```

## Configuration

### Environment Variables (.env)

```dotenv
PORT=3000
FINNHUB_API_KEY=your_finnhub_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

- **PORT**: Server port (default: 3000)
- **FINNHUB_API_KEY**: Your Finnhub API key (required)
- **ALPHA_VANTAGE_API_KEY**: Your Alpha Vantage API key (optional, required for dividend valuation)

### Obtaining API Keys

1. **Finnhub API**: https://finnhub.io
   - Register for a free account
   - Get your API key from the dashboard

2. **Alpha Vantage API**: https://www.alphavantage.co
   - Register for a free account
   - Get your API key from the dashboard

## File Structure

```
Gearwheel microservice/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── TESTING_EXAMPLES.py    # Example API testing code
├── TESTING_EXAMPLES.js    # Original JavaScript examples
├── README.md              # General documentation
├── PYTHON_SETUP.md        # This file
├── DEPLOYMENT.md          # Deployment guide
├── .env.example           # Environment variables template
├── .env                   # Environment variables (local, not tracked)
├── .gitignore             # Git ignore rules
├── lib/
│   ├── __init__.py       # Python package init
│   └── valuation.py      # Valuation business logic
└── [other files]
```

## Key Differences from JavaScript Version

1. **Web Framework**: Flask (Python) instead of Express (JavaScript)
2. **HTTP Client**: `requests` library instead of `fetch()`
3. **Async Handling**: Not using async/await, but Flask handles concurrent requests naturally
4. **Config**: Uses `python-dotenv` instead of JavaScript `dotenv`
5. **Startup**: Run with `python app.py` instead of `node app.js`

## Performance Notes

- Flask development server is suitable for testing and development
- For production, use a production WSGI server like Gunicorn:
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:3000 app:app
  ```

## Troubleshooting

### Module Not Found Error
```
ModuleNotFoundError: No module named 'flask'
```
Solution: Ensure virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Port Already in Use
If port 3000 is already in use, set a different port:
```bash
PORT=5000 python app.py
```

### API Key Issues
- Verify both `.env` file exists and contains valid API keys
- Or pass API keys as query parameters: `?finnhubApiKey=YOUR_KEY`

## API Response Format

All endpoints return responses in the same JSON format as the JavaScript version. Example:

```json
{
  "symbol": "AAPL",
  "market": "US",
  "fairValue": 150.25,
  "currentPrice": 145.30,
  "beta": 1.2,
  "actualEps": 5.61,
  "estimatedEps": 6.05,
  "stockPe": 25.89,
  "stockPeg": 1.89,
  "growthRate": 0.0784,
  "marketPe": 29,
  "marketPeg": 2.148,
  "valuationPossible": true,
  "warnings": [],
  "assumptions": {...}
}
```

## Further Help

For detailed API documentation, visit:
```
http://localhost:3000/api/docs
```

Or check the original JavaScript documentation in `README.md`
