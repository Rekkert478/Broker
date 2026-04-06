import requests
import pandas as pd
import matplotlib.pyplot as plt
import re

from symbol_store import SymbolStore


class Fetch:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.symbol_store = SymbolStore()

    def get_symbols(self, category: str) -> list[str]:
        return self.symbol_store.get_symbols(category)
    
    def _request(self, params: dict) -> dict:
        request_params = {**params, "apikey": self.api_key}
        response = requests.get(self.BASE_URL, params=request_params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if data.get("Error Message"):
            raise ValueError(f"AlphaVantage Error: {data['Error Message']}")
        if data.get("Note"):
            raise RuntimeError(f"AlphaVantage Limit/Note: {data['Note']}")

        return data

    # Methode zum Suchen von Symbolen basierend auf einem Suchbegriff, die von GUI 
    # aufgerufen wird
    # Sie nutzt die AlphaVantage Funktion "SYMBOL_SEARCH", um passende Symbole zu finden, 
    # und filtert die Ergebnisse
    def search_symbols(self, keywords: str) -> list[dict]:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
        }
        data = self._request(params)
        matches = data.get("bestMatches")
        if not matches:
            return []
        return matches

    def import_symbols_from_query(self, category: str, query: str) -> tuple[int, str | None]:
        terms = [term for term in re.split(r"[,;]+", query) if term.strip()]
        matches: list[dict] = []
        for term in terms:
            matches.extend(self.search_symbols(term.strip()))

        return self.symbol_store.import_from_matches(category, matches)

    @staticmethod
    def _to_ohlc_dataframe(time_series: dict) -> pd.DataFrame:
        rows = []
        for date_str, values in time_series.items():
            rows.append(
                {
                    "date": date_str,
                    "open": values.get("1. open"),
                    "high": values.get("2. high"),
                    "low": values.get("3. low"),
                    "close": values.get("4. close"),
                    "volume": values.get("5. volume"),
                }
            )

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    @staticmethod
    def _to_price_dataframe(time_series: dict) -> pd.DataFrame:
        rows = []
        for date_str, values in time_series.items():
            rows.append(
                {
                    "date": date_str,
                    "price": values.get("1a. open (USD)")
                    or values.get("4. close")
                    or values.get("1. open"),
                    "market_cap": values.get("6. market cap (USD)"),
                }
            )

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

        for col in ["price", "market_cap"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    # Methoden fürs fetchen der Daten, die von GUI aufgerufen werden
    def fetch_stocks(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
        }
        data = self._request(params)
        time_series = data.get("Time Series (Daily)")
        if not time_series:
            raise ValueError("Keine Aktien-Zeitreihe im Response gefunden.")
        return self._to_ohlc_dataframe(time_series)

    def fetch_crypto(self, symbol: str, market: str = "USD") -> pd.DataFrame:
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
        }
        data = self._request(params)
        time_series = data.get("Time Series (Digital Currency Daily)")
        if not time_series:
            raise ValueError("Keine Krypto-Zeitreihe im Response gefunden.")
        return self._to_price_dataframe(time_series)

    def fetch_forex(self, from_symbol: str, to_symbol: str = "USD") -> pd.DataFrame:
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": "compact",
        }
        data = self._request(params)
        time_series = data.get("Time Series FX (Daily)")
        if not time_series:
            raise ValueError("Keine Forex-Zeitreihe im Response gefunden.")
        return self._to_ohlc_dataframe(time_series)