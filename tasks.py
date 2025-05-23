from crewai import Task

class GuarderiaTasks:

    def location_task(self, agent, texto_usuario):
        return Task(
            description=f"""
            Extrae en formato JSON los siguientes campos desde el siguiente mensaje del usuario:
            ubicacion, transporte y tiempo_max_desplazamiento.

            Mensaje: {texto_usuario}

            Asegúrate de que todos los campos tengan un valor. Si un campo no está claro,
            usa un valor razonable por defecto o indica que falta.
            Retorna **solo** el bloque JSON válido, sin explicaciones adicionales.
            """,
            expected_output="Un JSON con las claves: ubicacion, transporte y tiempo_max_desplazamiento.",
            agent=agent
        )

    def preferencias_task(self, agent, descripcion_usuario):
        return Task(
            description=f"""
            A continuación, tienes una descripción escrita por una familia sobre lo que considera importante en una guardería:

            '{descripcion_usuario}'

            Tu tarea es analizar este texto y asignar una puntuación de importancia para cada uno de los siguientes criterios:
            instalaciones, horario, ratio_ninos_cuidadores, idiomas, alimentacion, necesidades_individuales, participacion_padres, actividades, tecnologia, pedagogia, precio.

            Aplica las siguientes reglas estrictas:
            - Si el usuario indica explícitamente que un criterio es importante para él/ella, asígnale una puntuación de 5.
            - Para cualquier otro caso (el criterio no se menciona, o se menciona sin indicar explícitamente su importancia), asígnale una puntuación de 3.
            
            Devuelve **solo** un bloque JSON válido con los valores (5 o 3 para cada criterio), sin texto introductorio, explicaciones ni formato adicional.
            Ejemplo de formato esperado:
            {{ "instalaciones": 3, "horario": 5, "ratio_ninos_cuidadores": 5, ... }}
            """,
            expected_output="Un único bloque JSON válido con la puntuación (5 o 3) de cada criterio.",
            agent=agent,
            async_execution=True
        )

    # Se añade website_url como parámetro opcional
    def recolector_task(self, agent, nombre, direccion, website_url=None):
        # Construir la descripción de la tarea, indicando si se proporciona URL
        url_info = f"Se ha identificado una posible web oficial: {website_url}" if website_url else "No se ha identificado una web oficial específica de antemano."
        
        return Task(
            description=f"""
            Investiga y completa el perfil detallado de la guardería '{nombre}' en '{direccion}'.
            {url_info} Sigue el flujo de trabajo **persistente y recursivo** indicado en tu `goal`:
            - Prioriza scraping si hay URL. Si falla, ¡NO TE RINDAS!, usa herramientas de búsqueda para info específica (tarifas, horario, equipo...). 
            - Si no hay URL o faltan datos, usa búsqueda web estratégica (`SerperDevTool`, `WebsiteSearchTool`) y luego scraping dirigido si encuentras URLs prometedoras.
            - Intenta extraer valores estructurados (booleanos, números, listas) siempre que sea posible.
            
            El objetivo final es completar todos los campos del siguiente JSON usando información fiable. Si un dato es imposible de encontrar tras investigar razonablemente, déjalo vacío ('') o como `false`.

            Formato JSON esperado a rellenar:
            {{
                "nombre": "{nombre}",
                "direccion": "{direccion}",
                "website": "{website_url if website_url else ''}", // Intentar confirmar o encontrar la URL correcta
                "instalaciones": {{ "espacios": "", "patio": false, "aulas_especificas": "" }},
                "horario": {{ "apertura": "", "cierre": "", "flexibilidad": "" }},
                "ratio_ninos_cuidadores": {{ "0-1": "", "1-2": "", "2-3": "" }}, // Intentar poner números si es posible
                "idiomas": [], // Lista de idiomas ofrecidos
                "alimentacion": {{ "cocina_propia": false, "comida_saludable": false, "menu_adaptable": false, "blw_ofrecido": false }},
                "necesidades_individuales": {{ "periodo_adaptacion_flexible": false, "protocolo_siesta": "" }},
                "participacion_padres": {{ "reuniones_periodicas": false, "talleres_padres": false, "acceso_observacion": false }},
                "actividades": {{ "programa_actividades": "", "tiempo_aire_libre_diario": false, "huerto_ecologico": false, "excursiones_regulares": false }},
                "tecnologia": {{ "uso_en_aula": "", "app_comunicacion_padres": false }},
                "pedagogia": {{ "metodo_principal": "", "principios_clave": "" }},
                "precio": {{ "mensualidad_base": "", "comedor": "", "extras": "" }}, // Intentar poner número en mensualidad_base
                "reseñas_externas": {{ "google_maps_rating": "", "num_reseñas": "", "resumen_sentimiento": "" }}
            }}

            Devuelve **solo** el bloque JSON completado, sin ningún texto adicional antes o después.
            """,
            expected_output="Un único bloque JSON válido con la ficha detallada de la guardería completada, intentando rellenar con valores estructurados (booleanos, números, listas) cuando sea posible.",
            agent=agent
            # async_execution=True # Mantenemos la ejecución asíncrona si es posible
        )

    # Se elimina guarderias_json de los argumentos, se usará el contexto
    def puntuador_task(self, agent, context):
        # Esta tarea depende del contexto (outputs de t_preferencias y t_recolectores)
        # Es crucial que el contexto contenga los resultados de TODAS las tareas recolectoras.
        return Task(
            description=f"""
            Tu misión es calcular la puntuación final ponderada para cada guardería investigada.
            
            Contexto Proporcionado:
            - El contexto contiene el resultado de 'preferencias_task' (un JSON con los pesos de cada criterio).
            - El contexto también contiene los resultados de múltiples tareas 'recolector_task' (una por cada guardería). Cada resultado es un JSON detallado con la información recopilada de esa guardería (incluyendo nombre, dirección, website, instalaciones, etc.).
            
            Tu Tarea:
            1. **Extrae las Preferencias:** Obtén el JSON de preferencias del usuario desde el contexto.
            2. **Extrae los Datos Recopilados:** Reúne TODOS los JSON detallados de las guarderías generados por las tareas 'recolector_task' del contexto. Forma una lista con estos JSONs.
            3. **Usa la Herramienta de Ponderación:** Llama a la herramienta `PonderacionTool`.
               - Pásale la lista de JSONs de guarderías recopilados como primer argumento (`guarderias_json`).
               - Pásale el JSON de preferencias del usuario como segundo argumento (`preferencias_json`).
            4. **Devuelve el Resultado:** La herramienta `PonderacionTool` calculará las puntuaciones y devolverá una lista JSON ordenada. Tu resultado final debe ser **exactamente** esta lista JSON devuelta por la herramienta.

            **IMPORTANTE:** No inventes ni simules datos. Usa la herramienta `PonderacionTool` con los datos reales proporcionados en el contexto.
            Devuelve **solo** la lista JSON resultante de la herramienta, sin explicaciones adicionales.
            """,
            expected_output="Una lista JSON de guarderías ordenadas por puntuación. Cada guardería debe incluir 'nombre', 'score', y 'detalles_puntuacion' (una lista de diccionarios por criterio).",
            context=context,
            agent=agent
            # Nota: output_json podría usarse si definimos un modelo Pydantic para la nueva estructura
        )

    # Se ajusta la descripción para esperar el nuevo formato del puntuador
    def recomendador_task(self, agent, context):
        # Esta tarea depende del contexto (outputs de t_puntuador y t_preferencias)
        return Task(
            description=f"""Analizar en profundidad la lista de guarderías puntuadas y las preferencias del usuario para generar un informe final CLARO, DETALLADO y ÚTIL en formato Markdown. Sigue el proceso detallado y adaptativo de tu `goal`.
            
            Input Clave (Contexto):
            - Resultado de 'puntuador_task': Lista de diccionarios (`nombre`, `score`, `detalles_puntuacion`).
            - Resultado de 'preferencias_task': JSON con pesos de criterios.
            
            Proceso Clave:
            1. Analiza las puntuaciones (`score` y `detalles_puntuacion` con sus `justificacion`).
            2. **Si los datos son pobres** (scores bajos, muchas justificaciones de "no encontrado"), **indícalo claramente** en el informe y recomienda verificación manual, pero aun así presenta el análisis de lo encontrado.
            3. Destaca pros/contras basándote en los criterios importantes (peso 5) y las `puntuacion_base` / `justificacion`.
            4. Escribe una conclusión comparativa y justificada.
            5. Formatea todo en Markdown claro (puedes usar `FormatterTool`).
            
            Output: Devuelve ÚNICAMENTE el informe final en formato Markdown.
            """,
            expected_output="Un informe detallado en formato Markdown. Debe incluir un análisis por guardería (puntuación, pros/contras basados en preferencias y datos disponibles) y una conclusión final comparativa con la recomendación justificada. **Si los datos eran limitados, el informe debe reflejarlo honestamente.**",
            context=context,
            agent=agent
        )
