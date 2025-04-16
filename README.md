# 🧠 GuarderIA - Asistente Inteligente para Elegir Guardería

GuarderIA es una aplicación impulsada por agentes de IA que ayuda a familias a encontrar la mejor guardería para sus hijos, según sus preferencias, ubicación y prioridades.

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
```

---

## 🖥️ Ejecutar la app en Streamlit

```bash
streamlit run app_streamlit_final.py
```

---

## ✨ Qué hace GuarderIA

1. El usuario describe lo que valora en una guardería
2. El sistema busca guarderías cercanas (Google Maps)
3. Cada guardería es analizada por un agente especializado
4. Las guarderías son puntuadas en función de las prioridades del usuario
5. El sistema recomienda la mejor opción, explicando por qué

---

## 🧩 Agentes implementados

| Agente               | Rol                                                                 |
|----------------------|----------------------------------------------------------------------|
| Planner              | Orquestador general del flujo jerárquico                             |
| LocationAgent        | Interpreta la ubicación, transporte y tiempo máximo                 |
| PreferenciasAgent    | Extrae puntuaciones desde texto libre del usuario                   |
| RecolectorAgent      | Busca información detallada online sobre cada guardería             |
| PuntuadorAgent       | Calcula una puntuación ponderada para cada centro                   |
| RecomendadorAgent    | Genera la recomendación final más adecuada para la familia          |

---

## 🧪 Testeo

Puedes lanzar tests individuales de agentes desde `/tests`.

---

## 📬 Contribuciones

¡Sugerencias, mejoras o PRs son más que bienvenidos!

---

## 📄 Licencia

MIT © 2025