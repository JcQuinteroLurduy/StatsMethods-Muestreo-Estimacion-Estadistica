"""
Genera el dataset de ejemplo: estudiantes con puntajes, género y estrato.
Ejecuta: python generate_sample_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(2024)
N = 1500

generos   = rng.choice(["Femenino", "Masculino", "No binario"], N, p=[0.48, 0.49, 0.03])
estratos  = rng.choice([1, 2, 3, 4, 5, 6], N, p=[0.18, 0.25, 0.27, 0.17, 0.08, 0.05])
edades    = rng.integers(16, 25, N)

# Puntaje influenciado suavemente por estrato
base  = 45 + estratos * 3
noise = rng.normal(0, 12, N)
puntaje = np.clip(base + noise, 0, 100).round(2)

gpa       = np.clip(puntaje / 25 + rng.normal(0, 0.2, N), 0, 4).round(2)
asistencia = np.clip(75 + rng.normal(0, 10, N), 0, 100).round(1)

df = pd.DataFrame({
    "id"         : range(1, N + 1),
    "puntaje"    : puntaje,
    "gpa"        : gpa,
    "edad"       : edades,
    "asistencia" : asistencia,
    "genero"     : generos,
    "estrato"    : estratos.astype(str),
})

df.to_csv("data/estudiantes.csv", index=False)
print(f"Dataset generado: data/estudiantes.csv  ({N} registros)")
print(df.describe())
