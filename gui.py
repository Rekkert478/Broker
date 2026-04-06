import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from fetch import Fetch
from plotter import Plotter


class GUI:
    def __init__(self, api_key: str) -> None:
        self.fetch = Fetch(api_key)
        self.plotter = Plotter()

        self.root = tk.Tk()
        self.root.title("Broker App für Dirk")
        self.root.geometry("1200x750")

        self.selected_category = tk.StringVar(value="stocks")
        self.symbol_query = tk.StringVar()
        self.status_text = tk.StringVar(value="")

        self._build_layout()
        self._load_symbols_for_category()
        self._plot_selected_symbol()

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(self.root, padding=10)
        left_panel.grid(row=0, column=0, sticky="ns")

        chart_panel = ttk.Frame(self.root, padding=(0, 10, 10, 10))
        chart_panel.grid(row=0, column=1, sticky="nsew")
        chart_panel.columnconfigure(0, weight=1)
        chart_panel.rowconfigure(0, weight=1)

        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill="x", pady=(0, 10))

        for label, value in [("Stocks", "stocks"), ("Crypto", "crypto"), ("Forex", "forex")]:
            button = ttk.Radiobutton(
                filter_frame,
                text=label,
                value=value,
                variable=self.selected_category,
                command=self._on_category_change,
            )
            button.pack(fill="x", pady=2)

        import_frame = ttk.LabelFrame(left_panel, text="Symbole per Query importieren", padding=8)
        import_frame.pack(fill="x", pady=(0, 10))

        query_entry = ttk.Entry(import_frame, textvariable=self.symbol_query)
        query_entry.pack(fill="x")
        query_entry.bind("<Return>", self._on_import_query)

        ttk.Label(import_frame, text="Beispiel: apple, tesla, eurusd").pack(anchor="w", pady=(4, 6))

        ttk.Button(import_frame, text="Importieren", command=self._import_symbols_from_query).pack(fill="x")
        ttk.Label(import_frame, textvariable=self.status_text, wraplength=260).pack(anchor="w", pady=(6, 0))

        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill="both", expand=True)

        self.symbol_listbox = tk.Listbox(list_frame, exportselection=False, height=25)
        self.symbol_listbox.pack(side="left", fill="both", expand=True)
        self.symbol_listbox.bind("<<ListboxSelect>>", self._on_symbol_selected)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.symbol_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.symbol_listbox.configure(yscrollcommand=scrollbar.set)

        self.figure = Figure(figsize=(9, 6), dpi=100)
        self.axis = self.figure.add_subplot(111)
        self.axis.set_title("Bitte links ein Symbol auswählen")
        self.axis.set_xlabel("Datum")
        self.axis.set_ylabel("Wert")

        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_panel)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _on_category_change(self) -> None:
        self._load_symbols_for_category()
        self._plot_selected_symbol()

    def _load_symbols_for_category(self) -> None:
        category = self.selected_category.get()
        symbols = self.fetch.get_symbols(category)

        self.symbol_listbox.delete(0, tk.END)
        for symbol in symbols:
            self.symbol_listbox.insert(tk.END, symbol)

        if symbols:
            self.symbol_listbox.selection_clear(0, tk.END)
            self.symbol_listbox.selection_set(0)
            self.symbol_listbox.activate(0)

    def _on_symbol_selected(self, _event: object) -> None:
        self._plot_selected_symbol()

    def _on_import_query(self, _event: object) -> None:
        self._import_symbols_from_query()

    def _import_symbols_from_query(self) -> None:
        query = self.symbol_query.get().strip()
        if not query:
            self.status_text.set("Bitte Suchbegriff eingeben.")
            return

        category = self.selected_category.get()

        try:
            added, last_added = self.fetch.import_symbols_from_query(category, query)
            symbols = self.fetch.get_symbols(category)

            self._load_symbols_for_category()
            if last_added:
                index = symbols.index(last_added)
                self.symbol_listbox.selection_clear(0, tk.END)
                self.symbol_listbox.selection_set(index)
                self.symbol_listbox.activate(index)
                self._plot_selected_symbol()

            if added:
                self.status_text.set(f"{added} Symbol(e) importiert.")
            else:
                self.status_text.set("Keine neuen passenden Symbole gefunden.")
        except Exception as error:
            self.status_text.set(f"Import fehlgeschlagen: {error}")

    def _get_selected_symbol(self) -> str | None:
        selected = self.symbol_listbox.curselection()
        if not selected:
            return None
        return self.symbol_listbox.get(selected[0])

    def _plot_selected_symbol(self) -> None:
        category = self.selected_category.get()
        symbol = self._get_selected_symbol()
        if not symbol:
            return

        try:
            if category == "stocks":
                df = self.fetch.fetch_stocks(symbol)
            elif category == "crypto":
                df = self.fetch.fetch_crypto(symbol)
            else:
                from_symbol, to_symbol = symbol.split("/")
                df = self.fetch.fetch_forex(from_symbol, to_symbol)

            value_col, title, ylabel = self.plotter.get_plot_config(category, symbol)
            self.plotter.plot_dataframe(self.axis, self.figure, df, value_col, title, ylabel)
        except Exception as error:
            self.plotter.plot_error(self.axis, error)

        self.canvas.draw_idle()

    def run(self) -> None:
        self.root.mainloop()