"""
ui/canvas.py
Widget de PyQt5 que embebe una figura matplotlib.
"""

from __future__ import annotations

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy


class MplCanvas(FigureCanvas):
    """Canvas embebible en cualquier layout de Qt."""

    def __init__(self, figure: Figure) -> None:
        super().__init__(figure)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def replace_figure(self, figure: Figure) -> None:
        """Reemplaza la figura actual y redibuja."""
        self.figure = figure
        self.draw()
