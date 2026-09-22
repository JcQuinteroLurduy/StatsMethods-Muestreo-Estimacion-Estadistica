"""
services/statistics_service.py
Lógica estadística pura — separada completamente de la UI.
"""

from __future__ import annotations

import numpy as np #error estádndar y en simulación, IC
import pandas as pd 
from scipy import stats # error estándar
from dataclasses import dataclass, field  # crear clases 100% enfocadas a datos sin un deploy tradicional + objetos mutables(dict)
from typing import Optional # Abre la posibilidad de valores nulos o 'none'


# ---------------------------------------------------------------------------
# Modelos de datos
# ---------------------------------------------------------------------------

@dataclass
class PopulationStats:
    n: int
    mean: float
    std: float
    min_val: float
    max_val: float
    proportions: dict[str, float] = field(default_factory=dict)


@dataclass
class SampleResult:
    sample_id: int
    size: int
    data: pd.DataFrame
    mean: float
    proportion: Optional[float]
    ci_mean_low: float
    ci_mean_high: float
    ci_prop_low: Optional[float]
    ci_prop_high: Optional[float]
    mean_contains_pop: bool
    prop_contains_pop: bool


@dataclass
class SimulationPoint:
    n: int
    mean_error: float
    ci_width: float


# ---------------------------------------------------------------------------
# Servicio principal
# ---------------------------------------------------------------------------

class StatisticsService:
    """Encapsula toda la lógica estadística de la aplicación."""

    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.numeric_col: Optional[str] = None
        self.categorical_col: Optional[str] = None
        self.pop_stats: Optional[PopulationStats] = None
        self.samples: list[SampleResult] = []

    # ------------------------------------------------------------------
    # Fase 1 — Población
    # ------------------------------------------------------------------

    def load_file(self, path: str) -> pd.DataFrame:
        """Carga CSV, Excel o TXT y devuelve el DataFrame."""
        lower = path.lower()
        if lower.endswith(".csv"):
            df = pd.read_csv(path)
        elif lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(path)
        elif lower.endswith(".txt"):
            # Intenta separadores comunes
            for sep in ["\t", ";", ","]:
                try:
                    df = pd.read_csv(path, sep=sep)
                    if df.shape[1] > 1:
                        break
                except Exception:
                    continue
            else:
                df = pd.read_csv(path, sep=r'\s+', engine="python")
        else:
            raise ValueError(f"Formato no soportado: {path}")

        if df.empty:
            raise ValueError("El archivo está vacío o no tiene datos válidos.")
        self.df = df
        return df

    def compute_population_stats(
        self,
        numeric_col: str,
        categorical_col: Optional[str] = None,
    ) -> PopulationStats:
        """Calcula estadísticos poblacionales."""
        if self.df is None:
            raise RuntimeError("No hay dataset cargado.")

        series = self.df[numeric_col].dropna()
        props: dict[str, float] = {}

        if categorical_col:
            counts = self.df[categorical_col].value_counts(normalize=True, dropna=True)
            props = counts.to_dict()

        self.numeric_col = numeric_col
        self.categorical_col = categorical_col
        self.pop_stats = PopulationStats(
            n=len(series),
            mean=float(series.mean()),
            std=float(series.std(ddof=0)),   # desviación poblacional
            min_val=float(series.min()),
            max_val=float(series.max()),
            proportions=props,
        )
        return self.pop_stats

    # ------------------------------------------------------------------
    # Fases 2-4 — Muestras + estimación
    # ------------------------------------------------------------------

    def generate_samples(
        self,
        n: int = 100,
        k: int = 5,
        confidence: float = 0.95,
        random_seed: Optional[int] = 42,
    ) -> list[SampleResult]:
        """
        Genera k muestras de tamaño n y calcula estimaciones.

        Args:
            n: Tamaño de cada muestra.
            k: Número de muestras.
            confidence: Nivel de confianza (0-1).
            random_seed: Semilla base para reproducibilidad.

        Returns:
            Lista de SampleResult.
        """
        if self.df is None or self.pop_stats is None or self.numeric_col is None:
            raise RuntimeError("Primero ejecuta el análisis de población (Fase 1).")

        N = len(self.df)
        if n > N:
            raise ValueError(f"n={n} es mayor que la población N={N}.")

        alpha = 1 - confidence
        z = stats.norm.ppf(1 - alpha / 2)

        results: list[SampleResult] = []

        for i in range(k):
            seed = (random_seed + i) if random_seed is not None else None
            sample_df = self.df.sample(n=n, replace=False, random_state=seed)

            # --- Media muestral ---
            s_mean = float(sample_df[self.numeric_col].mean())
            s_std = float(sample_df[self.numeric_col].std(ddof=1))
            se_mean = s_std / np.sqrt(n)

            ci_mean_low = s_mean - z * se_mean
            ci_mean_high = s_mean + z * se_mean
            mean_in = ci_mean_low <= self.pop_stats.mean <= ci_mean_high

            # --- Proporción muestral ---
            s_prop: Optional[float] = None
            ci_prop_low: Optional[float] = None
            ci_prop_high: Optional[float] = None
            prop_in = False

            if self.categorical_col:
                category = max(
                    self.pop_stats.proportions,
                    key=self.pop_stats.proportions.get,  # type: ignore
                )
                s_prop = float(
                    (sample_df[self.categorical_col] == category).mean()
                )
                se_prop = np.sqrt(s_prop * (1 - s_prop) / n)
                ci_prop_low = max(0.0, s_prop - z * se_prop)
                ci_prop_high = min(1.0, s_prop + z * se_prop)
                pop_prop = self.pop_stats.proportions.get(category, 0.0)
                prop_in = ci_prop_low <= pop_prop <= ci_prop_high

            results.append(
                SampleResult(
                    sample_id=i + 1,
                    size=n,
                    data=sample_df,
                    mean=s_mean,
                    proportion=s_prop,
                    ci_mean_low=ci_mean_low,
                    ci_mean_high=ci_mean_high,
                    ci_prop_low=ci_prop_low,
                    ci_prop_high=ci_prop_high,
                    mean_contains_pop=mean_in,
                    prop_contains_pop=prop_in,
                )
            )

        self.samples = results
        return results

    # ------------------------------------------------------------------
    # Simulación — tamaño de muestra
    # ------------------------------------------------------------------

    def simulate_sample_sizes(
        self,
        sizes: list[int],
        confidence: float = 0.95,
        replications: int = 50,
        random_seed: int = 0,
    ) -> list[SimulationPoint]:
        """
        Para cada n en `sizes`, promedia el error absoluto y el ancho del IC
        sobre `replications` muestras.
        """
        if self.df is None or self.pop_stats is None or self.numeric_col is None:
            raise RuntimeError("Primero ejecuta el análisis de población (Fase 1).")

        alpha = 1 - confidence
        z = stats.norm.ppf(1 - alpha / 2)
        pop_mean = self.pop_stats.mean
        N = len(self.df)
        points: list[SimulationPoint] = []

        for n in sizes:
            if n > N:
                continue
            errors, widths = [], []
            for rep in range(replications):
                seed = random_seed + n * 1000 + rep
                samp = self.df[self.numeric_col].sample(n=n, replace=False, random_state=seed)
                s_mean = samp.mean()
                s_std = samp.std(ddof=1)
                se = s_std / np.sqrt(n)
                errors.append(abs(s_mean - pop_mean))
                widths.append(2 * z * se)

            points.append(
                SimulationPoint(
                    n=n,
                    mean_error=float(np.mean(errors)),
                    ci_width=float(np.mean(widths)),
                )
            )

        return points
