import httpx

FRANKFURTER_URL = "https://api.frankfurter.app/latest"


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency == to_currency:
        return {"amount": amount, "from_currency": from_currency, "to_currency": to_currency, "converted_amount": amount, "rate": 1.0}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(FRANKFURTER_URL, params={"amount": amount, "from": from_currency, "to": to_currency})
        if resp.status_code >= 400:
            return {"error": f"Frankfurter error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    converted = data["rates"].get(to_currency)
    if converted is None:
        return {"error": f"No rate available for {to_currency}"}

    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": round(converted, 2),
        "rate": round(converted / amount, 4) if amount else None,
        "date": data.get("date"),
    }
