import json
from pathlib import Path


class SymbolStore:
    # Fallback-Werte, die genutzt werden, wenn keine gültige JSON-Datei vorhanden ist.
    DEFAULT_SYMBOLS = {
        "stocks": ["IBM", "AAPL", "MSFT"],
        "crypto": ["BTC", "ETH", "SOL"],
        "forex": ["EUR/USD", "GBP/USD", "USD/JPY"],
    }

    def __init__(self, symbols_file: Path | None = None) -> None:
        # Standardmäßig liegt symbols.json neben dieser Datei.
        self.symbols_file = symbols_file or Path(__file__).with_name("symbols.json")
        # Beim Start immer den gespeicherten Zustand laden (oder Defaults wiederherstellen).
        self.symbols = self._load_symbols()

    def _load_symbols(self) -> dict[str, list[str]]:
        # Kopie der Defaults erzeugen, damit die Originalkonstante unverändert bleibt.
        base = {category: list(values) for category, values in self.DEFAULT_SYMBOLS.items()}

        if not self.symbols_file.exists():
            # Erste Ausführung: Datei anlegen und mit Defaults starten.
            self._save_symbols(base)
            return base

        try:
            # Vorhandene JSON-Datei einlesen.
            raw = json.loads(self.symbols_file.read_text(encoding="utf-8"))
        except Exception:
            # Bei defekter Datei auf Defaults zurückfallen.
            self._save_symbols(base)
            return base

        if not isinstance(raw, dict):
            # Unerwartete Struktur ebenfalls mit Defaults heilen.
            self._save_symbols(base)
            return base

        # Defaults mit gültigen Werten aus der Datei zusammenführen.
        merged = {category: list(values) for category, values in base.items()}
        for category in ["stocks", "crypto", "forex"]:
            values = raw.get(category)
            if isinstance(values, list):
                # Einträge normalisieren: String, großgeschrieben, keine leeren Werte.
                merged[category] = [str(item).upper() for item in values if str(item).strip()]

        # Bereinigten Zustand zurück in die Datei schreiben.
        self._save_symbols(merged)
        return merged

    def _save_symbols(self, data: dict[str, list[str]] | None = None) -> None:
        # Ohne Übergabe den aktuellen In-Memory-Zustand speichern.
        payload = data if data is not None else self.symbols
        self.symbols_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_symbols(self, category: str) -> list[str]:
        # Kopie zurückgeben, damit Aufrufer den internen Zustand nicht direkt verändert.
        return list(self.symbols.get(category, []))

    @staticmethod
    def _normalize_symbol(category: str, raw_symbol: str) -> str | None:
        # Einheitliches Format: trimmen, upper-case, Leerzeichen entfernen.
        symbol = raw_symbol.strip().upper().replace(" ", "")
        if not symbol:
            return None

        if category == "forex":
            # Forex wird intern immer als XXX/YYY geführt.
            if "/" in symbol:
                left, right = symbol.split("/", 1)
                if len(left) == 3 and len(right) == 3:
                    return f"{left}/{right}"
                return None
            if len(symbol) == 6:
                return f"{symbol[:3]}/{symbol[3:]}"
            return None

        return symbol

    def _extract_symbol_from_match(self, category: str, match: dict) -> str | None:
        # AlphaVantage liefert das Symbol unter "1. symbol".
        symbol = (match.get("1. symbol") or "").strip()
        if not symbol:
            return None

        if category == "stocks":
            # Für Stocks nur Equity-Treffer akzeptieren.
            match_type = (match.get("3. type") or "").lower()
            if match_type and "equity" not in match_type:
                return None

        if category == "crypto":
            # Für Crypto nur passende Typen akzeptieren.
            match_type = (match.get("3. type") or "").lower()
            if match_type and "crypto" not in match_type and "digital" not in match_type:
                return None

        return self._normalize_symbol(category, symbol)

    def import_from_matches(self, category: str, matches: list[dict]) -> tuple[int, str | None]:
        # Kategorie-Liste anlegen, falls sie noch nicht existiert.
        bucket = self.symbols.setdefault(category, [])

        added = 0
        last_added: str | None = None
        for match in matches:
            symbol = self._extract_symbol_from_match(category, match)
            if not symbol:
                continue
            # Duplikate verhindern.
            if symbol not in bucket:
                bucket.append(symbol)
                last_added = symbol
                added += 1

        # Nur speichern, wenn sich wirklich etwas geändert hat.
        if added:
            self._save_symbols()

        return added, last_added
