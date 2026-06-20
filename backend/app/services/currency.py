from decimal import Decimal

import httpx

from app.config import get_settings

# Fallback rates if API unavailable
FALLBACK_RATES = {
    "RUB": Decimal("98.50"),
    "USD": Decimal("1.08"),
    "GBP": Decimal("0.85"),
    "EUR": Decimal("1.00"),
}


class CurrencyService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._rates: dict[str, Decimal] = dict(FALLBACK_RATES)

    async def refresh_rates(self) -> dict[str, Decimal]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.settings.exchange_rate_api,
                    params={"from": "EUR", "to": "RUB,USD,GBP"},
                )
                response.raise_for_status()
                data = response.json()
                for currency, rate in data.get("rates", {}).items():
                    self._rates[currency] = Decimal(str(rate))
        except Exception:
            pass
        self._rates["EUR"] = Decimal("1.00")
        return self._rates

    def get_rate(self, currency: str) -> Decimal:
        return self._rates.get(currency.upper(), Decimal("1.00"))

    def to_eur(self, amount: Decimal, currency: str) -> Decimal:
        currency = currency.upper()
        if currency == "EUR":
            return amount.quantize(Decimal("0.01"))
        rate = self.get_rate(currency)
        if currency == "RUB":
            return (amount / rate).quantize(Decimal("0.01"))
        return (amount / rate).quantize(Decimal("0.01"))

    def to_rub(self, amount_eur: Decimal) -> Decimal:
        rate = self.get_rate("RUB")
        return (amount_eur * rate).quantize(Decimal("0.01"))

    def convert(self, amount: Decimal, from_currency: str) -> tuple[Decimal, Decimal]:
        eur = self.to_eur(amount, from_currency)
        rub = self.to_rub(eur)
        return eur, rub


currency_service = CurrencyService()
