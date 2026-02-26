from matplotlib.axes import Axes
from matplotlib.figure import Figure
import pandas as pd


class Plotter:
    def get_plot_config(self, category: str, symbol: str) -> tuple[str, str, str]:
        if category == "crypto":
            return "price", f"{symbol} Daily Price", "Preis"
        if category == "forex":
            return "close", f"{symbol} Daily Close", "Kurs"
        return "close", f"{symbol} Close Price", "Preis"

    def plot_dataframe(
        self,
        axis: Axes,
        figure: Figure,
        dataframe: pd.DataFrame,
        value_column: str,
        title: str,
        y_label: str,
    ) -> None:
        if dataframe.empty or value_column not in dataframe.columns:
            raise ValueError("Keine passenden Daten zum Plotten erhalten.")

        axis.clear()
        axis.set_axis_on()
        axis.plot(dataframe.index, dataframe[value_column])
        axis.set_title(title)
        axis.set_xlabel("Datum")
        axis.set_ylabel(y_label)
        axis.grid(True, alpha=0.3)
        figure.autofmt_xdate()

    def plot_error(self, axis: Axes, error: Exception) -> None:
        axis.clear()
        axis.text(0.5, 0.5, f"Fehler beim Laden:\n{error}", ha="center", va="center")
        axis.set_axis_off()
