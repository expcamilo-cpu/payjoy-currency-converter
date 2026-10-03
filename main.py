import os
import requests
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from iso4217 import Currency

load_dotenv()

EXCHANGERATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
FASTFOREX_API_KEY = os.getenv("FASTFOREX_API_KEY")

if not EXCHANGERATE_API_KEY:
    raise ValueError("Missing EXCHANGE_RATE_API_KEY in the .env file")
if not FASTFOREX_API_KEY:
    raise ValueError("Missing FASTFOREX_API_KEY in the .env file")

app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies with automatic failover between providers.",
    version="1.1.0",
)


def get_rate_from_exchangerate(target: str) -> float:
    """Primary provider: ExchangeRate-API v6."""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise ValueError("ExchangeRate-API returned an error.")

    rates = data.get("conversion_rates", {})
    if target not in rates:
        raise ValueError(f"Currency {target} not supported by ExchangeRate-API.")

    return rates[target]


def get_rate_from_fastforex(target: str) -> float:
    """Fallback provider: FastForex."""
    url = "https://api.fastforex.io/fetch-one"
    headers = {"X-API-Key": FASTFOREX_API_KEY}
    params = {"from": "USD", "to": target}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    result = data.get("result", {})
    if target not in result:
        raise ValueError(f"Currency {target} not supported by FastForex.")

    return result[target]


@app.get("/convert")
async def convert_currency(
    amount: float = Query(..., gt=0, description="Amount in USD to convert. Must be > 0."),
    currency: str = Query(..., min_length=3, max_length=3, description="Target ISO 4217 currency code (e.g., BRL, MXN, PHP).")
):
    # Validate ISO 4217 code
    try:
        Currency(currency.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid currency code: '{currency}'. Please use a valid ISO 4217 code (e.g., BRL, MXN, PHP)."
        )

    target = currency.upper()
    rate = None
    provider = None
    errors = []

    # Try primary provider
    try:
        rate = get_rate_from_exchangerate(target)
        provider = "exchangerate-api"
    except (requests.RequestException, ValueError) as e:
        errors.append(f"exchangerate-api: {e}")

    # If primary fails, try fallback
    if rate is None:
        try:
            rate = get_rate_from_fastforex(target)
            provider = "fastforex (fallback)"
        except (requests.RequestException, ValueError) as e:
            errors.append(f"fastforex: {e}")

    # If both fail, return 502
    if rate is None:
        raise HTTPException(
            status_code=502,
            detail=f"All exchange rate providers failed: {'; '.join(errors)}"
        )

    converted = round(amount * rate, 2)

    return {
        "amount_usd": amount,
        "currency": target,
        "converted": converted,
        "rate": rate,
        "provider": provider,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}