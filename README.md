# 🧠 GuarderIA - Asistente Inteligente para Elegir Guardería

GuarderIA es una aplicación impulsada por agentes de IA que ayuda a familias a encontrar la mejor guardería para sus hijos, según sus preferencias, ubicación y prioridades.

---

## 🎯 Visión de Negocio

### Problema
Encontrar la guardería adecuada es un proceso complejo y que consume mucho tiempo para las familias. Requiere investigar múltiples opciones, comparar características (a menudo subjetivas o difíciles de encontrar), visitar centros y tomar una decisión basada en información dispersa y, a veces, incompleta.

### Solución
GuarderIA simplifica este proceso utilizando IA para:
- **Recopilar** información relevante sobre guarderías cercanas a la ubicación del usuario.
- **Interpretar** las prioridades y preferencias específicas de cada familia (expresadas en lenguaje natural).
- **Analizar** objetivamente cada guardería en función de esas prioridades.
- **Puntuar y comparar** las opciones de forma ponderada.
- **Recomendar** la opción más adecuada con una justificación clara, ahorrando tiempo y estrés a las familias.

### Valor Añadido
- **Personalización:** Recomendaciones adaptadas a las necesidades únicas de cada familia.
- **Eficiencia:** Automatización de la búsqueda y análisis de información.
- **Objetividad:** Puntuaciones basadas en criterios explícitos y datos recopilados.
- **Claridad:** Presentación de la información de forma estructurada y fácil de entender.

---

## 🛠️ Visión Tecnológica

### Arquitectura General
GuarderIA se basa en una arquitectura de agentes autónomos orquestada por la librería `CrewAI`. La aplicación web se sirve mediante `Streamlit`.

1.  **Interfaz de Usuario (`Streamlit`):** Recoge la ubicación, preferencias de transporte y descripción en texto libre de las prioridades del usuario (`app.py`).
2.  **Orquestador (`CrewAI`):** Gestiona el flujo de ejecución secuencial de los agentes y sus tareas (`app.py`).
3.  **Agentes (`agents.py`):** Cada agente tiene un rol específico y utiliza herramientas para cumplir sus objetivos.
4.  **Tareas (`tasks.py`):** Definen las instrucciones específicas que cada agente debe ejecutar.
5.  **Herramientas (`tools/`):** Módulos reutilizables que interactúan con APIs externas (Google Maps, búsqueda web) o realizan funciones específicas (ponderación, formato).

### Flujo de Ejecución
1.  **Entrada del Usuario:** Se recoge la dirección, transporte, tiempo máximo y preferencias en texto.
2.  **`LocationAgent` (`location_task`):** Extrae la información estructurada de ubicación/transporte.
3.  **`PreferenciasAgent` (`preferencias_task`):** Analiza el texto libre y genera un JSON con las puntuaciones de importancia (5 o 3) para cada criterio (instalaciones, horario, etc.).
4.  **Búsqueda Inicial (Google Places):** Se utiliza `GooglePlacesTool` para encontrar guarderías cercanas según la ubicación, transporte y tiempo (`app.py`).
5.  **`RecolectorAgent` (`recolector_task` - *Ejecución múltiple*):** Para cada guardería encontrada, este agente:
    - Intenta obtener información detallada usando `ScrapeWebsiteTool` (si se tiene una URL) y/o `SerperDevTool`/`WebsiteSearchTool`.
    - Rellena un JSON detallado para cada guardería.
6.  **`PuntuadorAgent` (`puntuador_task`):**
    - Recibe el JSON de preferencias y la lista de JSONs de todas las guarderías investigadas (del contexto).
    - Utiliza `PonderacionTool`, que aplica una lógica de puntuación específica por criterio (0-5) y luego pondera según las preferencias del usuario.
    - La herramienta devuelve una lista JSON ordenada por `score`, incluyendo `detalles_puntuacion` para cada criterio y guardería.
7.  **`RecomendadorAgent` (`recomendador_task`):**
    - Recibe la lista de guarderías puntuadas (con detalles) y el JSON de preferencias (del contexto).
    - Analiza los resultados, compara las mejores opciones basándose en los criterios importantes para el usuario.
    - Genera un informe final en Markdown con la recomendación justificada, pros y contras.
