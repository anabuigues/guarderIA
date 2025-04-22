from crewai.tools import BaseTool
import json
import re # Importar regex para extraer números

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
                detalles_puntuacion = []

                for criterio, peso in preferencias.items():
                    if not isinstance(peso, (int, float)):
                        continue

                    valor_original = g.get(criterio)
                    puntuacion_base = 0 # Puntuación base (0-5)
                    justificacion = "No aplica o valor no encontrado."
                    sub_justificaciones = [] # Para construir justificaciones compuestas

                    # --- Nueva Lógica de Puntuación Específica ---

                    if criterio == "instalaciones":
                        if isinstance(valor_original, dict):
                            if valor_original.get('patio') is True:
                                puntuacion_base += 2.5
                                sub_justificaciones.append("Tiene patio.")
                            elif valor_original.get('patio') is False:
                                sub_justificaciones.append("No indica tener patio.")
                            else:
                                sub_justificaciones.append("Patio no especificado.")

                            espacios_desc = valor_original.get('espacios', "")
                            if isinstance(espacios_desc, str) and len(espacios_desc.strip()) > 50:
                                puntuacion_base += 1.5
                                sub_justificaciones.append("Descripción detallada de espacios.")
                            elif isinstance(espacios_desc, str) and len(espacios_desc.strip()) > 10:
                                puntuacion_base += 0.5
                                sub_justificaciones.append("Descripción breve de espacios.")

                            aulas_esp = valor_original.get('aulas_especificas', "")
                            if isinstance(aulas_esp, str) and len(aulas_esp.strip()) > 10:
                                puntuacion_base += 1
                                sub_justificaciones.append("Menciona aulas específicas.")

                            justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Información de instalaciones incompleta."
                        else:
                            justificacion = "Formato de datos de instalaciones inesperado."

                    elif criterio == "horario":
                         if isinstance(valor_original, dict):
                             if valor_original.get('apertura') and valor_original.get('cierre'):
                                 puntuacion_base += 2
                                 sub_justificaciones.append(f"Horario {valor_original.get('apertura')}-{valor_original.get('cierre')}.")
                             else:
                                 sub_justificaciones.append("Horario base no especificado.")

                             flex_desc = valor_original.get('flexibilidad', "")
                             if isinstance(flex_desc, str) and len(flex_desc.strip()) > 5:
                                 puntuacion_base += 3 # Más puntos si describe flexibilidad
                                 sub_justificaciones.append("Describe flexibilidad.")
                             elif flex_desc: # Booleano True o string no vacío
                                 puntuacion_base += 1.5
                                 sub_justificaciones.append("Indica flexibilidad.")

                             justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Información de horario incompleta."
                         else:
                             justificacion = "Formato de datos de horario inesperado."

                    elif criterio == "ratio_ninos_cuidadores":
                        ratio_val = None
                        if isinstance(valor_original, dict):
                            # Intentar extraer un número de las claves comunes
                            ratio_str = valor_original.get('1-2') or valor_original.get('2-3') or valor_original.get('0-1') or ""
                            if isinstance(ratio_str, (int, float)):
                                ratio_val = float(ratio_str)
                            elif isinstance(ratio_str, str):
                                nums = re.findall(r"\d+\.?\d*", ratio_str) # Busca números (incluye decimales)
                                if nums:
                                    try:
                                        ratio_val = float(nums[0]) # Toma el primer número encontrado
                                    except ValueError: pass
                        elif isinstance(valor_original, (int, float)): # Si ya viene como número
                            ratio_val = float(valor_original)

                        if ratio_val is not None:
                            # Lógica inversa: Menos ratio es mejor. Min=5 (ideal, 5 pts), Max=15 (peor, 0 pts)
                            min_ratio, max_ratio = 5, 15
                            if ratio_val <= min_ratio:
                                puntuacion_base = 5
                                justificacion = f"Ratio ({ratio_val}) muy bueno (<= {min_ratio})."
                            elif ratio_val >= max_ratio:
                                puntuacion_base = 0
                                justificacion = f"Ratio ({ratio_val}) muy alto (>= {max_ratio})."
                            else:
                                puntuacion_base = 5 * (1 - (ratio_val - min_ratio) / (max_ratio - min_ratio))
                                justificacion = f"Ratio ({ratio_val}) intermedio."
                            puntuacion_base = round(max(0, min(puntuacion_base, 5)), 1)
                        else:
                            justificacion = "Valor de ratio no numérico o no encontrado."

                    elif criterio == "idiomas": # Mantener lógica anterior
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

                    elif criterio == "alimentacion":
                        if isinstance(valor_original, dict):
                            if valor_original.get('cocina_propia') is True:
                                puntuacion_base += 2.5
                                sub_justificaciones.append("Cocina propia.")
                            if valor_original.get('comida_saludable') is True:
                                puntuacion_base += 1
                                sub_justificaciones.append("Comida saludable.")
                            if valor_original.get('menu_adaptable') is True:
                                puntuacion_base += 1
                                sub_justificaciones.append("Menú adaptable.")
                            if valor_original.get('blw_ofrecido') is True:
                                puntuacion_base += 0.5
                                sub_justificaciones.append("Ofrece BLW.")
                            justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Información de alimentación incompleta."
                        else:
                            justificacion = "Formato de datos de alimentación inesperado."

                    elif criterio == "necesidades_individuales":
                         if isinstance(valor_original, dict):
                             if valor_original.get('periodo_adaptacion_flexible') is True:
                                 puntuacion_base += 3
                                 sub_justificaciones.append("Adaptación flexible.")
                             protocolo = valor_original.get('protocolo_siesta', "")
                             if isinstance(protocolo, str) and len(protocolo.strip()) > 5:
                                 puntuacion_base += 2
                                 sub_justificaciones.append("Protocolo siesta descrito.")
                             justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Info necesidades individuales incompleta."
                         else:
                              justificacion = "Formato datos necesidades individuales inesperado."

                    elif criterio == "participacion_padres":
                         if isinstance(valor_original, dict):
                             if valor_original.get('reuniones_periodicas') is True:
                                 puntuacion_base += 2
                                 sub_justificaciones.append("Reuniones periódicas.")
                             if valor_original.get('talleres_padres') is True:
                                 puntuacion_base += 1.5
                                 sub_justificaciones.append("Talleres padres.")
                             if valor_original.get('acceso_observacion') is True:
                                 puntuacion_base += 1.5
                                 sub_justificaciones.append("Acceso observación.")
                             justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Info participación padres incompleta."
                         else:
                              justificacion = "Formato datos participación padres inesperado."

                    elif criterio == "actividades":
                         if isinstance(valor_original, dict):
                             prog_act = valor_original.get('programa_actividades', "")
                             if isinstance(prog_act, str) and len(prog_act.strip()) > 20:
                                 puntuacion_base += 2
                                 sub_justificaciones.append("Programa detallado.")
                             elif isinstance(prog_act, str) and len(prog_act.strip()) > 0:
                                 puntuacion_base += 1
                                 sub_justificaciones.append("Menciona programa.")

                             if valor_original.get('tiempo_aire_libre_diario') is True:
                                 puntuacion_base += 1.5
                                 sub_justificaciones.append("Tiempo aire libre diario.")
                             if valor_original.get('huerto_ecologico') is True:
                                 puntuacion_base += 0.5
                                 sub_justificaciones.append("Huerto.")
                             if valor_original.get('excursiones_regulares') is True:
                                 puntuacion_base += 1
                                 sub_justificaciones.append("Excursiones.")
                             justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Info actividades incompleta."
                         else:
                              justificacion = "Formato datos actividades inesperado."

                    elif criterio == "tecnologia":
                         if isinstance(valor_original, dict):
                             uso_aula = valor_original.get('uso_en_aula', "")
                             if isinstance(uso_aula, str) and len(uso_aula.strip()) > 10:
                                 puntuacion_base += 1.5
                                 sub_justificaciones.append("Describe uso tecnología.")
                             if valor_original.get('app_comunicacion_padres') is True:
                                 puntuacion_base += 3.5 # Bastante importante hoy en día
                                 sub_justificaciones.append("App comunicación padres.")
                             justificacion = " ".join(sub_justificaciones) if sub_justificaciones else "Info tecnología incompleta."
                         else:
                              justificacion = "Formato datos tecnología inesperado."

                    elif criterio == "pedagogia":
                        # Ya no se espera solo string, sino dict
                        if isinstance(valor_original, dict):
                             metodo = valor_original.get('metodo_principal', "")
                             principios = valor_original.get('principios_clave', "")
                             len_metodo = len(metodo.strip()) if isinstance(metodo, str) else 0
                             len_princ = len(principios.strip()) if isinstance(principios, str) else 0

                             if len_metodo > 10:
                                 puntuacion_base += 2.5
                                 sub_justificaciones.append("Método principal descrito.")
                             if len_princ > 10:
                                 puntuacion_base += 2.5
                                 sub_justificaciones.append("Principios clave descritos.")

                             if len_metodo == 0 and len_princ == 0:
                                 justificacion = "Sin descripción de pedagogía."
                             else:
                                 justificacion = " ".join(sub_justificaciones)
                        else:
                            # Mantener lógica para strings si el recolector no devuelve dict
                            if isinstance(valor_original, str):
                                texto_limpio = valor_original.strip()
                                len_texto = len(texto_limpio)
                                if len_texto > 100:
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
                                justificacion = "Formato datos pedagogía inesperado."


                    elif criterio == "precio":
                        precio_val = None
                        if isinstance(valor_original, dict):
                             mensualidad_str = valor_original.get('mensualidad_base', "")
                             if isinstance(mensualidad_str, (int, float)):
                                 precio_val = float(mensualidad_str)
                             elif isinstance(mensualidad_str, str):
                                 # Extraer primer número (puede tener € u otros símbolos)
                                 nums = re.findall(r"\d+\.?\d*", mensualidad_str.replace(',', '.')) # Reemplazar coma decimal
                                 if nums:
                                     try:
                                         precio_val = float(nums[0])
                                     except ValueError: pass
                        elif isinstance(valor_original, (int, float)):
                             precio_val = float(valor_original)

                        if precio_val is not None:
                            # Puntuación inversa (más barato es mejor)
                            min_val, max_val = 300, 700 # Rango ajustado
                            if precio_val <= min_val:
                                puntuacion_base = 5
                                justificacion = f"Precio ({precio_val}€) muy bueno (<= {min_val}€)."
                            elif precio_val >= max_val:
                                puntuacion_base = 0
                                justificacion = f"Precio ({precio_val}€) muy alto (>= {max_val}€)."
                            else:
                                puntuacion_base = 5 * (1 - (precio_val - min_val) / (max_val - min_val))
                                justificacion = f"Precio ({precio_val}€) intermedio."
                            puntuacion_base = round(max(0, min(puntuacion_base, 5)), 1)
                        else:
                            justificacion = "Valor de precio base no numérico o no encontrado."

                    # --- Lógica por Defecto (si no coincide con criterios específicos) ---
                    else:
                        if isinstance(valor_original, bool):
                            puntuacion_base = 5 if valor_original else 0
                            justificacion = f"Indicado como {'Presente' if valor_original else 'Ausente'}."
                        elif isinstance(valor_original, (int, float)):
                            puntuacion_base = round(max(0, min(float(valor_original), 5)), 1)
                            justificacion = f"Valor numérico directo: {valor_original} (puntuado como {puntuacion_base}/5)."
                        elif isinstance(valor_original, str) and valor_original.strip():
                            puntuacion_base = 1.5 # Puntuación más baja por defecto para strings
                            justificacion = f"Texto encontrado: '{valor_original[:50]}...'."
                        elif isinstance(valor_original, list) and valor_original:
                            puntuacion_base = round(max(0, min(len(valor_original) * 0.5, 5)), 1) # Menos puntos por item en lista
                            justificacion = f"Lista con {len(valor_original)} elementos encontrada."
                        # No poner else final para que mantenga justificacion="No aplica o valor no encontrado."

                    # --- Fin Lógica Puntuación ---

                    # Asegurar que la puntuación base está entre 0 y 5
                    puntuacion_base = round(max(0, min(puntuacion_base, 5)), 1)

                    score_parcial = puntuacion_base * peso
                    score_total += score_parcial
                    total_pesos += peso

                    detalles_puntuacion.append({
                        "criterio": criterio,
                        "peso": peso,
                        "valor_original": str(valor_original), # Asegurar string para JSON
                        "puntuacion_base": puntuacion_base,
                        "justificacion": justificacion
                    })

                score_final = round(score_total / total_pesos, 2) if total_pesos > 0 else 0

                resultado = {
                    "nombre": g.get("nombre", "Nombre Desconocido"),
                    "score": score_final,
                    "detalles_puntuacion": detalles_puntuacion
                }
                resultados.append(resultado)

            resultados.sort(key=lambda x: x["score"], reverse=True)

            return json.dumps(resultados, ensure_ascii=False, indent=2)

        except Exception as e:
            import traceback # Importar para log más detallado
            return f"Error inesperado al calcular puntuaciones: {e}\nTraceback: {traceback.format_exc()}"