"""
utils/charts.py
Genera figuras matplotlib para embeber en la UI de PyQt5.
"""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from services.statistics_service import PopulationStats, SampleResult, SimulationPoint

# Paleta corporativa
C_POP   = "#2563EB"   # azul población
C_SAMP  = "#10B981"   # verde muestra
C_ERROR = "#EF4444"   # rojo error/fuera de IC
C_OK    = "#10B981"   # verde dentro de IC
C_BG    = "#F8FAFC"
C_GRID  = "#E2E8F0"
C_TEXT  = "#1E293B"


def _base_fig(w: float = 9, h: float = 5) -> tuple[Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(w, h), facecolor=C_BG)
    ax.set_facecolor(C_BG)
    ax.grid(True, color=C_GRID, linewidth=0.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_TEXT, labelsize=9)
    ax.title.set_color(C_TEXT)
    ax.xaxis.label.set_color(C_TEXT)
    ax.yaxis.label.set_color(C_TEXT)
    return fig, ax


def chart_means_comparison(
    samples: list[SampleResult],
    pop_stats: PopulationStats,
    numeric_col: str,
) -> Figure:
    """Barras: media muestral vs línea de media poblacional."""
    fig, ax = _base_fig(8, 5)

    ids = [f"M{s.sample_id}" for s in samples]
    means = [s.mean for s in samples]
    colors = [
        C_OK if abs(s.mean - pop_stats.mean) / pop_stats.std < 0.3 else C_ERROR
        for s in samples
    ]

    bars = ax.bar(ids, means, color=colors, width=0.5, zorder=3, edgecolor="white", linewidth=1.2)
    ax.axhline(pop_stats.mean, color=C_POP, linewidth=2.2, linestyle="--",
               label=f"Media poblacional = {pop_stats.mean:.4f}", zorder=4)

    for bar, val in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (pop_stats.std * 0.02),
            f"{val:.3f}",
            ha="center", va="bottom", fontsize=8.5, color=C_TEXT, fontweight="bold"
        )

    ax.set_title(f"Medias muestrales vs Media poblacional  —  «{numeric_col}»",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Muestra")
    ax.set_ylabel("Media")
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def chart_confidence_intervals(
    samples: list[SampleResult],
    pop_stats: PopulationStats,
    kind: str = "mean",   # "mean" | "proportion"
) -> Figure:
    """Gráfico de intervalos de confianza al 95%."""
    fig, ax = _base_fig(7,4 )

    pop_val = pop_stats.mean if kind == "mean" else max(
        pop_stats.proportions.values(), default=0
    )

    for s in samples:
        low  = s.ci_mean_low  if kind == "mean" else s.ci_prop_low
        high = s.ci_mean_high if kind == "mean" else s.ci_prop_high
        ctr  = s.mean         if kind == "mean" else s.proportion
        ok   = s.mean_contains_pop if kind == "mean" else s.prop_contains_pop

        if low is None or high is None or ctr is None:
            continue

        color = C_OK if ok else C_ERROR
        y = s.sample_id
        ax.plot([low, high], [y, y], color=color, linewidth=2.5, solid_capstyle="round", zorder=3)
        ax.scatter(ctr, y, color=color, s=55, zorder=4)

    ax.axvline(pop_val, color=C_POP, linewidth=2, linestyle="--",
               label=f"Valor poblacional = {pop_val:.4f}", zorder=5)

    label = "Media" if kind == "mean" else "Proporción"
    ax.set_title(f"Intervalos de confianza 95% — {label}", fontsize=12,
                 fontweight="bold", pad=12)
    ax.set_xlabel(label)
    ax.set_ylabel("Muestra #")
    ax.set_yticks([s.sample_id for s in samples])
    ax.set_yticklabels([f"M{s.sample_id}" for s in samples])

    patch_ok  = mpatches.Patch(color=C_OK,    label="Contiene valor poblacional")
    patch_err = mpatches.Patch(color=C_ERROR, label="No contiene valor poblacional")
    ax.legend(handles=[patch_ok, patch_err,
                        mpatches.Patch(color=C_POP, label=f"Valor pob. = {pop_val:.4f}")],
              fontsize=9)
    fig.tight_layout()
    return fig


def chart_simulation(points: list[SimulationPoint]) -> Figure:
    """Doble eje: error absoluto y ancho IC vs tamaño de muestra."""
    fig, ax1 = plt.subplots(figsize=(10, 6), facecolor=C_BG)
    ax1.set_facecolor(C_BG)
    ax1.grid(True, color=C_GRID, linewidth=0.8, zorder=0)
    for spine in ax1.spines.values():
        spine.set_color(C_GRID)

    ns     = [p.n         for p in points]
    errors = [p.mean_error for p in points]
    widths = [p.ci_width   for p in points]

    ax1.plot(ns, errors, "o-", color=C_ERROR, linewidth=2.2, markersize=6,
             label="Error absoluto promedio", zorder=3)
    ax1.set_xlabel("Tamaño de muestra (n)", color=C_TEXT, fontsize=10)
    ax1.set_ylabel("Error absoluto promedio", color=C_ERROR, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=C_ERROR)

    ax2 = ax1.twinx()
    ax2.plot(ns, widths, "s--", color=C_POP, linewidth=2.2, markersize=6,
             label="Ancho IC 95%", zorder=3)
    ax2.set_ylabel("Ancho intervalo de confianza 95%", color=C_POP, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=C_POP)
    ax2.set_facecolor(C_BG)

    lines1, labs1 = ax1.get_legend_handles_labels()
    lines2, labs2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labs1 + labs2, fontsize=9, loc="upper right")

    ax1.set_title("Efecto del tamaño de muestra sobre error e IC",
                  fontsize=12, fontweight="bold", color=C_TEXT, pad=12)
    fig.tight_layout()
    return fig


def chart_histogram(
    samples: list[SampleResult],
    pop_stats: PopulationStats,
    numeric_col: str,
) -> Figure:
    """Histogramas superpuestos de las muestras con línea de media poblacional."""
    fig, ax = _base_fig(9, 5)
    palette = ["#3B82F6","#10B981","#F59E0B","#8B5CF6","#EC4899"]

    for s in samples:
        vals = s.data[numeric_col].dropna()
        ax.hist(vals, bins=18, alpha=0.35, color=palette[s.sample_id % len(palette)],
                label=f"Muestra {s.sample_id}", edgecolor="white", linewidth=0.4, zorder=3)

    ax.axvline(pop_stats.mean, color=C_POP, linewidth=2.5, linestyle="--",
               label=f"Media pob. = {pop_stats.mean:.3f}", zorder=5)

    ax.set_title(f"Distribución de muestras — «{numeric_col}»",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Valor")
    ax.set_ylabel("Frecuencia")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig
