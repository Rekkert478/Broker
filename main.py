from gui import GUI
import tkinter as tk


def prompt_api_key() -> str:
    dialog = tk.Tk()
    dialog.title("API-Key eingeben")
    dialog.geometry("420x150")
    dialog.resizable(False, False)

    tk.Label(dialog, text="Bitte AlphaVantage API-Key eingeben:").pack(pady=(16, 6))

    key_var = tk.StringVar()
    key_entry = tk.Entry(dialog, textvariable=key_var, width=48, show="*")
    key_entry.pack(pady=4, padx=16)
    key_entry.focus_set() # setzt den Fokus auf das Eingabefeld, dass
                          # die Tatstatureingabe direkt möglich ist

    result: dict[str, str | None] = {"api_key": None}

    def on_confirm() -> None:
        api_key = key_var.get().strip()
        if api_key:
            result["api_key"] = api_key
            dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="OK", command=on_confirm, width=10).pack(side="left", padx=6)
    tk.Button(button_frame, text="Abbrechen", command=on_cancel, width=10).pack(side="left", padx=6)

    dialog.bind("<Return>", lambda _event: on_confirm()) # ermöglicht das Drücken der Enter-Taste als Bestätigung
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.mainloop()

    if not result["api_key"]:
        raise ValueError("Es wurde kein API-Key eingegeben.")

    return str(result["api_key"])


if __name__ == "__main__":
    api_key = prompt_api_key()
    app = GUI(api_key)
    app.run()