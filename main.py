from gui import GUI


if __name__ == "__main__":
    api_key = input("Bitte AlphaVantage API-Key eingeben: ").strip() # Keine Ahnung wie Dirk das später am besten macht
    if not api_key:
        raise ValueError("Es wurde kein API-Key eingegeben.") # Später bessere Kontrolle einbauen, z.B. Format oder Länge prüfen

    app = GUI(api_key)
    app.run()