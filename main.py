import requests
from fastapi import FastAPI, HTTPException, Query
from iso4217 import Currency

app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies for the PayJoy chatbot.",
    version="0.4.0",
)

# TODO: move this to an environment variable in a later commit
API_KEY = "REDACTED_EXCHANGERATE_KEY"
EXCHANGE_API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"


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

    # Call the external exchange rate API
    try:
        response = requests.get(EXCHANGE_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") != "success":
            raise HTTPException(status_code=502, detail="The exchange rate API returned an error.")

        rates = data.get("conversion_rates", {})
        target = currency.upper()

        if target not in rates:
            raise HTTPException(status_code=400, detail=f"Currency not supported by the API: {target}")

        rate = rates[target]
        converted = round(amount * rate, 2)

        return {
            "amount_usd": amount,
            "currency": target,
            "converted": converted,
            "rate": rate,
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to the exchange rate API timed out.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error connecting to the exchange rate API: {e}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}