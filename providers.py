import logging
from decimal import Decimal

import requests

from config import settings

logger = logging.getLogger("payjoy.currency.providers")


class ProviderError(Exception):
    """Raised when an external exchange-rate provider fails (network, timeout, 5xx, invalid key)."""


class UnsupportedCurrencyError(Exception):
    """Raised when a valid ISO 4217 code is not supported by the provider."""


def fetch_rate_from_exchangerate(target: str) -> Decimal:
    """Primary provider: ExchangeRate-API v6."""
    url = f"https://v6.exchangerate-api.com/v6/{settings.exchange_rate_api_key}/latest/USD"
    try:
        response = requests.get(url, timeout=settings.primary_timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log only the exception type; never the URL (which contains the API key).
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


def fetch_rate_from_fastforex(target: str) -> Decimal:
    """Fallback provider: FastForex."""
    if not settings.fastforex_api_key:
        raise ProviderError("fastforex not configured")

    url = "https://api.fastforex.io/fetch-one"
    headers = {"X-API-Key": settings.fastforex_api_key}
    params = {"from": "USD", "to": target}
    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=settings.fallback_timeout
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("fastforex request failed: %s", type(exc).__name__)
        raise ProviderError("fastforex unavailable") from exc

    data = response.json()
    result = data.get("result", {})
    if target not in result:
        raise UnsupportedCurrencyError(f"Currency {target} not supported by fastforex")

    return Decimal(str(result[target]))


def get_rate(target: str) -> tuple[Decimal, str, bool]:
    """
    Fetch the exchange rate for `target` using a primary -> fallback strategy.

    Returns:
        (rate, provider_name, fallback_used)

    Raises:
        UnsupportedCurrencyError: if every enabled provider rejected the currency.
        ProviderError: if all providers failed for infra reasons.
    """
    primary_error: Exception | None = None
    fallback_error: Exception | None = None

    # 1. Primary
    try:
        rate = fetch_rate_from_exchangerate(target)
        return rate, "exchangerate-api", False
    except (ProviderError, UnsupportedCurrencyError) as exc:
        primary_error = exc
        logger.info("Primary provider rejected request: %s", type(exc).__name__)

    # 2. Fallback (only if configured)
    if settings.fastforex_api_key:
        try:
            rate = fetch_rate_from_fastforex(target)
            return rate, "fastforex", True
        except (ProviderError, UnsupportedCurrencyError) as exc:
            fallback_error = exc
            logger.warning("Fallback provider rejected request: %s", type(exc).__name__)
    else:
        logger.info("Fallback provider not configured; skipping.")

    # 3. Classify final error
    errors = [e for e in (primary_error, fallback_error) if e is not None]
    if errors and all(isinstance(e, UnsupportedCurrencyError) for e in errors):
        raise UnsupportedCurrencyError(f"Currency {target} not supported by any enabled provider")

    raise ProviderError("All enabled providers failed")