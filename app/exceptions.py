class ProviderError(Exception):
    """Raised when an external exchange-rate provider fails (network, timeout, 5xx, invalid key)."""


class UnsupportedCurrencyError(Exception):
    """Raised when a valid ISO 4217 code is not supported by the provider."""