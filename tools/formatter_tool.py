from crewai.tools import BaseTool

import json

class FormatterTool(BaseTool):
    name: str = "FormatterTool"
    description: str = "Toma una lista JSON de guarderías puntuadas y la convierte en una recomendación clara en lenguaje natural."

    def _run(self, ranking_json: str) -> str:
        try:
            # Validar y decodificar JSON de entrada
            try:
                ranking = json.loads(ranking_json)
            except json.JSONDecodeError as e:
                return f"Error al decodificar ranking_json: {e}"
            
            if not isinstance(ranking, list):
                 return "Error: El ranking recibido no es una lista válida."

            if not ranking:
                return "No se encontraron guarderías puntuadas para generar una recomendación."

            # Ordenar por si acaso la herramienta PonderacionTool no lo hizo
            ranking.sort(key=lambda x: x.get("score", 0), reverse=True)

            top_guarderias = ranking[:3] # Tomar las 3 mejores

            texto = "¡Hola! 👋 Hemos analizado las opciones según tus preferencias y aquí tienes las guarderías más destacadas:\n\n"

            for i, g in enumerate(top_guarderias, start=1):
                # Usar .get() para acceso seguro a las claves
                nombre = g.get("nombre", "Nombre Desconocido")
                score = g.get("score", "N/A")
                comentario = g.get("comentario", "Sin comentarios adicionales.")
                texto += f"{i}. **{nombre}** - Puntuación: **{score}**\n   📝 _{comentario}_\n\n"

            if top_guarderias:
                principal_nombre = top_guarderias[0].get("nombre", "la mejor valorada")
                texto += f"✅ Basado en la puntuación, nuestra recomendación principal es **{principal_nombre}**.\n\n"
            
            texto += "💡 Esperamos que esta información te sea útil. Si quieres explorar más a fondo alguna de estas opciones o ajustar los criterios, ¡no dudes en preguntar!"

            return texto

        except Exception as e:
            return f"Error inesperado al generar el formato de resultados: {e}"