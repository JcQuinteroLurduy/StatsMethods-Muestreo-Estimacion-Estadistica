"""
ui/table_widget.py
Tabla estilizada reutilizable basada en QTableWidget.
"""

from __future__ import annotations

import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


HEADER_BG   = "#1e353b"
HEADER_FG   = "#EDE9FE"
ROW_ALT     = "#EDE9FE"
ROW_NORMAL  = "#94A3B8"
BORDER      = "#1E293B"
FONT_DATA   = QFont("Consolas", 9)
FONT_HEADER = QFont("Segoe UI", 9, QFont.Bold)


class StyledTable(QTableWidget):
    """QTableWidget con estilos aplicados por defecto."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self) -> None:
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {BORDER};
                border-radius: 6px;
                background: {ROW_NORMAL};
                alternate-background-color: {ROW_ALT};
                font-family: Consolas, monospace;
                font-size: 9pt;
                color: #1E293B;
                gridline-color: {BORDER};
            }}
            QHeaderView::section {{
                background-color: {HEADER_BG};
                color: {HEADER_FG};
                padding: 6px 10px;
                font-weight: bold;
                font-size: 9pt;
                border: none;
                border-right: 1px solid #334155;
            }}
            QTableWidget::item:selected {{
                background-color: #DBEAFE;
                color: #1E293B;
            }}
        """)

    def load_dataframe(self, df: pd.DataFrame, max_rows: int = 500) -> None:
        """Carga un DataFrame completo en la tabla."""
        df_show = df.head(max_rows)
        self.clear()
        self.setRowCount(len(df_show))
        self.setColumnCount(len(df_show.columns))
        self.setHorizontalHeaderLabels([str(c) for c in df_show.columns])

        for i, row in df_show.iterrows():
            for j, val in enumerate(row):
                display = f"{val:.4f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(df_show.index.get_loc(i), j, item)  # type: ignore

    def load_dict_rows(self, headers: list[str], rows: list[list]) -> None:
        """Carga filas de datos arbitrarios."""
        self.clear()
        self.setRowCount(len(rows))
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                display = f"{val:.4f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(r_idx, c_idx, item)
