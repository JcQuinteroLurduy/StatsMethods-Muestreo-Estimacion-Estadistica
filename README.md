# StatSampler Pro 📊

Aplicación de escritorio en Python para **análisis estadístico de muestreo y estimación**.  
Construida con PyQt5, pandas, numpy, scipy y matplotlib.

---

## 🚀 Instalación y ejecución rápida

```bash
# 1. Clonar / descomprimir el proyecto
cd stat_app

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

## 🗂 Estructura del proyecto

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
│   ├── main_window.py             # Ventana principal + 5 pestañas
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

## 🎯 Flujo de trabajo en la app

| Paso | Pestaña | Acción |
|------|---------|--------|
| 1 | **Datos** | Carga CSV / Excel / TXT con el botón "📂 Cargar archivo" |
| 2 | Barra superior | Elige **variable numérica** y (opcionalmente) **variable categórica** |
| 3 | **Fase 1** | Pulsa "▶ Fase 1" → estadísticos poblacionales + histograma |
| 4 | **Fase 2** | Ajusta n y k, pulsa "🎲 Generar Muestras" → tabla + gráfico comparativo |
| 5 | **Fases 3 & 4** | Pulsa "📐 Calcular Estimaciones" → puntual + intervalos de confianza |
| 6 | **Simulación** | Ajusta rango de n y réplicas, pulsa "🔬 Ejecutar Simulación" |

---

## 📊 Dataset de ejemplo — `data/estudiantes.csv`

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

## 🧱 Decisiones técnicas

### ¿Por qué PyQt5 y no Tkinter?

| Criterio | PyQt5 ✅ | Tkinter |
|----------|----------|---------|
| Aspecto visual | Nativo moderno, estilizable con CSS-like QSS | Anticuado en todos los SO |
| Integración matplotlib | `FigureCanvasQTAgg` nativa | Requiere wrappers frágiles |
| Tablas | `QTableWidget` potente | `ttk.Treeview` muy limitado |
| Layouts | `QSplitter`, `QTabWidget` | Nulo splitter, sin tabs nativas |
| Threads | `QThread` integrado | `threading` manual + riesgos |

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

## 🔬 Metodología estadística

### Intervalo de confianza para la media
$$\bar{x} \pm z_{\alpha/2} \cdot \frac{s}{\sqrt{n}}$$

Con $z_{0.025} = 1.96$ para un nivel de confianza del 95%.

### Intervalo de confianza para proporciones
$$\hat{p} \pm z_{\alpha/2} \cdot \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$

### Error estándar de muestreo
$$SE = \frac{s}{\sqrt{n}}$$

La simulación demuestra que al duplicar n, el error se reduce en un factor de $\sqrt{2}$.

---

## 💡 Sugerencias de mejora (nivel pro)

1. **Muestreo estratificado** — Agregar `StratifiedSampler` en `services/` usando `pandas.groupby` para garantizar representatividad por categoría.

2. **Bootstrap IC** — Implementar intervalos de confianza por bootstrap (10 000 resamplings) como alternativa no paramétrica, especialmente útil para distribuciones asimétricas.

3. **Exportar resultados** — Botón "Exportar a Excel" usando `openpyxl` con colores condicionales en las celdas de IC.

4. **Tests unitarios** — Agregar `pytest` con fixtures para `StatisticsService`; cobertura mínima del 90% en la capa de servicios.

5. **Tamaño de muestra óptimo** — Calculadora integrada: dado un margen de error y nivel de confianza deseados, calcular el n mínimo necesario.

6. **Distribución de medias muestrales** — Visualizar el Teorema Central del Límite animado (histograma que converge a normal conforme aumenta k).

7. **Soporte para muestreo sistemático y por conglomerados** — Ampliar `generate_samples()` con un parámetro `method: Literal["simple", "systematic", "cluster"]`.

8. **Panel de comparación de métodos** — Dashboard que compare SRS vs estratificado en términos de precisión del IC para el mismo n.

---

## 📦 Dependencias

```
PyQt5 >= 5.15      # Interfaz gráfica
pandas >= 1.5      # Manipulación de datos
numpy >= 1.23      # Cálculo numérico
scipy >= 1.9       # Distribuciones estadísticas (norm.ppf)
matplotlib >= 3.6  # Visualizaciones
openpyxl >= 3.0    # Lectura de archivos Excel
```
