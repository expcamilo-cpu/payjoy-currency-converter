import requests
from fastapi import FastAPI, Query

app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies for the PayJoy chatbot.",
    version="0.2.0",
)

# TODO: move this to an environment variable in a later commit
API_KEY = "your_api_key_here"
EXCHANGE_API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"


@app.get("/convert")
async def convert_currency(
    amount: float = Query(..., gt=0, description="Amount in USD to convert. Must be > 0."),
    currency: str = Query(..., min_length=3, max_length=3, description="Target ISO 4217 currency code (e.g., BRL, MXN, PHP).")
):
    response = requests.get(EXCHANGE_API_URL, timeout=10)
    data = response.json()

    rates = data.get("conversion_rates", {})
    target = currency.upper()
    rate = rates[target]
    converted = round(amount * rate, 2)

    return {
        "amount_usd": amount,
        "currency": target,
        "converted": converted,
        "rate": rate,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}