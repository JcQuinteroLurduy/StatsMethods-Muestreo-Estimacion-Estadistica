"""
ui/main_window.py
Ventana principal de la aplicación.
Organiza 5 pestañas: Datos, Fase 1, Fase 2, Fases 3-4, Simulación.
"""

from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTabWidget, QGroupBox, QGridLayout,
    QScrollArea, QSplitter, QMessageBox, QStatusBar,
    QFrame, QSizePolicy, QProgressBar,
)

from services.statistics_service import StatisticsService
from ui.canvas import MplCanvas
from ui.table_widget import StyledTable
from utils.charts import (
    chart_means_comparison,
    chart_confidence_intervals,
    chart_simulation,
    chart_histogram,
)

# ─────────────────────────── Colores ────────────────────────────
ACCENT      = "#344765"
ACCENT_DARK = "#5a6371"
SUCCESS     = "#059669"
WARNING     = "#D97706"
DANGER      = "#DC2626"
BG_MAIN     = "#1E293B"
BG_PANEL    = "#313b4c"
BG_SIDEBAR  = "#313b4c"
TEXT_MAIN   = "#94A3B8"
TEXT_MUTED  = "#94A3B8"
BORDER      = "#1E293B"


# ─────────────────────────── Worker thread ──────────────────────
class WorkerThread(QThread):
    result  = pyqtSignal(object)
    error   = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self.result.emit(self._fn(*self._args, **self._kwargs))
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────── Utilidades UI ──────────────────────
def _label(text: str, bold=False, size=10, color=TEXT_MAIN) -> QLabel:
    lbl = QLabel(text)
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color};")
    return lbl


