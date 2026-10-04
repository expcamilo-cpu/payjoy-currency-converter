import logging
import os
import requests
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from iso4217 import Currency

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payjoy.currency")


class ProviderError(Exception):
    """Raised when an external exchange-rate provider fails (network, timeout, 5xx, invalid key)."""


class UnsupportedCurrencyError(Exception):
    """Raised when a valid ISO 4217 code is not supported by the provider."""


EXCHANGERATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
FASTFOREX_API_KEY = os.getenv("FASTFOREX_API_KEY")

if not EXCHANGERATE_API_KEY:
    raise ValueError("Missing EXCHANGE_RATE_API_KEY in the .env file")
if not FASTFOREX_API_KEY:
    raise ValueError("Missing FASTFOREX_API_KEY in the .env file")


app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies with automatic failover between providers.",
    version="1.2.0",
)


def _fetch_rate_from_exchangerate(target: str) -> Decimal:
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log only the exception type, never the URL (it contains the API key).
        logger.warning("exchangerate-api request failed: %s", type(exc).__name__)
        raise ProviderError("exchangerate-api unavailable") from exc

    data = response.json()
    if data.get("result") != "success":
        logger.warning("exchangerate-api returned non-success result: %s", data.get("error-type"))
        raise ProviderError("exchangerate-api returned an error")

    rates = data.get("conversion_rates", {})
    if target not in rates:
        raise UnsupportedCurrencyError(f"Currency {target} not supported by exchangerate-api")

    return Decimal(str(rates[target]))


def _fetch_rate_from_fastforex(target: str) -> Decimal:
    url = "https://api.fastforex.io/fetch-one"
    headers = {"X-API-Key": FASTFOREX_API_KEY}
    params = {"from": "USD", "to": target}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("fastforex request failed: %s", type(exc).__name__)
        raise ProviderError("fastforex unavailable") from exc

    data = response.json()
    result = data.get("result", {})
    if target not in result:
        raise UnsupportedCurrencyError(f"Currency {target} not supported by fastforex")

    return Decimal(str(result[target]))


@app.get("/convert")
def convert_currency(  # NOT async: uses blocking requests; FastAPI runs it in a threadpool.
    amount: Decimal = Query(..., gt=0, description="Amount in USD. Must be > 0."),
    currency: str = Query(..., min_length=3, max_length=3, description="ISO 4217 currency code."),
):
    # 1. Validate ISO 4217 code (input validation -> 400)
    try:
        Currency(currency.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid currency code: '{currency}'. Please use a valid ISO 4217 code.",
        )

    target = currency.upper()
    rate: Decimal | None = None
    provider: str | None = None
    fallback_used = False
    primary_error: Exception | None = None
    fallback_error: Exception | None = None

    # 2. Try primary provider
    try:
        rate = _fetch_rate_from_exchangerate(target)
        provider = "exchangerate-api"
    except (ProviderError, UnsupportedCurrencyError) as exc:
        primary_error = exc
        logger.info("Primary provider rejected request: %s", type(exc).__name__)

    # 3. Try fallback provider
    if rate is None:
        try:
            rate = _fetch_rate_from_fastforex(target)
            provider = "fastforex"
            fallback_used = True
        except (ProviderError, UnsupportedCurrencyError) as exc:
            fallback_error = exc
            logger.warning("Fallback provider rejected request: %s", type(exc).__name__)

    # 4. Classify final error if no provider succeeded
    if rate is None:
        both_unsupported = isinstance(primary_error, UnsupportedCurrencyError) and isinstance(
            fallback_error, UnsupportedCurrencyError
        )
        if both_unsupported:
            raise HTTPException(
                status_code=422,
                detail=f"Currency {target} is valid ISO 4217 but is not supported by any provider.",
            )
        raise HTTPException(
            status_code=502,
            detail="Exchange rate providers are currently unavailable.",
        )

    converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "amount_usd": float(amount),
        "currency": target,
        "converted": float(converted),
        "rate": float(rate),
        "provider": provider,
        "fallback_used": fallback_used,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}