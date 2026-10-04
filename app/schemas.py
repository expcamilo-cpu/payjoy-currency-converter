from pydantic import BaseModel, Field


class ConversionResponse(BaseModel):
    """Response body for the /convert endpoint."""

    amount_usd: float = Field(..., description="Original amount in USD.")
    currency: str = Field(..., description="Target ISO 4217 currency code.")
    converted: float = Field(..., description="Converted amount in the target currency.")
    rate: float = Field(..., description="Exchange rate used (1 USD = rate <currency>).")
    provider: str = Field(..., description="Provider that served the conversion.")
    fallback_used: bool = Field(..., description="True if the fallback provider was used.")