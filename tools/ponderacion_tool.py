from crewai.tools import BaseTool
import json

class PonderacionTool(BaseTool):
    name: str = "PonderacionTool"
    description: str = "Calcula la puntuación ponderada de una lista de guarderías según los criterios del usuario."

    def _run(self, guarderias_json: str, preferencias_json: str) -> str:
        try:
            try:
                guarderias = json.loads(guarderias_json)
            except json.JSONDecodeError as e:
                return f"Error al decodificar guarderias_json: {e}"
            try:
                preferencias = json.loads(preferencias_json)
            except json.JSONDecodeError as e:
                return f"Error al decodificar preferencias_json: {e}"

            if not isinstance(guarderias, list):
                return "Error: guarderias_json debe ser una lista."
            if not isinstance(preferencias, dict):
                return "Error: preferencias_json debe ser un diccionario."

            resultados = []
            for g in guarderias:
                if not isinstance(g, dict):
                    continue

                score_total = 0
                total_pesos = 0
                # Crear lista para guardar los detalles de puntuación por criterio
                detalles_puntuacion = []

                for criterio, peso in preferencias.items():
                    if not isinstance(peso, (int, float)):
                        continue 
                    
                    valor_original = g.get(criterio) # Guardar valor original
                    puntuacion_base = 0 # Puntuación antes de aplicar peso (escala 0-5)
                    justificacion = "No aplica o valor no encontrado." # Justificación por defecto

                    # --- Lógica de Puntuación Específica (calcula puntuacion_base y justificacion) ---
                    if criterio == "precio":
                        if isinstance(valor_original, (int, float)):
                            min_val, max_val = 200, 800 
                            if valor_original <= min_val: 
                                puntuacion_base = 5
                                justificacion = f"Precio ({valor_original}€) igual o inferior al ideal ({min_val}€)."
                            elif valor_original >= max_val: 
                                puntuacion_base = 0
                                justificacion = f"Precio ({valor_original}€) igual o superior al máximo ({max_val}€)."
                            else: 
                                puntuacion_base = 5 * (1 - (valor_original - min_val) / (max_val - min_val))
                                justificacion = f"Precio ({valor_original}€) dentro del rango, puntuación inversa."
                            puntuacion_base = round(max(0, min(puntuacion_base, 5)), 1)
                        else:
                            justificacion = "Valor de precio no numérico."
                            
                    elif criterio == "ratio_ninos_cuidadores":
                        if isinstance(valor_original, (int, float)):
                            # CORRECCIÓN: Asumiendo que MÁS niños por cuidador es PEOR. 
                            # Si ratio=1 es ideal (0 pts), ratio=5 es malo (5 pts). ¡La fórmula estaba invertida antes!
                            # Nueva lógica: Menos ratio es mejor. Min=5 (ideal, 5 pts), Max=15 (peor, 0 pts)
                            min_ratio, max_ratio = 5, 15 
                            if valor_original <= min_ratio:
                                puntuacion_base = 5
                                justificacion = f"Ratio ({valor_original}) muy bueno (<= {min_ratio})."
                            elif valor_original >= max_ratio:
                                puntuacion_base = 0
                                justificacion = f"Ratio ({valor_original}) muy alto (>= {max_ratio})."
                            else:
                                # Interpolación lineal inversa: a más ratio, menos puntos
                                puntuacion_base = 5 * (1 - (valor_original - min_ratio) / (max_ratio - min_ratio))
                                justificacion = f"Ratio ({valor_original}) intermedio."
                            puntuacion_base = round(max(0, min(puntuacion_base, 5)), 1)
                        else:
                             justificacion = "Valor de ratio no numérico."

                    elif criterio == "idiomas":
                        num_items = 0
                        if isinstance(valor_original, list): num_items = len(valor_original)
                        elif isinstance(valor_original, (int, float)): num_items = int(valor_original)
                        
                        if num_items == 1: 
                            puntuacion_base = 2
                            justificacion = f"Ofrece 1 idioma ({valor_original})."
                        elif num_items == 2: 
                            puntuacion_base = 4
                            justificacion = f"Ofrece 2 idiomas ({valor_original})."
                        elif num_items >= 3: 
                            puntuacion_base = 5
                            justificacion = f"Ofrece 3 o más idiomas ({valor_original})."
                        else:
                             justificacion = "No se especifican idiomas."

                    elif criterio in ["pedagogia", "descripcion", "proyecto_educativo"]:
                        if isinstance(valor_original, str):
                            texto_limpio = valor_original.strip()
                            len_texto = len(texto_limpio)
                            if len_texto > 100: # Aumentamos umbral para descripción detallada
                                puntuacion_base = 4.5 
                                justificacion = f"Descripción detallada encontrada ({len_texto} caracteres)."
                            elif len_texto > 20: 
                                puntuacion_base = 3
                                justificacion = f"Descripción breve encontrada ({len_texto} caracteres)."
                            elif len_texto > 0:
                                 puntuacion_base = 1.5
                                 justificacion = "Descripción muy corta encontrada."
                            else:
                                justificacion = "Sin descripción proporcionada."
                        else:
                            justificacion = "Valor no textual para descripción."

                    else: # Lógica por defecto mejorada
                        if isinstance(valor_original, bool):
                            puntuacion_base = 5 if valor_original else 0
                            justificacion = f"Indicado como {'Presente' if valor_original else 'Ausente'}."
                        elif isinstance(valor_original, (int, float)):
                            # Asume numérico directo (más es mejor), acotado 0-5
                            puntuacion_base = round(max(0, min(float(valor_original), 5)), 1)
                            justificacion = f"Valor numérico directo: {valor_original} (puntuado como {puntuacion_base}/5)."
                        elif isinstance(valor_original, str) and valor_original.strip():
                            puntuacion_base = 3 
                            justificacion = f"Texto encontrado: '{valor_original[:50]}...'." # Mostrar inicio del texto
                        elif isinstance(valor_original, list) and valor_original:
                            puntuacion_base = min(len(valor_original), 5)
                            justificacion = f"Lista con {len(valor_original)} elementos encontrada."
                        else:
                             justificacion = f"Valor '{valor_original}' no evaluable con reglas por defecto."
                    # --- Fin Lógica Puntuación ---

                    score_parcial = puntuacion_base * peso
                    score_total += score_parcial
                    total_pesos += peso
                    
                    # Guardar detalle del criterio
                    detalles_puntuacion.append({
                        "criterio": criterio,
                        "peso": peso,
                        "valor_original": str(valor_original), # Convertir a string para asegurar serialización JSON
                        "puntuacion_base": puntuacion_base,
                        "justificacion": justificacion
                    })

                # Evitar división por cero si todos los pesos son 0
                score_final = round(score_total / total_pesos, 2) if total_pesos > 0 else 0
                
                # Crear el diccionario de resultado para esta guardería
                resultado = {
                    "nombre": g.get("nombre", "Nombre Desconocido"),
                    "score": score_final,
                    "detalles_puntuacion": detalles_puntuacion # Incluir la lista de detalles
                }
                resultados.append(resultado)

            # Ordenar resultados por score descendente
            resultados.sort(key=lambda x: x["score"], reverse=True)

            return json.dumps(resultados, ensure_ascii=False, indent=2)

        except Exception as e:
            # Captura más genérica para errores inesperados
            return f"Error inesperado al calcular puntuaciones: {e}"