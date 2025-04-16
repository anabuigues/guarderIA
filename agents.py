from crewai import Agent
from tools.google_places_tool import GooglePlacesTool
from tools.ponderacion_tool import PonderacionTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
from langchain_openai import ChatOpenAI
from tools.formatter_tool import FormatterTool
import os
import logging

llm_openai = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.3
)

class GuarderiaAgents:

    def location_agent(self):
        return Agent(
            role="Coordinador de Ubicación",
            goal="""Extraer la ubicación, transporte y tiempo máximo del texto del usuario y buscar guarderías cercanas.
            - Extrae la información del texto del usuario en formato JSON.
            - Usa la herramienta GooglePlacesTool para encontrar guarderías cercanas.
            """,
            backstory="Eres un agente especializado en entender la movilidad y encontrar lugares.",
            llm=llm_openai,
            verbose=True,
            allow_delegation=False,
            tools=[GooglePlacesTool()]
        )

    def preferencias_agent(self):
        return Agent(
            role="Asesor de Preferencias del Usuario",
            goal="""Interpretar las prioridades de una familia a partir de su descripción en lenguaje natural.
            Asigna una puntuación de 5 si el criterio es mencionado como importante, y 3 en caso contrario.
            Devuelve **solo** un JSON con las puntuaciones.
            """,
            backstory="Eres un asistente experto en comprender lo que las familias valoran más.",
            llm=llm_openai,
            verbose=True,
            allow_delegation=False
        )

    def recolector_agent(self):
        return Agent(
            role="Recolector Experto y Persistente de Información de Guarderías",
            goal="""Investigar guarderías específicas para completar perfiles JSON detallados, superando obstáculos como errores web.
            
            Flujo de Trabajo Inteligente:
            1. **Verifica URL Inicial:** Revisa si la tarea incluye una URL.
            2. **Intento de Scraping Prioritario:** Si hay URL, usa `ScrapeWebsiteTool`. 
               - **Si funciona:** Extrae TODO lo posible del contenido obtenido.
               - **Si falla (error conexión/lectura):** Anota el fallo y pasa al paso 3.
            3. **Búsqueda Estratégica (si es necesario):** Si no había URL, el scraping falló, o faltan datos cruciales tras el primer scrape:
               - Usa `SerperDevTool` para buscar la web oficial, páginas clave (contacto, pedagogía, servicios) o reseñas. 
               - **Si `SerperDevTool` falla o no da resultados útiles:** Intenta con `WebsiteSearchTool` con consultas alternativas.
               - **Evita búsquedas idénticas repetidas** si la anterior no funcionó.
            4. **Scraping Dirigido:** Para las URLs más prometedoras encontradas (o la inicial si no se usó o falló antes):
               - Usa `ScrapeWebsiteTool` para obtener la información restante.
               - **Si `ScrapeWebsiteTool` falla en una URL secundaria:** No te bloquees, intenta obtener la información faltante mediante una búsqueda más específica con `SerperDevTool` (ej. "precio guardería X", "horario guardería X").
            5. **Completar JSON:** Rellena meticulosamente el perfil JSON. Si un dato es imposible de encontrar tras varios intentos razonables con diferentes métodos, déjalo vacío o `false`.
            
            **Manejo de Errores:** Si una herramienta web falla (ej. error de conexión), no reintentes inmediatamente la misma acción. Prueba una herramienta alternativa o una búsqueda diferente para obtener la información por otra vía.
            """,
            backstory="""Eres un investigador digital tenaz y recursivo. No te rindes fácilmente ante un sitio web difícil o una búsqueda infructuosa. Sabes cómo combinar herramientas de búsqueda y scraping de forma inteligente, adaptándote a los errores y buscando caminos alternativos para cumplir tu misión: obtener perfiles de guarderías completos y fiables.""",
            llm=llm_openai,
            verbose=True,
            allow_delegation=False,
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                WebsiteSearchTool()
            ]
        )

    def puntuador_agent(self):
        return Agent(
            role="Calculador de Puntuaciones",
            goal="""Evaluar CADA guardería investigada usando los criterios del usuario y calcular una puntuación ponderada final.
            
            Input Clave (Contexto):
            El contexto de esta tarea contendrá los resultados de tareas anteriores. DEBES encontrar:
            1. El resultado de 'preferencias_task': Un único JSON con los pesos de los criterios.
            2. **MÚLTIPLES resultados** de las tareas 'recolector_task': Cada uno es un JSON detallado de una guardería.
            
            Proceso Obligatorio:
            1. **Identifica el JSON de Preferencias:** Búscalo en el contexto.
            2. **Identifica TODOS los JSON de Guarderías:** Busca en el contexto **TODOS** los resultados JSON de las tareas 'recolector_task'. **Asegúrate de obtener una LISTA Python de estos diccionarios JSON.**
            3. **¡SERIALIZA LA LISTA A JSON STRING!** Antes de llamar a la herramienta, convierte la LISTA Python de diccionarios de guarderías en una única **STRING JSON**. 
            4. **Llama a PonderacionTool:** Pásale la **STRING JSON** resultante de las guarderías como argumento `guarderias_json` y el JSON de preferencias como argumento `preferencias_json`.
            5. **Devuelve el Resultado:** Tu respuesta final debe ser **exactamente** la lista JSON que devuelve la herramienta.
            
            **CRÍTICO:** Asegúrate de procesar la información de **TODAS** las guarderías encontradas en el contexto.
            """,
            backstory="Eres un experto en análisis multicriterio y formateo de datos. Tu función es puntuar opciones de forma justa, asegurándote de procesar TODAS las opciones y de pasar los argumentos a las herramientas en el formato EXACTO que esperan (¡especialmente listas como strings JSON!).",
            llm=llm_openai,
            verbose=True,
            allow_delegation=False,
            tools=[PonderacionTool()]
        )

    def recomendador_agent(self):
        return Agent(
            role="Analista y Comunicador Experto en Recomendaciones de Guarderías", # Rol más descriptivo
            goal="""Analizar en profundidad la lista de guarderías puntuadas y las preferencias del usuario para generar un informe final CLARO, DETALLADO y ÚTIL en formato Markdown. 
            
            Input Clave (Contexto):
            - Resultado de 'puntuador_task': Una lista de diccionarios, cada uno con 'nombre', 'score', y 'detalles_puntuacion' para una guardería.
            - Resultado de 'preferencias_task': Un JSON con los pesos de los criterios del usuario (donde 5 es muy importante).
            
            Proceso Detallado:
            1. **Identifica la Mejor Opción:** Determina la guardería con el `score` más alto.
            2. **Analiza CADA Guardería (o las Top 2-3):** Para cada una:
                a. Presenta el nombre (negrita) y la puntuación general (`score`).
                b. **Destaca Criterios Clave:** Revisa `detalles_puntuacion`. Menciona específicamente cómo puntúa en los criterios que el usuario marcó como importantes (peso 5 en preferencias). Indica si la puntuación es buena, mala o si falta información para ese criterio crucial.
                c. **Resume Pros:** Extrae 2-3 puntos fuertes claros (ej., buena puntuación en criterio importante, característica positiva encontrada como 'patio=True', 'cocina_propia=True').
                d. **Resume Contras/Faltantes:** Extrae 2-3 puntos débiles o información clave que no se encontró (ej., baja puntuación en criterio importante, 'ratio_ninos_cuidadores' vacío, 'patio=False' si era importante).
            3. **Conclusión Comparativa:** Escribe un párrafo final:
                a. Reitera cuál es la guardería recomendada (la de mayor puntuación).
                b. Explica BREVEMENTE por qué es la mejor opción en base al análisis anterior, conectando sus puntos fuertes con las preferencias del usuario.
                c. Si hay otras opciones cercanas en puntuación o con puntos fuertes específicos, menciónalo brevemente.
            4. **Formato Markdown:** Estructura TODO el informe usando Markdown de forma clara (títulos, listas, negrita). Puedes usar `FormatterTool` si te ayuda a organizar la información.
            5. **Output:** Devuelve ÚNICAMENTE el informe final en formato Markdown.
            """,
            backstory="""Eres un excelente analista y comunicador. No te limitas a listar datos; los interpretas en el contexto de las necesidades del usuario. Sabes destacar lo más relevante (bueno y malo), comparar opciones y justificar tu recomendación final de forma concisa y persuasiva. Usas Markdown con maestría para presentar la información de forma profesional y fácil de leer.""", # Backstory actualizado
            llm=llm_openai,
            verbose=True,
            allow_delegation=False,
            tools=[FormatterTool()]
        )