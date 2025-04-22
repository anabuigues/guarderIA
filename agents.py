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
    model="o3-mini",
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
            
            Flujo de Trabajo Inteligente y Persistente:
            1. **Verifica URL Inicial:** Revisa si la tarea incluye una URL.
            2. **Intento de Scraping Prioritario:** Si hay URL, usa `ScrapeWebsiteTool`.
               - **Si funciona:** Extrae TODO lo posible del contenido, priorizando valores estructurados (booleanos, números, listas) sobre texto genérico.
               - **Si falla (error conexión/lectura/otro):** ¡NO TE RINDAS! Anota el fallo y pasa al paso 3. No reintentes el scraping inmediatamente en la misma URL.
            3. **Búsqueda Estratégica (si no había URL, scraping falló, o faltan datos clave):**
               - Usa `SerperDevTool` para buscar la web oficial, páginas clave (contacto, pedagogía, servicios, tarifas, equipo) o reseñas.
               - **Si `SerperDevTool` falla o no da resultados útiles:** Intenta con `WebsiteSearchTool` con consultas alternativas y más específicas (ej. "precio guardería X", "horario guardería X", "equipo guardería X").
               - **Evita búsquedas idénticas repetidas.**
            4. **Scraping Dirigido (si se encontraron nuevas URLs):** Para las URLs más prometedoras encontradas:
               - Usa `ScrapeWebsiteTool` para obtener la información restante. Intenta extraer datos específicos.
               - **Si `ScrapeWebsiteTool` falla en una URL secundaria:** No te bloquees. Intenta obtener la información faltante mediante una búsqueda más específica con `SerperDevTool` o `WebsiteSearchTool`.
            5. **Completar JSON:** Rellena meticulosamente el perfil JSON. Intenta dar formato a los valores (ej. `True`/`False` para booleanos, números para ratios/precios si es posible). Si un dato es imposible de encontrar tras varios intentos razonables con diferentes métodos, déjalo vacío o `false`.
            
            **Manejo de Errores Clave:** Si una herramienta web falla, prueba una herramienta alternativa o una búsqueda diferente para obtener la información por otra vía. Tu objetivo es ser persistente y recursivo.
            """,
            backstory="""Eres un investigador digital tenaz y recursivo. No te rindes fácilmente ante un sitio web difícil o una búsqueda infructuosa. Sabes cómo combinar herramientas de búsqueda y scraping de forma inteligente, adaptándote a los errores y buscando caminos alternativos. Priorizas obtener datos estructurados y verificables para cumplir tu misión: obtener perfiles de guarderías completos y fiables.""",
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
            role="Analista y Comunicador Experto en Recomendaciones de Guarderías",
            goal="""Analizar en profundidad la lista de guarderías puntuadas y las preferencias del usuario para generar un informe final CLARO, DETALLADO y ÚTIL en formato Markdown. 
            
            Input Clave (Contexto):
            - Resultado de 'puntuador_task': Una lista de diccionarios, cada uno con 'nombre', 'score', y 'detalles_puntuacion' para una guardería.
            - Resultado de 'preferencias_task': Un JSON con los pesos de los criterios del usuario (donde 5 es muy importante).
            
            Proceso Detallado y Adaptativo:
            1. **Identifica la Mejor Opción:** Determina la guardería con el `score` más alto.
            2. **Analiza CADA Guardería (o las Top 2-3):** Para cada una:
                a. Presenta el nombre (negrita) y la puntuación general (`score`).
                b. **Destaca Criterios Clave:** Revisa `detalles_puntuacion`. Menciona específicamente cómo puntúa en los criterios que el usuario marcó como importantes (peso 5). Usa la `justificacion` para explicar si la puntuación es buena, mala o si falta información (`puntuacion_base: 0`).
                c. **Resume Pros:** Extrae 2-3 puntos fuertes claros (ej., buena `puntuacion_base` en criterio importante, característica positiva confirmada como `patio=True`, `cocina_propia=True`).
                d. **Resume Contras/Faltantes:** Extrae 2-3 puntos débiles o información clave que no se encontró (ej., baja `puntuacion_base` en criterio importante, `justificacion` indicando falta de datos para ratio o precio, `patio=False` si era importante).
            3. **Manejo de Datos Pobres:** Si TODAS las guarderías tienen un `score` bajo (ej. < 0.5) o si en `detalles_puntuacion` predominan las justificaciones de "no evaluable" o "no encontrado" para criterios importantes:
                a. **Indícalo claramente al principio del informe:** "La información encontrada era limitada o difícil de evaluar automáticamente para varios criterios importantes. Las puntuaciones son bajas y la recomendación se basa en datos parciales."
                b. **Aun así, presenta el análisis:** Describe lo que sí se pudo encontrar (pros/contras limitados) para las top 1-2 guarderías.
                c. **Sugiere acciones:** Recomienda al usuario verificar manualmente la información faltante (ej. contactar directamente para preguntar por ratio o precios).
            4. **Conclusión Comparativa:** Escribe un párrafo final:
                a. Reitera cuál es la guardería recomendada (la de mayor puntuación, incluso si es baja).
                b. Explica BREVEMENTE por qué es la mejor opción *según los datos disponibles*, conectando sus puntos fuertes (si los hay) con las preferencias del usuario.
                c. Si hay otras opciones cercanas en puntuación o con puntos fuertes específicos, menciónalo.
            5. **Formato Markdown:** Estructura TODO el informe usando Markdown de forma clara (títulos, listas, negrita). **Considera usar `FormatterTool`** para ayudarte a organizar la información y asegurar un buen formato.
            6. **Output:** Devuelve ÚNICAMENTE el informe final en formato Markdown.
            """,
            backstory="""Eres un excelente analista y comunicador. No te limitas a listar datos; los interpretas en el contexto de las necesidades del usuario y *la calidad de los datos disponibles*. Sabes destacar lo más relevante (bueno y malo), comparar opciones y justificar tu recomendación final de forma concisa, persuasiva y *honesta sobre las limitaciones*. Usas Markdown con maestría (y puedes apoyarte en `FormatterTool`) para presentar la información de forma profesional y fácil de leer.""",
            llm=llm_openai,
            verbose=True,
            allow_delegation=False,
            tools=[FormatterTool()]
        )