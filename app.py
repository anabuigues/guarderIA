import streamlit as st
import json
import sys
import io
import logging
import os
import builtins # Necesario para monkey-patching print

# --- Configuración Logging AL PRINCIPIO --- 
LOG_FILE = "crew_execution.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                    encoding='utf-8',
                    filemode='w')
logging.critical(f"*** INICIO SCRIPT APP.PY - Logging configurado (mode='w') para: {LOG_FILE} ***") 
# ----------------------------------------

from agents import GuarderiaAgents
from tasks import GuarderiaTasks
from crewai import Crew, Task

from tools.google_places_tool import GooglePlacesTool

# --- Monkey-Patching Print --- 
original_print = builtins.print # Guardar el print original

def print_to_log(*args, **kwargs):
    """Función personalizada que redirige print() a logging.info()."""
    # Formatear el mensaje de forma similar a print
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    # Crear el mensaje como una sola cadena
    message = sep.join(map(str, args))
    # Usar logging.info para escribirlo en el archivo configurado por basicConfig
    # Quitamos el 'end' final para evitar dobles saltos de línea en el log
    logging.info(f"[PRINT]: {message}") 
# --------------------------- 

st.set_page_config(page_title="GuarderIA", layout="wide")
st.title("🎓 GuarderIA - Encuentra la mejor guardería para tu peque")

class GuarderiaCrewRunner:
    def __init__(self, ubicacion, transporte, tiempo_max, texto_preferencias, status_placeholder):
        self.ubicacion = ubicacion
        self.transporte = transporte
        self.tiempo_max = tiempo_max
        self.texto_preferencias = texto_preferencias
        self.status_placeholder = status_placeholder # Puede ser None

    def run(self):
        if self.status_placeholder:
            self.status_placeholder.info("🚀 Iniciando proceso...")
        logging.info("--- Iniciando ejecución del GuarderiaCrewRunner --- ")
        
        agents = GuarderiaAgents()
        tasks = GuarderiaTasks()

        a_ubicacion = agents.location_agent()
        a_preferencias = agents.preferencias_agent()
        a_recolector = agents.recolector_agent()
        a_puntuador = agents.puntuador_agent()
        a_recomendador = agents.recomendador_agent()

        if self.status_placeholder:
            self.status_placeholder.info("🧠 Analizando ubicación y preferencias...")
        texto_usuario = f"Vivo en {self.ubicacion}. Me desplazo en {self.transporte} y no quiero tardar más de {self.tiempo_max} minutos."
        t_ubicacion: Task = tasks.location_task(a_ubicacion, texto_usuario)
        t_preferencias: Task = tasks.preferencias_task(a_preferencias, self.texto_preferencias)

        gpt = GooglePlacesTool()
        if self.status_placeholder:
            self.status_placeholder.info(f"🗺️ Buscando guarderías cercanas a '{self.ubicacion}'...")
        logging.info(f"Buscando guarderías para {self.ubicacion}, {self.transporte}, {self.tiempo_max}min")
        try:
            resultados_guarderias = gpt.run(self.ubicacion, self.transporte, self.tiempo_max)
            guarderias = json.loads(resultados_guarderias)
        except Exception as e:
             logging.error(f"Error durante GooglePlacesTool: {e}", exc_info=True)
             if self.status_placeholder: self.status_placeholder.error(f"Error al buscar en Google Maps: {e}")
             error_msg = f"Error al buscar guarderías en Google Maps: {e}"
             return (False, error_msg) # Devolver fallo y mensaje
        
        if not guarderias:
             logging.warning("No se encontraron guarderías cercanas.")
             if self.status_placeholder: self.status_placeholder.warning("😕 No se encontraron guarderías cercanas con esos criterios.")
             error_msg = "No se encontraron guarderías cercanas con esos criterios."
             return (False, error_msg) # Devolver fallo y mensaje
        else:
             num_guarderias = len(guarderias)
             logging.info(f"Encontradas {num_guarderias} guarderías iniciales.")
             if self.status_placeholder: self.status_placeholder.info(f"✔️ Encontradas {num_guarderias} guarderías. Investigando...")
             
        if self.status_placeholder:
             self.status_placeholder.info(f"🕵️‍♀️ Recopilando información para {num_guarderias} guarderías...")
        t_recolectores = []
        processed_nurseries = set() # Set para guardar tuplas (nombre, direccion) procesadas
        
        for g in guarderias:
            nombre = g.get("nombre", "Nombre Desconocido")
            direccion = g.get("direccion", "Dirección Desconocida")
            website = g.get("website", None) # Obtener la URL si existe
            
            # Crear un identificador único para la guardería
            nursery_id = (nombre, direccion) 
            
            # Si no la hemos procesado ya, crear la tarea y añadirla al set
            if nursery_id not in processed_nurseries:
                logging.info(f"Creando tarea recolector para: {nombre} ({direccion})")
                task = tasks.recolector_task(a_recolector, nombre, direccion, website_url=website)
                t_recolectores.append(task)
                processed_nurseries.add(nursery_id)
            else:
                logging.warning(f"Guardería duplicada encontrada y omitida: {nombre} ({direccion})")

        guarderias_json = json.dumps(guarderias, ensure_ascii=False)

        if self.status_placeholder:
             self.status_placeholder.info("📊 Calculando puntuaciones...")
        t_puntuador: Task = tasks.puntuador_task(agent=a_puntuador, context=[t_preferencias, *t_recolectores])

        if self.status_placeholder:
            self.status_placeholder.info("✍️ Preparando recomendación...")
        t_recomendador: Task = tasks.recomendador_task(agent=a_recomendador, context=[t_puntuador, t_preferencias])

        # --- Definición del Crew (verbose=True) --- 
        crew = Crew(
            agents=[a_ubicacion, a_preferencias, a_recolector, a_puntuador, a_recomendador],
            tasks=[t_ubicacion, t_preferencias, *t_recolectores, t_puntuador, t_recomendador],
            verbose=True, 
            process="sequential",
        )
        
        # --- Ejecución del Crew con MONKEY-PATCHING de print --- 
        if self.status_placeholder: self.status_placeholder.info("⚙️ Ejecutando agentes (con print redirigido a log)...")
        logging.info("===> Preparando para llamar a crew.kickoff() reemplazando print <===")
        
        resultado = None
        success_flag = False
        
        # Reemplazar print global ANTES de llamar a kickoff
        builtins.print = print_to_log
        logging.info("print global reemplazado por print_to_log.")
        
        try:
            # Ejecutar kickoff - cualquier print() interno ahora llamará a print_to_log
            resultado = crew.kickoff()
            logging.info("===> crew.kickoff() finalizado con éxito (print aún reemplazado) <===")
            success_flag = True
            
        except Exception as e:
            logging.exception("### EXCEPCIÓN durante kickoff() del Crew (print reemplazado) ###")
            resultado = f"Error durante la ejecución interna de los agentes: {e}"
            success_flag = False
        finally:
            # RESTAURAR print original SIEMPRE
            builtins.print = original_print
            logging.info("print global restaurado al original.")
            
        # Log final después de restaurar print
        logging.info(f"--- Finalizada ejecución del GuarderiaCrewRunner (Éxito={success_flag}) ---")
        return (success_flag, resultado)

# Interfaz
with st.form("form_guarderia"):
    st.markdown("#### 📍 Introduce tu dirección")
    # Dividir la dirección en campos separados
    calle = st.text_input("🏠 Calle y número", value="")
    codigo_postal = st.text_input("📮 Código Postal", value="")
    ciudad = st.text_input("🏙️ Ciudad", value="")
    
    st.markdown("#### 🚗 Preferencias de desplazamiento")
    transporte = st.selectbox("Medio de transporte habitual", ["andando", "coche", "autobús"])
    tiempo_max = st.slider("⏱️ Tiempo máximo de trayecto (minutos)", 5, 60, 20)

    st.markdown("### 💬 ¿Qué aspectos valoras más a la hora de elegir una guardería?")
    texto_preferencias = st.text_area("Describe con tus palabras lo que es más importante para ti")

    submitted = st.form_submit_button("🔍 Buscar guarderías")

