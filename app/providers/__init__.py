import logging
from decimal import Decimal

from app.config import settings
from app.exceptions import ProviderError, UnsupportedCurrencyError
from app.providers import exchangerate, fastforex

logger = logging.getLogger("payjoy.currency.providers")


def get_rate(target: str) -> tuple[Decimal, str, bool]:
    """
    Fetch the exchange rate for `target` using a primary -> fallback strategy.

    Returns:
        (rate, provider_name, fallback_used)
    """
    primary_error: Exception | None = None
    fallback_error: Exception | None = None

    try:
        rate = exchangerate.fetch_rate_from_exchangerate(target)
        return rate, "exchangerate-api", False
    except (ProviderError, UnsupportedCurrencyError) as exc:
        primary_error = exc
        logger.info("Primary provider rejected request: %s", type(exc).__name__)

    if settings.fastforex_api_key:
        try:
            rate = fastforex.fetch_rate_from_fastforex(target)
            return rate, "fastforex", True
        except (ProviderError, UnsupportedCurrencyError) as exc:
            fallback_error = exc
            logger.warning("Fallback provider rejected request: %s", type(exc).__name__)
    else:
        logger.info("Fallback provider not configured; skipping.")

    errors = [e for e in (primary_error, fallback_error) if e is not None]
    if errors and all(isinstance(e, UnsupportedCurrencyError) for e in errors):
        raise UnsupportedCurrencyError(f"Currency {target} not supported by any enabled provider")

    raise ProviderError("All enabled providers failed")