# StatsMethods | Analisis de Muestreo y Estimación

Aplicación de escritorio en Python para **análisis estadístico de muestreo y estimación**.  
Construida con PyQt5, pandas, numpy, scipy y matplotlib.

---

## Instalación y ejecución rápida

```bash
# 1. Clonar / descomprimir el proyecto
cd StatsMethods - Analisis de Muestro y Estimación

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Generar dataset de ejemplo
python generate_sample_data.py

# 5. Ejecutar la aplicación
python main.py
```

---

## Estructura del proyecto

```
stat_app/
├── main.py                        # Punto de entrada
├── requirements.txt
├── generate_sample_data.py        # Genera datos de prueba
├── data/
│   └── estudiantes.csv            # Dataset de ejemplo (1 500 registros)
│
├── services/
│   ├── __init__.py
│   └── statistics_service.py      # Toda la lógica estadística (pura Python)
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py             # Ventana principal y cada pestaña
│   ├── canvas.py                  # Widget matplotlib embebido en Qt
│   └── table_widget.py            # QTableWidget estilizado y reutilizable
│
├── utils/
│   ├── __init__.py
│   └── charts.py                  # Generadores de figuras matplotlib
│
└── models/
    └── __init__.py                # Reservado para futuras entidades
```

---

## Flujo de trabajo en la app

| Paso | Pestaña | Acción |
|------|---------|--------|
| 1 | **Datos** | Carga CSV / Excel / TXT con el botón "📂 Cargar archivo" |
| 2 | Barra superior | Elige **variable numérica** y opcionalmente **variable categórica** |
| 3 | **Fase 1** | Pulsa " Fase 1" → estadísticos poblacionales + histograma |
| 4 | **Fase 2** | Ajusta n y k, pulsa " Generar Muestras" → tabla + gráfico comparativo |
| 5 | **Fases 3 & 4** | Pulsa " Calcular Estimaciones" → puntual + intervalos de confianza |
| 6 | **Simulación** | Ajusta rango de n y réplicas, pulsa " Ejecutar Simulación" |

---

## Dataset de ejemplo — `data/estudiantes.csv`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | int | Identificador |
| `puntaje` | float | Puntaje en prueba (0–100) — **variable numérica principal** |
| `gpa` | float | Promedio académico (0–4) |
| `edad` | int | Edad del estudiante (16–24) |
| `asistencia` | float | Porcentaje de asistencia |
| `genero` | str | Femenino / Masculino / No binario — **variable categórica** |
| `estrato` | str | Estrato socioeconómico 1–6 |

**Configuración sugerida para explorar la app:**
- Variable numérica → `puntaje`
- Variable categórica → `genero`
- n = 100, k = 5

---

### Separación de responsabilidades

```
StatisticsService  ← solo numpy/scipy/pandas, sin PyQt5
    ↓ devuelve dataclasses (PopulationStats, SampleResult…)
utils/charts.py    ← solo matplotlib, sin PyQt5
    ↓ devuelve Figure
ui/canvas.py       ← embebe Figure en Qt
ui/main_window.py  ← coordina todo, maneja eventos
```

---

## Metodología estadística

### Intervalo de confianza para la media
$$\bar{x} \pm z_{\alpha/2} \cdot \frac{s}{\sqrt{n}}$$

Con $z_{0.025} = 1.96$ para un nivel de confianza del 95%.

### Intervalo de confianza para proporciones
$$\hat{p} \pm z_{\alpha/2} \cdot \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$

### Error estándar de muestreo
$$SE = \frac{s}{\sqrt{n}}$$

La simulación demuestra que al duplicar n, el error se reduce en un factor de $\sqrt{2}$.

---



## Dependencias

```
PyQt5 >= 5.15      # Interfaz gráfica
pandas >= 1.5      # Manipulación de datos
numpy >= 1.23      # Cálculo numérico
scipy >= 1.9       # Distribuciones estadísticas (norm.ppf)
matplotlib >= 3.6  # Visualizaciones
openpyxl >= 3.0    # Lectura de archivos Excel
```