# --- Ya no hay expander de log en la interfaz --- 

if submitted:
    if not calle or not codigo_postal or not ciudad:
        st.error("Por favor, completa todos los campos de la dirección.")
    else:
        ubicacion_completa = f"{calle}, {codigo_postal} {ciudad}"
        st.info("⏳ Preparando para iniciar...") 

        with st.spinner("⚙️ Ejecutando agentes... Esto puede tardar unos minutos."): 
            runner = GuarderiaCrewRunner(ubicacion_completa, transporte, tiempo_max, texto_preferencias, None)
            success, result_or_error = runner.run()
            
            # --- Leer y Mostrar Log (si se genera) --- 
            # Este bloque se mantiene, leerá el archivo con logs de basicConfig Y la captura
            log_content_from_file = ""
            log_expander_read = None # Inicializar
            try:
                logging.info(f"Intentando leer el archivo de log FINAL: {LOG_FILE}") 
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    log_content_from_file = f.read()
                if log_content_from_file:
                     # Crear el expander y placeholder JUSTO ANTES de mostrar
                     log_expander_read = st.expander("🧠 Ver Log de Ejecución", expanded=False)
                     log_placeholder_read = log_expander_read.empty()
                     log_placeholder_read.code(log_content_from_file, language='log')
                     logging.info("Contenido del log mostrado en el expander.")
                else:
                     logging.warning("El archivo de log FINAL se encontró pero estaba vacío.")
                     # Mostrar mensaje si está vacío pero existe
                     st.info("El log de ejecución está vacío.") 
            except FileNotFoundError:
                 logging.error(f"FileNotFoundError al intentar leer {LOG_FILE}")
                 st.warning(f"No se encontró el archivo de log ({LOG_FILE}).")
            except Exception as e:
                 logging.exception("Error inesperado al leer el log:")
                 st.error(f"Error inesperado al leer el archivo de log: {e}")

            # --- Mostrar resultado final --- 
            st.markdown("---")
            st.markdown("## ✅ Resultado Final")

            # Usar la tupla para decidir qué mostrar
            if success:
                resultado = result_or_error # Es el objeto resultado si success=True
                final_output_text = None
                try:
                    # Extraer texto (priorizando .raw)
                    if hasattr(resultado, 'raw') and isinstance(resultado.raw, str):
                        final_output_text = resultado.raw
                    elif isinstance(resultado, str):
                        final_output_text = resultado
                    elif hasattr(resultado, 'result') and isinstance(resultado.result, str):
                        final_output_text = resultado.result
                    
                    if final_output_text is None:
                        logging.warning(f"No se encontró texto extraíble. Convirtiendo objeto a string. Tipo: {type(resultado)}")
                        final_output_text = str(resultado) 
                    
                    # Mostrar con introducción
                    st.markdown("Aquí tienes el resumen generado por los agentes:")
                    st.markdown(final_output_text)
                    logging.info("Resultado final mostrado con éxito.")

                except Exception as e:
                    logging.exception("Excepción al procesar el resultado final para mostrar:")
                    st.error(f"Error al procesar el resultado final para mostrarlo: {e}")
                    st.markdown(f"Resultado bruto: `{str(resultado)[:1000]}...`")
            else:
                # Si success=False, result_or_error es el mensaje de error
                error_message = result_or_error
                st.error(f"**Ocurrió un error durante la ejecución:** {error_message}")
                logging.error(f"Se mostró error al usuario: {error_message}")

# --- Fin Mostrar resultado final ---
