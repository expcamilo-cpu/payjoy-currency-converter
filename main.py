from fastapi import FastAPI

app = FastAPI(
    title="PayJoy Currency Converter API",
    description="Converts USD amounts to local currencies for the PayJoy chatbot.",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}