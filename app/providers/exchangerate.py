import logging
from decimal import Decimal

import requests

from app.config import settings
from app.exceptions import ProviderError, UnsupportedCurrencyError

logger = logging.getLogger("payjoy.currency.providers.exchangerate")


def fetch_rate_from_exchangerate(target: str) -> Decimal:
    """Primary provider: ExchangeRate-API v6."""
    url = f"https://v6.exchangerate-api.com/v6/{settings.exchange_rate_api_key}/latest/USD"
    try:
        response = requests.get(url, timeout=settings.primary_timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("exchangerate-api request failed: %s", type(exc).__name__)
        raise ProviderError("exchangerate-api unavailable") from exc

    data = response.json()
    if data.get("result") != "success":
        logger.warning("exchangerate-api non-success: %s", data.get("error-type"))
        raise ProviderError("exchangerate-api returned an error")

    rates = data.get("conversion_rates", {})
    if target not in rates:
        raise UnsupportedCurrencyError(f"Currency {target} not supported by exchangerate-api")

    return Decimal(str(rates[target]))