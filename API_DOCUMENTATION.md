# PEG Stock Valuation Microservice - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication & API Keys](#authentication--api-keys)
4. [Endpoints](#endpoints)
5. [Valuation Methods](#valuation-methods)
6. [Request & Response Examples](#request--response-examples)
7. [Error Handling](#error-handling)
8. [Supported Markets](#supported-markets)
9. [Common Use Cases](#common-use-cases)

---

## Overview

The **PEG Stock Valuation Microservice** is a REST API that calculates fair stock prices using multiple valuation methods:
- **PEG-based Valuation** - Price-to-Earnings Growth ratio calculation
- **Earnings Track Method** - Based on earnings momentum and track record
- **Asset-based Valuation** - Market capitalization relative to assets
- **Dividend Valuation** - Dividend discount model

**Base URL:** `http://localhost:3000`

**Service Version:** 1.0.0

---

## Getting Started

### Prerequisites
1. **Finnhub API Key** - Required for all valuation endpoints
   - Get it at: https://finnhub.io
   
2. **Alpha Vantage API Key** - Required for dividend valuation, optional for others
   - Get it at: https://www.alphavantage.co

### Quick Start Example

```bash
# Health check
curl "http://localhost:3000/health"

# Get API documentation
curl "http://localhost:3000/api/docs"

# Valuate a stock (requires Finnhub API key)
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_KEY"
```

---

## Authentication & API Keys

### Method 1: Query Parameters
Pass API keys directly in the request URL:

```bash
http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_KEY&alphaVantageApiKey=YOUR_KEY
```

### Method 2: Environment Variables
Set API keys as environment variables (more secure):

```bash
# Windows (PowerShell)
$env:FINNHUB_API_KEY = "your-finnhub-key"
$env:ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-key"

# Linux/Mac
export FINNHUB_API_KEY="your-finnhub-key"
export ALPHA_VANTAGE_API_KEY="your-alpha-vantage-key"
```

Then make requests without API keys in the URL:

```bash
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL"
```

**Note:** Environment variables are checked if API keys are not provided in the request.

---

## Endpoints

### 1. Health Check

Check if the service is running and get uptime information.

**Endpoint:** `GET /health`

**Query Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "uptime": 3600.5
}
```

---

### 2. API Documentation

Get the complete API documentation in JSON format.

**Endpoint:** `GET /api/docs`

**Query Parameters:** None

**Response:** Returns detailed documentation for all available endpoints

---

### 3. PEG Valuation

Calculate fair stock value using the PEG-based valuation method.

**Endpoint:** `GET /api/valuation/peg`

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `symbol` | string | ✅ Yes | - | Stock ticker symbol (e.g., AAPL, MSFT) |
| `finnhubApiKey` | string | ✅ Yes* | - | Finnhub API key (or use FINNHUB_API_KEY env var) |
| `alphaVantageApiKey` | string | ❌ No | - | Alpha Vantage API key (or use ALPHA_VANTAGE_API_KEY env var) |
| `market` | string | ❌ No | US | Market: "US" or "HK" |
| `marketGrowthRatePercent` | float | ❌ No | 10 | Expected market growth rate (positive number) |

*Can be provided via environment variable

**Example Request:**
```bash
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_KEY&market=US&marketGrowthRatePercent=10"
```

**Response:**
```json
{
  "symbol": "AAPL",
  "market": "US",
  "fairValue": 185.42,
  "currentPrice": 180.50,
  "beta": 1.2,
  "actualEps": 6.05,
  "estimatedEps": 6.50,
  "stockPe": 29.83,
  "stockPeg": 1.35,
  "growthRate": 9.8,
  "marketPe": 25.5,
  "marketPeg": 1.1,
  "valuationPossible": true,
  "warnings": [],
  "assumptions": {
    "marketGrowthRate": 10,
    "dataSource": "Finnhub",
    "priceDate": "2024-01-15"
  }
}
```

---

### 4. PEG Batch Valuation

Valuate multiple stocks in a single request using the PEG method.

**Endpoint:** `GET /api/valuation/peg/batch`

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `symbols` | string | ✅ Yes | - | Comma-separated stock symbols (e.g., AAPL,MSFT,GOOGL) |
| `finnhubApiKey` | string | ✅ Yes* | - | Finnhub API key |
| `alphaVantageApiKey` | string | ❌ No | - | Alpha Vantage API key |
| `markets` | string | ❌ No | US | Comma-separated markets (must match symbols count) |
| `marketGrowthRatePercent` | float | ❌ No | 10 | Expected market growth rate |

*Can be provided via environment variable

**Example Request:**
```bash
curl "http://localhost:3000/api/valuation/peg/batch?symbols=AAPL,MSFT,GOOGL&finnhubApiKey=YOUR_KEY&markets=US,US,US"
```

**Response:**
```json
{
  "processingTime": "2024-01-15T10:30:45.123456",
  "count": 3,
  "results": [
    {
      "symbol": "AAPL",
      "fairValue": 185.42,
      "currentPrice": 180.50,
      "valuationPossible": true
    },
    {
      "symbol": "MSFT",
      "fairValue": 380.25,
      "currentPrice": 375.10,
      "valuationPossible": true
    },
    {
      "symbol": "GOOGL",
      "error": "Insufficient data for valuation",
      "valuationPossible": false
    }
  ]
}
```

---

### 5. Earnings Track Valuation

Calculate fair value using the Earnings Track method, focusing on earnings momentum.

**Endpoint:** `GET /api/valuation/earning_track`

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `symbol` | string | ✅ Yes | - | Stock ticker symbol |
| `finnhubApiKey` | string | ✅ Yes* | - | Finnhub API key |
| `alphaVantageApiKey` | string | ❌ No | - | Alpha Vantage API key |
| `market` | string | ❌ No | US | Market: "US" or "HK" |
| `marketGrowthRatePercent` | float | ❌ No | 10 | Expected market growth rate |

**Example Request:**
```bash
curl "http://localhost:3000/api/valuation/earning_track?symbol=AAPL&finnhubApiKey=YOUR_KEY"
```

---

### 6. Asset-Based Valuation

Calculate fair value based on company assets relative to market capitalization.

**Endpoint:** `GET /api/valuation/asset`

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `symbol` | string | ✅ Yes | - | Stock ticker symbol |
| `finnhubApiKey` | string | ✅ Yes* | - | Finnhub API key |
| `alphaVantageApiKey` | string | ❌ No | - | Alpha Vantage API key |
| `market` | string | ❌ No | US | Market: "US" or "HK" |
| `marketGrowthRatePercent` | float | ❌ No | 10 | Expected market growth rate |

**Example Request:**
```bash
curl "http://localhost:3000/api/valuation/asset?symbol=JPM&finnhubApiKey=YOUR_KEY"
```

---

### 7. Dividend Valuation

Calculate fair value for dividend-paying stocks using the Dividend Discount Model.

**Endpoint:** `GET /api/valuation/dividend`

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `symbol` | string | ✅ Yes | - | Stock ticker symbol |
| `finnhubApiKey` | string | ✅ Yes* | - | Finnhub API key |
| `alphaVantageApiKey` | string | ✅ Yes* | - | **REQUIRED** - Alpha Vantage API key (dividend history) |
| `market` | string | ❌ No | US | Market: "US" or "HK" |
| `marketGrowthRatePercent` | float | ❌ No | 10 | Expected market growth rate |

**Example Request:**
```bash
curl "http://localhost:3000/api/valuation/dividend?symbol=JNJ&finnhubApiKey=YOUR_KEY&alphaVantageApiKey=YOUR_KEY"
```

**Note:** This endpoint requires both API keys. It retrieves dividend history which is essential for the calculation.

---

## Valuation Methods

### PEG-Based Valuation
**Method:** Price-to-Earnings Growth ratio analysis
- Compares stock PEG to market PEG
- Considers earnings growth rate
- Accounts for market conditions
- **Best for:** Growth companies with consistent earnings

### Earnings Track Valuation
**Method:** Earnings momentum analysis
- Focuses on earnings trends and acceleration
- Evaluates historical earnings performance
- Considers future estimates
- **Best for:** Companies with strong earnings growth

### Asset-Based Valuation
**Method:** Book value analysis
- Compares market cap to total assets
- Useful for asset-heavy companies
- Provides intrinsic value assessment
- **Best for:** Mature, stable companies; financial institutions

### Dividend Valuation
**Method:** Dividend Discount Model (DDM)
- Projects future dividend payments
- Calculates present value
- Assumes consistent dividend policy
- **Best for:** Dividend-paying, mature companies

---

## Request & Response Examples

### Example 1: Basic PEG Valuation

```bash
# Request
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_FINNHUB_KEY"

# Response (200 OK)
{
  "symbol": "AAPL",
  "market": "US",
  "fairValue": 185.42,
  "currentPrice": 180.50,
  "beta": 1.2,
  "actualEps": 6.05,
  "estimatedEps": 6.50,
  "stockPe": 29.83,
  "stockPeg": 1.35,
  "growthRate": 9.8,
  "marketPe": 25.5,
  "marketPeg": 1.1,
  "valuationPossible": true,
  "warnings": ["Market growth rate assumption: 10%"],
  "assumptions": {
    "marketGrowthRate": 10,
    "dataSource": "Finnhub",
    "priceDate": "2024-01-15"
  }
}
```

### Example 2: Batch Valuation

```bash
# Request
curl "http://localhost:3000/api/valuation/peg/batch?symbols=AAPL,MSFT&finnhubApiKey=YOUR_KEY"

# Response (200 OK)
{
  "processingTime": "2024-01-15T10:35:20.543210",
  "count": 2,
  "results": [
    {
      "symbol": "AAPL",
      "fairValue": 185.42,
      "currentPrice": 180.50,
      "valuationPossible": true,
      "stockPeg": 1.35
    },
    {
      "symbol": "MSFT",
      "fairValue": 380.25,
      "currentPrice": 375.10,
      "valuationPossible": true,
      "stockPeg": 1.22
    }
  ]
}
```

### Example 3: Dividend Stock Valuation

```bash
# Request
curl "http://localhost:3000/api/valuation/dividend?symbol=JNJ&finnhubApiKey=YOUR_FINNHUB_KEY&alphaVantageApiKey=YOUR_AV_KEY"

# Response (200 OK)
{
  "symbol": "JNJ",
  "market": "US",
  "fairValue": 155.30,
  "currentPrice": 152.80,
  "dividendYield": 2.85,
  "estimatedAnnualDividend": 4.24,
  "recentDividendHistory": [4.22, 4.20, 4.15, 4.10],
  "valuationPossible": true,
  "warnings": [],
  "assumptions": {
    "dividendGrowthRate": 5.2,
    "requiredReturn": 8.5,
    "lastDividendDate": "2024-01-10"
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow this standard format:

```json
{
  "error": "Error Category",
  "message": "Detailed error message",
  "timestamp": "2024-01-15T10:35:20.123456"
}
```

### Common HTTP Status Codes

| Status | Meaning | Possible Causes |
|--------|---------|-----------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Missing required parameters, invalid values |
| 404 | Not Found | Invalid endpoint |
| 500 | Internal Server Error | API failures, data source issues |

### Common Error Scenarios

#### 1. Missing Required Parameter
```json
{
  "error": "Bad Request",
  "message": "Missing required fields: symbol is required, and finnhubApiKey must be provided in request or FINNHUB_API_KEY environment variable",
  "receivedFields": {
    "symbol": "missing",
    "finnhubApiKey": "missing"
  }
}
```

#### 2. Invalid Market
```json
{
  "error": "Bad Request",
  "message": "Invalid market. Must be \"US\" or \"HK\"",
  "received": "JP"
}
```

#### 3. Invalid Market Growth Rate
```json
{
  "error": "Bad Request",
  "message": "marketGrowthRatePercent must be a positive number",
  "received": -5
}
```

#### 4. External API Error
```json
{
  "error": "Internal Server Error",
  "message": "Failed to fetch data from Finnhub API: Invalid API key",
  "timestamp": "2024-01-15T10:35:20.123456"
}
```

#### 5. Insufficient Data
```json
{
  "error": "Bad Request",
  "message": "Cannot calculate valuation: Insufficient data for symbol UNKNOWN",
  "symbol": "UNKNOWN",
  "valuationPossible": false
}
```

---

## Supported Markets

The API supports the following markets:

| Market Code | Market Name | Notes |
|-------------|------------|-------|
| `US` | United States | Default market, most data available |
| `HK` | Hong Kong | Limited symbols, some data constraints |

**Example:**
```bash
# US market
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&market=US&finnhubApiKey=YOUR_KEY"

# Hong Kong market  
curl "http://localhost:3000/api/valuation/peg?symbol=0700&market=HK&finnhubApiKey=YOUR_KEY"
```

---

## Common Use Cases

### Use Case 1: Find Undervalued Stocks

Compare calculated fair value with current price:

```bash
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_KEY" | jq '{
  symbol: .symbol,
  current: .currentPrice,
  fair: .fairValue,
  discount: ((.fairValue - .currentPrice) / .currentPrice * 100)
}'
```

**Output:**
```json
{
  "symbol": "AAPL",
  "current": 180.50,
  "fair": 185.42,
  "discount": 2.73
}
```

### Use Case 2: Screen Multiple Stocks

Get valuations for a portfolio:

```bash
curl "http://localhost:3000/api/valuation/peg/batch?symbols=AAPL,MSFT,GOOGL,AMZN&finnhubApiKey=YOUR_KEY"
```

### Use Case 3: Analyze Dividend Stocks

Evaluate dividend-paying stocks:

```bash
curl "http://localhost:3000/api/valuation/dividend?symbol=JNJ&finnhubApiKey=YOUR_KEY&alphaVantageApiKey=YOUR_KEY" | jq '{
  symbol: .symbol,
  current: .currentPrice,
  fair: .fairValue,
  yield: .dividendYield
}'
```

### Use Case 4: Compare Valuation Methods

Use different methods for comprehensive analysis:

```bash
# PEG method
curl "http://localhost:3000/api/valuation/peg?symbol=AAPL&finnhubApiKey=YOUR_KEY"

# Earnings Track method
curl "http://localhost:3000/api/valuation/earning_track?symbol=AAPL&finnhubApiKey=YOUR_KEY"

# Asset-based method
curl "http://localhost:3000/api/valuation/asset?symbol=AAPL&finnhubApiKey=YOUR_KEY"
```

Compare the results to get a range of fair values.

---

## Tips & Best Practices

1. **Use Environment Variables** - Store API keys securely using environment variables rather than embedding them in URLs

2. **Handle Rate Limits** - External APIs have rate limits. Consider caching results and implementing retry logic

3. **Validate Inputs** - Always validate stock symbols and parameters before sending requests

4. **Multiple Valuations** - Use different methods and compare results for better investment decisions

5. **Monitor Warnings** - Pay attention to warnings in responses about data quality or assumptions

6. **Error Handling** - Implement proper error handling in your client applications

7. **Market-Specific Data** - Ensure you're using the correct market code (US/HK) for accurate results

---

## Support & Troubleshooting

**Service won't start?**
- Check that required environment variables are set
- Verify API keys are valid
- Check port 3000 is not in use

**Getting API errors?**
- Verify API keys (Finnhub, Alpha Vantage)
- Check that stock symbols are valid
- Review rate limits on external APIs

**Valuation shows warnings?**
- Review the 'warnings' field in the response
- Some stocks may have insufficient data
- Try alternative valuation methods

**Need help?**
- Check `/api/docs` endpoint for live documentation
- Review this documentation
- Check `/health` endpoint to verify service status

