import logging
from decimal import ROUND_HALF_UP, Decimal

from fastapi import FastAPI, HTTPException, Query
from iso4217 import Currency

from config import settings
from providers import ProviderError, UnsupportedCurrencyError, get_rate
from schemas import ConversionResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payjoy.currency")

app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies with automatic failover between providers.",
    version="1.2.0",
)


@app.get("/convert", response_model=ConversionResponse)
def convert_currency(
    amount: Decimal = Query(..., gt=0, description="Amount in USD. Must be > 0."),
    currency: str = Query(..., min_length=3, max_length=3, description="ISO 4217 currency code."),
) -> ConversionResponse:
    # 1. Validate ISO 4217 code
    try:
        Currency(currency.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid currency code: '{currency}'. Please use a valid ISO 4217 code.",
        )

    target = currency.upper()

    # 2. Fetch rate (primary -> fallback)
    try:
        rate, provider, fallback_used = get_rate(target)
    except UnsupportedCurrencyError:
        raise HTTPException(
            status_code=422,
            detail=f"Currency {target} is valid ISO 4217 but is not supported by any enabled provider.",
        )
    except ProviderError:
        raise HTTPException(
            status_code=502,
            detail="Exchange rate providers are currently unavailable.",
        )

    # 3. Compute converted amount with explicit rounding
    converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return ConversionResponse(
        amount_usd=float(amount),
        currency=target,
        converted=float(converted),
        rate=float(rate),
        provider=provider,
        fallback_used=fallback_used,
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "fallback_configured": settings.fastforex_api_key is not None,
    }