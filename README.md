## 📄 README.md (versión final)

```markdown
# PayJoy – Currency Converter

Technical assessment for the **Automation Engineer – Tools Specialist (L2)** role at PayJoy.

## Description

A currency conversion API that converts USD installment amounts into local currencies, integrated with a chatbot to automate a common customer question. Includes automatic failover between two exchange-rate providers for reliability.

**Customer scenario:** _"I bought my phone for $200 USD. How much is my monthly installment in my local currency?"_

## Components

1. **REST API (FastAPI + Python):** converts USD amounts to local currencies using ExchangeRate-API as the primary provider and FastForex as an automatic fallback.
2. **Chatbot (Landbot):** conversational flow that consumes the API.
3. **Deployment (Render):** public HTTPS URL for the chatbot.

## How to Run Locally

### Requirements

- Python 3.11+
- Git
- API keys from [ExchangeRate-API](https://www.exchangerate-api.com) and [FastForex](https://fastforex.io) (both offer free tiers)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/expcamilo-cpu/payjoy-currency-converter.git
   cd payjoy-currency-converter
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root with both API keys:
   ```
   EXCHANGE_RATE_API_KEY="your_exchangerate_api_key"
   FASTFOREX_API_KEY="your_fastforex_api_key"
   ```

5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

6. Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Endpoints

### `GET /convert`

Converts a USD amount to a target currency.

**Query parameters:**
- `amount` (float, > 0): amount in USD
- `currency` (string, 3 letters): ISO 4217 currency code

**Example:**
```bash
curl "http://127.0.0.1:8000/convert?amount=200&currency=BRL"
```

**Response:**
```json
{
  "amount_usd": 200.0,
  "currency": "BRL",
  "converted": 1045.62,
  "rate": 5.2281,
  "provider": "exchangerate-api"
}
```

The `provider` field indicates which provider served the conversion. It will show `"exchangerate-api"` when the primary succeeds, or `"fastforex (fallback)"` when the automatic failover is triggered.

### `GET /health`

Returns the API health status.

**Example:**
```bash
curl "http://127.0.0.1:8000/health"
```

**Response:**
```json
{"status": "ok"}
```

## API Key Configuration

The API keys are **never hardcoded**. They are loaded from environment variables (`EXCHANGE_RATE_API_KEY`, `FASTFOREX_API_KEY`) via a `.env` file in local development, and configured as environment variables in production (Render).

The `.env` file is excluded from version control via `.gitignore`. A `.env.example` file is included as a template for other developers.

## Technical Decisions

- **Python + FastAPI:** modern, high-performance framework with automatic validation and Swagger UI generation.
- **Strict ISO 4217 validation:** uses the `iso4217` library to guarantee valid currency codes (e.g., `PHP` for Philippine peso, not `PHL`).
- **Clear error handling:** HTTP 400 for validation errors, 502 for external provider failures, 504 for timeouts.
- **Automatic failover between providers:** if ExchangeRate-API fails (timeout, error, invalid account), the API automatically retries with FastForex. The response includes a `provider` field for observability.
- **Fail-fast on startup:** the app refuses to start if either API key is missing, avoiding silent misconfigurations.

## Project Structure

```
payjoy-currency-converter/
├── .env.example          # Template for environment variables
├── .gitignore            # Excludes .env, .venv, etc.
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## What I Would Improve with More Time

- Unit and integration tests with `pytest`.
- Caching exchange rates (Redis) to reduce external API calls.
- API authentication (own API key) to protect the endpoint from abuse.
- Structured logging and monitoring (Sentry, CloudWatch).
- CI/CD pipeline with GitHub Actions.
- Add an alert when fallback rate exceeds a threshold (e.g., > 5% of requests).
- Circuit breaker pattern to avoid hammering a provider that is down.

## Success Metrics in Production

- **Bot Handle Rate (BHR):** % of conversions resolved by the bot without escalating to an agent.
- **API error rate:** < 1% of requests.
- **Fallback rate:** % of requests served by the fallback provider. If it rises above ~5%, it indicates the primary provider is degraded.
- **Average latency:** < 500 ms.
- **Customer Satisfaction (CSAT/BSAT):** feedback collected at the end of the flow.

## AI Tools Disclosure