def _button(text: str, color=ACCENT, hover=ACCENT_DARK, text_color="#FFFFFF") -> QPushButton:
    btn = QPushButton(text)
    btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: {text_color};
            border: none;
            border-radius: 6px;
            padding: 8px 18px;
            min-height: 32px;
        }}
        QPushButton:hover   {{ background: {hover}; }}
        QPushButton:pressed {{ background: {hover}; opacity: 0.85; }}
        QPushButton:disabled {{ background: #94A3B8; color: #E2E8F0; }}
    """)
    return btn


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {BORDER};")
    return line


def _card(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    gb = QGroupBox(title)
    gb.setFont(QFont("Segoe UI", 10, QFont.Bold))
    gb.setStyleSheet(f"""
        QGroupBox {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 14px;
            padding: 10px;
            color: {TEXT_MAIN};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {ACCENT};
        }}
    """)
    lay = QVBoxLayout(gb)
    lay.setContentsMargins(10, 16, 10, 10)
    return gb, lay


# ──────────────────────────── Ventana ───────────────────────────
class MainWindow(QMainWindow):
    """Ventana principal de la aplicación de análisis estadístico."""

    APP_NAME = "StatsMethods"
    VERSION  = "jcql/1.0"

    def __init__(self) -> None:
        super().__init__()
        self.svc = StatisticsService()
        self._workers: list[WorkerThread] = []

        self.setWindowTitle(f"{self.APP_NAME} — Análisis de Muestreo y Estimación")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 700)
        self._apply_app_style()
        self._build_ui()
        self._init_status()

    # ─────────────────────── Estilos globales ──────────────────
    def _apply_app_style(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {BG_MAIN}; color: {TEXT_MAIN}; }}
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 0 8px 8px 8px;
                background: {BG_PANEL};
            }}
            QTabBar::tab {{
                background: #313b4c;
                color: {TEXT_MUTED};
                border-left: 1px solid #1E293B;
                padding: 15px 15px;
                font: bold 9pt 'Segoe UI';
                
            }}
            QTabBar::tab:selected {{
                background: {ACCENT};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{ background: #CBD5E1; }}
            QComboBox, QSpinBox, QDoubleSpinBox {{
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 5px 10px;
                background: white;
                color: {TEXT_MAIN};
                font: 9pt 'Segoe UI';
                min-height: 28px;
            }}
            QComboBox:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
            QScrollBar:vertical {{
                background: {BG_MAIN};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 30px;
            }}
        """)

    # ─────────────────────── UI principal ──────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_toolbar(), 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        root.addWidget(self.tabs, 1)

        self.tabs.addTab(self._tab_data(),       "📂  Datos")
        self.tabs.addTab(self._tab_phase1(),     "  Fase 1 — Población")
        self.tabs.addTab(self._tab_phase2(),     "  Fase 2 — Muestreo")
        self.tabs.addTab(self._tab_phase34(),    "  Fases 3 & 4 — Estimación")
        self.tabs.addTab(self._tab_simulation(), "  Simulación")

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(56)
        w.setStyleSheet(f"background: {BG_SIDEBAR};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(20, 0, 20, 0)

        title = _label(f"  {self.APP_NAME}", bold=True, size=14, color="#F1F5F9")
        sub   = _label(f"v{self.VERSION}  •  Muestreo & Estimación Estadística",
                       size=9, color="#94A3B8")
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addStretch()

        self.lbl_file = _label("Sin archivo cargado", size=9, color="#94A3B8")
        lay.addWidget(self.lbl_file)
        return w

    def _build_toolbar(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(70)
        w.setStyleSheet(f"background: #1E293B; border-bottom: 1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(10)

        self.btn_load = _button("📂  Cargar archivo", "#2563EB", "#1D4ED8")
        self.btn_load.clicked.connect(self._on_load_file)
        lay.addWidget(self.btn_load)
        lay.addWidget(_separator() if False else QFrame())  # spacer visual

        self.cmb_numeric = QComboBox(); self.cmb_numeric.setMinimumWidth(180)
        self.cmb_numeric.setPlaceholderText("Variable numérica…")
        self.cmb_cat = QComboBox();     self.cmb_cat.setMinimumWidth(180)
        self.cmb_cat.setPlaceholderText("Variable categórica (opcional)…")

        lay.addWidget(_label("Variable numérica:", size=9))
        lay.addWidget(self.cmb_numeric)
        lay.addWidget(_label("Variable categórica:", size=9))
        lay.addWidget(self.cmb_cat)

        self.btn_phase1 = _button("▶  Fase 1", SUCCESS, "#047857")
        self.btn_phase1.clicked.connect(self._run_phase1)
        lay.addWidget(self.btn_phase1)

        lay.addStretch()
        return w

    # ─────────────────────── Tab: Datos ────────────────────────
    def _tab_data(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)

        gb, inner = _card("Vista previa del dataset")
        self.tbl_data = StyledTable()
        inner.addWidget(self.tbl_data)
        lay.addWidget(gb, 1)

        info_row = QHBoxLayout()
        self.lbl_shape = _label("—", size=9, color=TEXT_MUTED)
        info_row.addWidget(self.lbl_shape)
        info_row.addStretch()
        lay.addLayout(info_row)
        return w

    # ─────────────────────── Tab: Fase 1 ───────────────────────
    def _tab_phase1(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # Métricas rápidas
        self.metrics_row = QHBoxLayout()
        self.metric_n    = self._metric_card("N (Población)", "—")
        self.metric_mean = self._metric_card("Media (μ)", "—")
        self.metric_std  = self._metric_card("Desv. Estándar (σ)", "—")
        self.metric_min  = self._metric_card("Mínimo", "—")
        self.metric_max  = self._metric_card("Máximo", "—")
        for m in [self.metric_n, self.metric_mean, self.metric_std,
                  self.metric_min, self.metric_max]:
            self.metrics_row.addWidget(m)
        lay.addLayout(self.metrics_row)

        # Proporciones + gráfica
        split = QSplitter(Qt.Horizontal)

        gb_prop, lay_prop = _card("Proporciones — Variable Categórica")
        self.tbl_prop = StyledTable()
        lay_prop.addWidget(self.tbl_prop)
        split.addWidget(gb_prop)

        gb_chart, lay_chart = _card("Histograma Poblacional")
        self.canvas_hist_pop = QLabel("(ejecuta Fase 1)")
        self.canvas_hist_pop.setAlignment(Qt.AlignCenter)
        lay_chart.addWidget(self.canvas_hist_pop)
        split.addWidget(gb_chart)

        split.setSizes([350, 650])
        lay.addWidget(split, 1)
        return w

    # ─────────────────────── Tab: Fase 2 ───────────────────────
    def _tab_phase2(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Controles
        ctrl = QHBoxLayout()
        ctrl.addWidget(_label("Tamaño de muestra (n):", size=9, bold=True))
        self.spn_n = QSpinBox()
        self.spn_n.setRange(5, 100_000)
        self.spn_n.setValue(100)
        self.spn_n.setFixedWidth(90)
        ctrl.addWidget(self.spn_n)
        ctrl.addWidget(_label("Número de muestras (k):", size=9, bold=True))
        self.spn_k = QSpinBox()
        self.spn_k.setRange(1, 20)
        self.spn_k.setValue(5)
        self.spn_k.setFixedWidth(70)
        ctrl.addWidget(self.spn_k)

        self.btn_phase2 = _button("Generar Muestras", SUCCESS, "#047857")
        self.btn_phase2.clicked.connect(self._run_phase2)
        ctrl.addWidget(self.btn_phase2)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        split = QSplitter(Qt.Vertical)

        gb_tbl, lay_tbl = _card("Tabla comparativa — Medias muestrales vs Poblacional")
        self.tbl_samples = StyledTable()
        lay_tbl.addWidget(self.tbl_samples)
        split.addWidget(gb_tbl)

        gb_chart, lay_chart = _card("Gráfico comparativo")
        self.canvas_means = QLabel("(genera las muestras primero)")
        self.canvas_means.setAlignment(Qt.AlignCenter)
        lay_chart.addWidget(self.canvas_means)
        split.addWidget(gb_chart)

        split.setSizes([250, 400])
        lay.addWidget(split, 1)
        return w

    # ─────────────────────── Tab: Fases 3 & 4 ──────────────────
    def _tab_phase34(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16,5,16,5)
        lay.setSpacing(0)

        self.btn_phase34 = _button("Calcular Estimaciones", SUCCESS, "#047857")
        self.btn_phase34.clicked.connect(self._run_phase34)

        self.tabs_inner = QTabWidget()

        hb = QHBoxLayout()
        hb.setSpacing(8)
        hb.addWidget(self.btn_phase34)
        hb.addWidget(self.tabs_inner.tabBar())
        hb.addStretch()
        hb.setContentsMargins(16, 0, 16, 0)
        lay.addLayout(hb)

        lay.addWidget(self.tabs_inner, 1)

        tabs_inner = QTabWidget()
        tabs_inner.setStyleSheet("""
            QTabBar::tab { min-width: 0px; }
        """)


        # Sub-tab Fase 3
        f3 = QWidget()
        f3_lay = QVBoxLayout(f3)
        f3_lay.setContentsMargins(0,16,0,0)
        gb3, lay3 = _card("Fase 3 — Estimación puntual por muestra")
        self.tbl_point = StyledTable()
        lay3.addWidget(self.tbl_point)
        f3_lay.addWidget(gb3)
        self.tabs_inner.addTab(f3, "Fase 3 — Estimación Puntual")

        # Sub-tab Fase 4
        f4 = QWidget()
        f4_lay = QVBoxLayout(f4)
        f4_lay.setContentsMargins(0,16,0,0)
        f4_split = QSplitter(Qt.Vertical)

        gb4, lay4 = _card("Fase 4 — Intervalos de confianza 95%")
        gb4.setMinimumHeight(200)
        self.tbl_intervals = StyledTable()
        lay4.addWidget(self.tbl_intervals)
        f4_split.addWidget(gb4)

        gb4c, lay4c = _card("Visualización de intervalos")
        gb4c.setMinimumHeight(500)
        ic_tabs = QTabWidget()
        ic_tabs.tabBar().setExpanding(True)
        ic_tabs.setContentsMargins(0, 0, 0, 0)
        self.canvas_ci_mean = QLabel("(ejecuta estimación)"); self.canvas_ci_mean.setAlignment(Qt.AlignCenter)
        self.canvas_ci_prop = QLabel("(ejecuta estimación)"); self.canvas_ci_prop.setAlignment(Qt.AlignCenter)
        ic_tabs.addTab(self.canvas_ci_mean, "IC — Media")
        ic_tabs.addTab(self.canvas_ci_prop, "IC — Proporción")
        lay4c.addWidget(ic_tabs)
        f4_split.addWidget(gb4c)

        f4_split.setSizes([400, 800])
        f4_lay.addWidget(f4_split)
        self.tabs_inner.addTab(f4, "Fase 4 — Intervalos de Confianza")

        lay.addWidget(tabs_inner, 1)
        return w

    # ─────────────────────── Tab: Simulación ───────────────────
    def _tab_simulation(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        ctrl = QHBoxLayout()
        ctrl.addWidget(_label("n mínimo:", size=9, bold=True))
        self.spn_sim_min = QSpinBox(); self.spn_sim_min.setRange(5, 10000); self.spn_sim_min.setValue(10); self.spn_sim_min.setFixedWidth(80)
        ctrl.addWidget(self.spn_sim_min)
        ctrl.addWidget(_label("n máximo:", size=9, bold=True))
        self.spn_sim_max = QSpinBox(); self.spn_sim_max.setRange(10, 100000); self.spn_sim_max.setValue(500); self.spn_sim_max.setFixedWidth(90)
        ctrl.addWidget(self.spn_sim_max)
        ctrl.addWidget(_label("Pasos:", size=9, bold=True))
        self.spn_sim_steps = QSpinBox(); self.spn_sim_steps.setRange(5, 50); self.spn_sim_steps.setValue(15); self.spn_sim_steps.setFixedWidth(70)
        ctrl.addWidget(self.spn_sim_steps)
        ctrl.addWidget(_label("Réplicas por n:", size=9, bold=True))
        self.spn_sim_reps = QSpinBox(); self.spn_sim_reps.setRange(10, 500); self.spn_sim_reps.setValue(50); self.spn_sim_reps.setFixedWidth(70)
        ctrl.addWidget(self.spn_sim_reps)

        self.btn_sim = _button("🔬  Ejecutar Simulación", "#7C3AED", "#6D28D9")
        self.btn_sim.clicked.connect(self._run_simulation)
        ctrl.addWidget(self.btn_sim)
        ctrl.addStretch()
        lay.addLayout(ctrl)

        split = QSplitter(Qt.Vertical)

        gb_tbl, lay_tbl = _card("Tabla de resultados por tamaño de muestra")
        self.tbl_sim = StyledTable()
        lay_tbl.addWidget(self.tbl_sim)
        split.addWidget(gb_tbl)

        gb_chart, lay_chart = _card("Error e IC en función de n")
        self.canvas_sim = QLabel("(ejecuta la simulación)")
        self.canvas_sim.setAlignment(Qt.AlignCenter)
        lay_chart.addWidget(self.canvas_sim)
        split.addWidget(gb_chart)

        split.setSizes([200, 450])
        lay.addWidget(split, 1)
        return w

    # ─────────────────────── Tarjeta métrica ───────────────────
    def _metric_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lbl_t = _label(title, size=8, color=TEXT_MUTED)
        lbl_v = _label(value, bold=True, size=16, color=SUCCESS)
        lbl_v.setObjectName("metric_val")
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_v)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return card

    def _update_metric(self, card: QFrame, value: str) -> None:
        for child in card.findChildren(QLabel):
            if child.objectName() == "metric_val":
                child.setText(value)

    # ─────────────────────── Status bar ────────────────────────
    def _init_status(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.setStyleSheet(f"""
            QStatusBar {{
                background: {BG_SIDEBAR};
                color: #94A3B8;
                font: 8pt 'Segoe UI';
                border-top: 1px solid #334155;
            }}
        """)
        self.status.showMessage("Listo — carga un archivo para comenzar.")

    def _msg(self, text: str) -> None:
        self.status.showMessage(text)

    # ─────────────────────── Acciones ──────────────────────────
    def _on_load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir dataset", "",
            "Archivos de datos (*.csv *.xlsx *.xls *.txt);;Todos (*)"
        )
        if not path:
            return
        try:
            df = self.svc.load_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar", str(e))
            return

        self.lbl_file.setText(f"📄 {Path(path).name}  ({df.shape[0]:,} filas × {df.shape[1]} cols)")
        self.lbl_shape.setText(f"Forma: {df.shape[0]:,} × {df.shape[1]}   |   "
                                f"Columnas: {', '.join(df.columns[:8])}{'…' if len(df.columns)>8 else ''}")
        self.tbl_data.load_dataframe(df, max_rows=1000)

        # Actualiza combos
        num_cols = df.select_dtypes("number").columns.tolist()
        cat_cols = df.select_dtypes(["object","category"]).columns.tolist()

        self.cmb_numeric.clear(); self.cmb_numeric.addItems(num_cols)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— ninguna —")
        self.cmb_cat.addItems(cat_cols)

        self._msg(f"Archivo cargado: {Path(path).name} — {df.shape[0]:,} registros")
        self.tabs.setCurrentIndex(0)

    # ─────────── Fase 1 ────────────────────────────────────────
    def _run_phase1(self) -> None:
        if self.svc.df is None:
            QMessageBox.warning(self, "Sin datos", "Carga un archivo primero."); return
        num_col = self.cmb_numeric.currentText()
        cat_col = self.cmb_cat.currentText()
        if not num_col:
            QMessageBox.warning(self, "Sin variable", "Selecciona una variable numérica."); return
        cat_col = None if cat_col.startswith("—") else cat_col

        try:
            ps = self.svc.compute_population_stats(num_col, cat_col)
        except Exception as e:
            QMessageBox.critical(self, "Error Fase 1", str(e)); return

        self._update_metric(self.metric_n,    f"{ps.n:,}")
        self._update_metric(self.metric_mean, f"{ps.mean:.4f}")
        self._update_metric(self.metric_std,  f"{ps.std:.4f}")
        self._update_metric(self.metric_min,  f"{ps.min_val:.4f}")
        self._update_metric(self.metric_max,  f"{ps.max_val:.4f}")

        if ps.proportions:
            rows = [[cat, f"{p*100:.2f}%"] for cat, p in sorted(
                ps.proportions.items(), key=lambda x: -x[1])]
            self.tbl_prop.load_dict_rows(["Categoría", "Proporción"], rows)
        else:
            self.tbl_prop.load_dict_rows(["Info"], [["No se seleccionó variable categórica"]])

        # Histograma
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        fig, ax = plt.subplots(figsize=(6, 4), facecolor="#F8FAFC")
        ax.set_facecolor("#F8FAFC")
        vals = self.svc.df[num_col].dropna()
        ax.hist(vals, bins=30, color=ACCENT, alpha=0.8, edgecolor="white", linewidth=0.5)
        ax.axvline(ps.mean, color=SUCCESS, linewidth=2, linestyle="--",
                   label=f"Media = {ps.mean:.3f}")
        ax.set_title(f"Distribución poblacional — «{num_col}»", fontsize=11, fontweight="bold")
        ax.set_xlabel(num_col); ax.set_ylabel("Frecuencia")
        ax.legend(fontsize=9)
        fig.tight_layout()

        canvas = MplCanvas(fig)
        # reemplaza el placeholder
        gb = self.canvas_hist_pop.parent()
        if gb:
            lay = gb.layout()
            if lay:
                lay.replaceWidget(self.canvas_hist_pop, canvas)
                self.canvas_hist_pop.deleteLater()
                self.canvas_hist_pop = canvas

        self.tabs.setCurrentIndex(1)
        self._msg(f"Fase 1 completada — N={ps.n:,}  μ={ps.mean:.4f}  σ={ps.std:.4f}")

    # ─────────── Fase 2 ────────────────────────────────────────
    def _run_phase2(self) -> None:
        if self.svc.pop_stats is None:
            QMessageBox.warning(self, "Falta Fase 1", "Ejecuta primero el análisis de población."); return

        n = self.spn_n.value()
        k = self.spn_k.value()
        if n > self.svc.pop_stats.n:
            QMessageBox.warning(self, "n muy grande",
                f"n={n} excede la población N={self.svc.pop_stats.n}."); return

        try:
            samples = self.svc.generate_samples(n=n, k=k)
        except Exception as e:
            QMessageBox.critical(self, "Error Fase 2", str(e)); return

        # Tabla
        headers = ["Muestra", "Tamaño", "Media Muestral", "Media Poblacional",
                   "Diferencia", "Diferencia %"]
        rows = []
        for s in samples:
            diff = s.mean - self.svc.pop_stats.mean
            pct  = diff / self.svc.pop_stats.mean * 100 if self.svc.pop_stats.mean != 0 else 0
            rows.append([f"M{s.sample_id}", s.size, s.mean,
                         self.svc.pop_stats.mean, diff, pct])
        self.tbl_samples.load_dict_rows(headers, rows)

        # Gráfico
        fig = chart_means_comparison(samples, self.svc.pop_stats, self.svc.numeric_col or "")
        canvas = MplCanvas(fig)
        self._replace_placeholder(self.canvas_means, canvas, "canvas_means")

        self.tabs.setCurrentIndex(2)
        self._msg(f"Fase 2 completada — {k} muestras de tamaño n={n} generadas.")

    # ─────────── Fases 3 & 4 ───────────────────────────────────
    def _run_phase34(self) -> None:
        if not self.svc.samples:
            QMessageBox.warning(self, "Sin muestras", "Ejecuta primero la Fase 2."); return

        samples   = self.svc.samples
        pop_stats = self.svc.pop_stats

        # Fase 3 — Estimación puntual
        headers3 = ["Muestra", "Media Muestral", "Proporción Muestral"]
        rows3 = []
        for s in samples:
            prop_str = f"{s.proportion:.4f}" if s.proportion is not None else "N/A"
            rows3.append([f"M{s.sample_id}", s.mean, prop_str])
        self.tbl_point.load_dict_rows(headers3, rows3)

        # Fase 4 — IC
        headers4 = ["Muestra", "IC Media (low)", "IC Media (high)",
                    "Contiene μ?", "IC Prop (low)", "IC Prop (high)", "Contiene p?"]
        rows4 = []
        for s in samples:
            rows4.append([
                f"M{s.sample_id}",
                s.ci_mean_low, s.ci_mean_high,
                "✅ Sí" if s.mean_contains_pop else "❌ No",
                f"{s.ci_prop_low:.4f}" if s.ci_prop_low is not None else "N/A",
                f"{s.ci_prop_high:.4f}" if s.ci_prop_high is not None else "N/A",
                "✅ Sí" if s.prop_contains_pop else "❌ No",
            ])
        self.tbl_intervals.load_dict_rows(headers4, rows4)

        # Gráficos IC
        fig_mean = chart_confidence_intervals(samples, pop_stats, "mean")
        canvas_m = MplCanvas(fig_mean)
        self._replace_placeholder(self.canvas_ci_mean, canvas_m, "canvas_ci_mean")

        if any(s.ci_prop_low is not None for s in samples):
            fig_prop = chart_confidence_intervals(samples, pop_stats, "proportion")
            canvas_p = MplCanvas(fig_prop)
            self._replace_placeholder(self.canvas_ci_prop, canvas_p, "canvas_ci_prop")

        self.tabs.setCurrentIndex(3)
        n_ok = sum(s.mean_contains_pop for s in samples)
        self._msg(f"Fases 3 & 4 completadas — {n_ok}/{len(samples)} ICs contienen la media poblacional.")

    # ─────────── Simulación ────────────────────────────────────
    def _run_simulation(self) -> None:
        if self.svc.pop_stats is None:
            QMessageBox.warning(self, "Falta Fase 1", "Ejecuta primero el análisis de población."); return

        n_min   = self.spn_sim_min.value()
        n_max   = min(self.spn_sim_max.value(), self.svc.pop_stats.n)
        steps   = self.spn_sim_steps.value()
        reps    = self.spn_sim_reps.value()

        import numpy as np
        sizes = [int(x) for x in np.linspace(n_min, n_max, steps)]

        try:
            points = self.svc.simulate_sample_sizes(sizes=sizes, replications=reps)
        except Exception as e:
            QMessageBox.critical(self, "Error Simulación", str(e)); return

        # Tabla
        headers = ["n", "Error Absoluto Promedio", "Ancho IC 95%"]
        rows = [[p.n, p.mean_error, p.ci_width] for p in points]
        self.tbl_sim.load_dict_rows(headers, rows)

        # Gráfico
        fig = chart_simulation(points)
        canvas = MplCanvas(fig)
        self._replace_placeholder(self.canvas_sim, canvas, "canvas_sim")

        self.tabs.setCurrentIndex(4)
        self._msg(f"Simulación completada — {len(points)} puntos evaluados.")

    # ─────────── Helper para reemplazar placeholders ────────────
    def _replace_placeholder(self, placeholder: QWidget, new_widget: QWidget, attr: str) -> None:
        """Reemplaza un QLabel placeholder con un widget real."""
        parent = placeholder.parent()
        if parent is None:
            return
        layout = parent.layout()
        if layout is None:
            return
        idx = layout.indexOf(placeholder)
        if idx == -1:
            # Busca recursivamente
            self._deep_replace(placeholder, new_widget)
        else:
            layout.replaceWidget(placeholder, new_widget)
            placeholder.deleteLater()
        setattr(self, attr, new_widget)

    def _deep_replace(self, old: QWidget, new_widget: QWidget) -> bool:
        """Búsqueda profunda para reemplazar widget en layouts anidados."""
        def _search(layout):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() == old:
                    layout.replaceWidget(old, new_widget)
                    old.deleteLater()
                    return True
                if item.layout():
                    if _search(item.layout()):
                        return True
                if item.widget():
                    child_layout = item.widget().layout()
                    if child_layout and _search(child_layout):
                        return True
            return False

        for widget in self.findChildren(QWidget):
            if widget.layout():
                if _search(widget.layout()):
                    return True
        return False
