import logging
from decimal import Decimal

import requests

from app.config import settings
from app.exceptions import ProviderError, UnsupportedCurrencyError

logger = logging.getLogger("payjoy.currency.providers.fastforex")


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