8.  **Salida:** El informe Markdown se muestra al usuario en la interfaz de Streamlit.

### Componentes Clave y Herramientas
- **`crewai`:** Framework para la orquestación de agentes y tareas.
- **`streamlit`:** Creación de la interfaz web interactiva.
- **`langchain_openai` (`ChatOpenAI`):** Modelo LLM (GPT-4o-mini por defecto) para la inteligencia de los agentes.
- **`GooglePlacesTool`:** Interfaz con la API de Google Maps para buscar guarderías y calcular tiempos de viaje.
- **`SerperDevTool`, `ScrapeWebsiteTool`, `WebsiteSearchTool`:** Herramientas para la búsqueda web y extracción de contenido.
- **`PonderacionTool`:** Lógica personalizada para calcular la puntuación ponderada (0-5) para cada criterio con reglas específicas (precio inverso, longitud de texto, etc.), aplicar pesos de preferencias y devolver una lista JSON ordenada con `nombre`, `score` y `detalles_puntuacion`.
- **`FormatterTool`:** Ayuda a formatear la salida en Markdown.
- **Logging:** Se configura un logging detallado en `crew_execution.log` para depuración (`app.py`).

---

## 🚀 Requisitos

- Python 3.10 o superior
- OpenAI API Key (si usas modelos de OpenAI)
- Google Maps API Key

---

## 📦 Instalación

1. Clona este repositorio y accede a la carpeta del proyecto:

```bash
git clone https://github.com/tuusuario/guarderia-ia.git
cd guarderia-ia
```

2. Crea y activa un entorno virtual (opcional pero recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

---

## 🔐 Configuración de variables de entorno

Crea un archivo `.env` en la raíz del proyecto con:

```
OPENAI_API_KEY=sk-...
GOOGLE_MAPS_API_KEY=tu_api_key
SERPER_API_KEY=tu_api_key_serper
```

---

## 🖥️ Ejecutar la app en Streamlit

```bash
streamlit run app.py
```
*Nota: El nombre del archivo de ejecución principal es `app.py`.*

---

## ✨ Qué hace GuarderIA (Resumen Funcional)

1. El usuario describe lo que valora en una guardería, junto con su ubicación y preferencias de transporte.
2. El sistema busca guarderías cercanas usando Google Maps.
3. Cada guardería es investigada online por un agente especializado (`RecolectorAgent`).
4. Las preferencias del usuario se convierten en pesos numéricos (`PreferenciasAgent`).
5. Las guarderías se puntúan según la información encontrada y los pesos del usuario (`PuntuadorAgent`).
6. El sistema recomienda la mejor opción, explicando detalladamente por qué (`RecomendadorAgent`).

---

## 🧩 Agentes Implementados (Resumen Técnico)

| Agente               | Rol                                                                 | Tarea Principal (`tasks.py`) | Herramientas Clave (`tools/`)        |
|----------------------|----------------------------------------------------------------------|-------------------------------|---------------------------------------|
| `LocationAgent`      | Extrae ubicación/transporte del usuario.                             | `location_task`               | `GooglePlacesTool` (usada en `app.py`) |
| `PreferenciasAgent`  | Convierte preferencias en texto a pesos JSON.                       | `preferencias_task`           | -                                     |
| `RecolectorAgent`    | Investiga online cada guardería y rellena perfil JSON.              | `recolector_task`             | `SerperDevTool`, `ScrapeWebsiteTool`, `WebsiteSearchTool` |
| `PuntuadorAgent`     | Calcula puntuación ponderada detallada usando preferencias y datos recogidos. | `puntuador_task`              | `PonderacionTool`                    |
| `RecomendadorAgent`  | Genera informe Markdown final con análisis y recomendación.         | `recomendador_task`           | `FormatterTool` (opcional)           |
*Nota: La orquestación la maneja `CrewAI` directamente en `app.py`.*

---

## 📬 Contribuciones

¡Sugerencias, mejoras o PRs son más que bienvenidos!

---

## 📄 Licencia

MIT © 2025