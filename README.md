# PayJoy – Currency Converter

Technical assessment for the **Automation Engineer – Tools Specialist (L2)** role at PayJoy.

## Description

A currency conversion API that converts USD installment amounts into local currencies, integrated with a chatbot to automate a common customer question.

**Customer scenario:** _"I bought my phone for $200 USD. How much is my monthly installment in my local currency?"_

## Components

1. **REST API (FastAPI + Python):** converts USD amounts to local currencies using ExchangeRate-API.
2. **Chatbot (Landbot):** conversational flow that consumes the API.
3. **Deployment (Render):** public HTTPS URL for the chatbot.

## How to Run Locally

### Requirements

- Python 3.11+
- Git
- An API key from [ExchangeRate-API](https://www.exchangerate-api.com) (free tier available)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/expcamilo-cpu/payjoy-currency-converter.git
   cd payjoy-currency-converter
Create and activate a virtual environment:

bash
python3.11 -m venv .venv
source .venv/bin/activate
Install dependencies:

bash
pip install -r requirements.txt
Create a .env file in the root with your API key:

text
EXCHANGE_RATE_API_KEY="your_api_key_here"
Run the server:

bash
uvicorn main:app --reload
Open http://127.0.0.1:8000/docs for the interactive API documentation.

Endpoints
GET /convert
Converts a USD amount to a target currency.

Query parameters:

amount (float, > 0): amount in USD

currency (string, 3 letters): ISO 4217 currency code

Example:

bash
curl "http://127.0.0.1:8000/convert?amount=200&currency=BRL"
Response:

json
{
  "amount_usd": 200.0,
  "currency": "BRL",
  "converted": 1045.62,
  "rate": 5.2281
}
GET /health
Returns the API health status.

API Key Configuration
The API key is never hardcoded. It is loaded from an environment variable (EXCHANGE_RATE_API_KEY) via a .env file in local development, and configured as an environment variable in production (Render).

Technical Decisions
Python + FastAPI: modern, high-performance framework with automatic validation and Swagger UI generation.

Strict ISO 4217 validation: uses the iso4217 library to guarantee valid currency codes (e.g., PHP for Philippine peso, not PHL).

Clear error handling: HTTP 400 for validation errors, 502 for external provider failures, 504 for timeouts.

Fail-fast on startup: the app refuses to start if the API key is missing, avoiding silent misconfigurations.

What I Would Improve with More Time
Unit and integration tests with pytest.

Caching exchange rates (Redis) to reduce external API calls.

API authentication (own API key) to protect the endpoint from abuse.

Structured logging and monitoring (Sentry, CloudWatch).

CI/CD pipeline with GitHub Actions.

Success Metrics in Production
Bot Handle Rate (BHR): % of conversions resolved by the bot without escalating to an agent.

API error rate: < 1% of requests.

Average latency: < 500 ms.

Customer Satisfaction (CSAT/BSAT): feedback collected at the end of the flow.

AI Tools Disclosure
