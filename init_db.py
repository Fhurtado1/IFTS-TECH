""""

import sqlite3 
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import logging


TELEGRAM_TOKEN = '8134964845:AAEJ9_TbXvi4mml5vgpgwYFYa4uXDE2vTis'

# Configuración de logging al inicio del script
logging.basicConfig(level=logging.INFO)

# Ejemplo de mensaje al iniciar el bot
logging.info("Iniciando el bot...")

# Puedes agregar más mensajes en diferentes partes del código
logging.info("Conectando a Telegram...")

# Dentro de una función o después de un comando específico
logging.info("Bot en ejecución, esperando mensajes...")



# Función para inicializar la base de datos y crear la tabla de turnos si no existe
def inicializar_db():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT DEFAULT 'DNI',
                    numero_documento TEXT,
                    nombre TEXT,
                    apellido TEXT,
                    placa TEXT,
                    tipo_vehiculo TEXT,
                    tipo_carga TEXT,
                    fecha TEXT,
                    dia TEXT,
                    hora TEXT
                )''')
    conn.commit()
    conn.close()

# Función para guardar un turno en la base de datos
def guardar_turno(turno):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute('''INSERT INTO turnos (tipo_documento, numero_documento, nombre, apellido, placa, tipo_vehiculo, tipo_carga, fecha, dia, hora)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                 'DNI', turno['numero_documento'], turno['nombre'],
                 turno['apellido'], turno['placa'], turno['tipo_vehiculo'],
                 turno['tipo_carga'], turno['fecha'], turno['dia'], turno['hora']
             ))
    conn.commit()
    conn.close()

# Función para consultar un turno por número de documento
def consultar_turno_por_dni(dni):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("SELECT * FROM turnos WHERE numero_documento = ?", (dni,))
    turnos = c.fetchall()
    conn.close()
    return turnos

# Función para cancelar/borrar un turno por ID
def borrar_turno_por_id(turno_id):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("DELETE FROM turnos WHERE id = ?", (turno_id,))
    conn.commit()
    conn.close()

# Función para consultar disponibilidad en los próximos 7 días
def consultar_disponibilidad_siete_dias():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    
    fecha_hoy = datetime.now().date()
    fecha_limite = fecha_hoy + timedelta(days=7)

    c.execute("SELECT fecha, dia, hora FROM disponibilidad WHERE fecha BETWEEN ? AND ? AND disponible = 1",
              (fecha_hoy.strftime("%Y-%m-%d"), fecha_limite.strftime("%Y-%m-%d")))
    disponibilidad = c.fetchall()
    conn.close()
    return disponibilidad

# Función para manejar el comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenido al turnero de IFTS Tech 16. Selecciona una opción:\n"
        "1. Registrar un nuevo turno\n"
        "2. Consultar un turno existente por DNI\n"
        "3. Verificar disponibilidad de horarios\n"
        "4. Cancelar un turno por DNI\n"
        "Escribe el número de la opción que deseas elegir."
    )
    context.user_data.clear()  # Limpiar los datos previos

# Función para manejar mensajes de texto
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()  # Convertimos a minúsculas para evitar problemas de mayúsculas

    # Verificar si se selecciona la opción de registrar un turno
    if text == "1" and "paso" not in context.user_data:
        context.user_data["accion"] = "registrar_turno"
        context.user_data["paso"] = "numero_documento"
        await update.message.reply_text("Ingresa tu número de documento (DNI):\nEscribe '0' para volver al menú principal.")

    # Consultar un turno existente por DNI
    elif text == "2" and context.user_data.get("paso") is None:
        context.user_data["paso"] = "consulta_dni"
        await update.message.reply_text("Ingresa tu número de documento (DNI) para consultar tus turnos activos:")

    # Verificar disponibilidad de horarios
    elif text == "3" and context.user_data.get("paso") is None:
        disponibilidad = consultar_disponibilidad_siete_dias()
        if disponibilidad:
            mensaje_disponibilidad = "\n".join(
                [f"{i+1}. {fecha} ({dia}) a las {hora}" for i, (fecha, dia, hora) in enumerate(disponibilidad)]
            )
            await update.message.reply_text(
                f"Horarios disponibles para los próximos 7 días:\n{mensaje_disponibilidad}\n\n"
                "Puedes regresar al menú principal escribiendo 'menu'."
            )
        else:
            await update.message.reply_text("No hay horarios disponibles en los próximos 7 días.")

    # Cancelar un turno por DNI
    elif text == "4" and context.user_data.get("paso") is None:
        context.user_data["paso"] = "cancelar_dni"
        await update.message.reply_text("Ingresa tu número de documento (DNI) para cancelar un turno:")

    # Procesar consulta de turno por DNI
    elif context.user_data.get("paso") == "consulta_dni":
        turnos = consultar_turno_por_dni(text)
        if turnos:
            mensaje_turnos = "\n\n".join([
                f"Turno {i+1}:\n- ID: {turno[0]}\n- Tipo de documento: {turno[1]}\n- Número de documento: {turno[2]}\n"
                f"- Nombre: {turno[3]}\n- Apellido: {turno[4]}\n- Placa: {turno[5]}\n"
                f"- Tipo de vehículo: {turno[6]}\n- Tipo de carga: {turno[7]}\n"
                f"- Fecha y hora: {turno[8]} ({turno[9]}) a las {turno[10]}"
                for i, turno in enumerate(turnos)
            ])
            await update.message.reply_text(f"Turnos activos encontrados:\n{mensaje_turnos}\n\nEscribe 'menu' para volver al menú principal.")
        else:
            await update.message.reply_text("No se encontraron turnos activos con ese número de documento. Escribe 'menu' para volver al menú principal.")
        context.user_data.clear()

    # Confirmación de selección de horario
    elif context.user_data.get("paso") == "seleccion_horario":
        try:
            seleccion = int(text) - 1
            if 0 <= seleccion < len(context.user_data["disponibilidad"]):
                fecha, dia, hora = context.user_data["disponibilidad"][seleccion]
                context.user_data.update({"fecha": fecha, "dia": dia, "hora": hora})
                
                # Guardar el turno
                guardar_turno(context.user_data)
                
                # Resumen del turno
                resumen_turno = (
                    f"Resumen del turno:\n"
                    f"- Tipo de documento: DNI\n"
                    f"- Número de documento: {context.user_data['numero_documento']}\n"
                    f"- Nombre: {context.user_data['nombre']}\n"
                    f"- Apellido: {context.user_data['apellido']}\n"
                    f"- Placa: {context.user_data['placa']}\n"
                    f"- Tipo de vehículo: {context.user_data['tipo_vehiculo']}\n"
                    f"- Tipo de carga: {context.user_data['tipo_carga']}\n"
                    f"- Fecha y hora del turno: {fecha} ({dia}) a las {hora}\n\n"
                    "¡Turno registrado exitosamente! Puedes consultar el estado de tu turno en cualquier momento.\n"
                    "Escribe 'menu' para volver al menú principal."
                )
                await update.message.reply_text(resumen_turno)
                context.user_data.clear()
            else:
                await update.message.reply_text("Por favor, selecciona un número válido de la lista.")
        except ValueError:
            await update.message.reply_text("Entrada no válida. Por favor, ingresa el número del horario.")
    
    # Procesar cada paso del registro de turno
    elif context.user_data.get("paso") == "numero_documento":
        if text == "0":
            await start(update, context)  # Volver al menú principal
        elif re.match("^[0-9]+$", text):
            context.user_data["numero_documento"] = text
            context.user_data["paso"] = "nombre"
            await update.message.reply_text("Ingresa tu nombre:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El número de documento solo debe contener números. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "nombre":
        if text == "0":
            context.user_data["paso"] = "numero_documento"
            await update.message.reply_text("Ingresa tu número de documento:")
        elif text.isalpha():
            context.user_data["nombre"] = text
            context.user_data["paso"] = "apellido"
            await update.message.reply_text("Ingresa tu apellido:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El nombre solo debe contener letras. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "apellido":
        if text == "0":
            context.user_data["paso"] = "nombre"
            await update.message.reply_text("Ingresa tu nombre:")
        elif text.isalpha():
            context.user_data["apellido"] = text
            context.user_data["paso"] = "placa"
            await update.message.reply_text("Ingresa tu placa:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El apellido solo debe contener letras. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "placa":
        if text == "0":
            context.user_data["paso"] = "apellido"
            await update.message.reply_text("Ingresa tu apellido:")
        elif re.match("^[a-zA-Z0-9]+$", text):
            context.user_data["placa"] = text
            context.user_data["paso"] = "tipo_vehiculo"
            await update.message.reply_text("Selecciona el tipo de vehículo:\nA. Camioneta\nB. Camión\nC. Semi\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("La placa solo debe contener letras y números. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "tipo_vehiculo":
        if text == "0":
            context.user_data["paso"] = "placa"
            await update.message.reply_text("Ingresa tu placa:")
        elif text in ["a", "b", "c"]:
            tipos_vehiculo = {"a": "Camioneta", "b": "Camión", "c": "Semi"}
            context.user_data["tipo_vehiculo"] = tipos_vehiculo[text]
            context.user_data["paso"] = "tipo_carga"
            await update.message.reply_text("Selecciona el tipo de carga:\nA. Electrónicos\nB. Materia prima\nC. Alimentos\nD. Ropa\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("Por favor, selecciona una opción válida (A, B, C o 0).")

    elif context.user_data.get("paso") == "tipo_carga":
        if text == "0":
            context.user_data["paso"] = "tipo_vehiculo"
            await update.message.reply_text("Selecciona el tipo de vehículo:\nA. Camioneta\nB. Camión\nC. Semi")
        elif text in ["a", "b", "c", "d"]:
            tipos_carga = {"a": "Electrónicos", "b": "Materia prima", "c": "Alimentos", "d": "Ropa"}
            context.user_data["tipo_carga"] = tipos_carga[text]
            context.user_data["paso"] = "seleccion_horario"
            disponibilidad = consultar_disponibilidad_siete_dias()
            if disponibilidad:
                mensaje_disponibilidad = "\n".join(
                    [f"{i+1}. {fecha} ({dia}) a las {hora}" for i, (fecha, dia, hora) in enumerate(disponibilidad)]
                )
                await update.message.reply_text(
                    f"Horarios disponibles para los próximos 7 días:\n{mensaje_disponibilidad}\n\n"
                    "Selecciona un número correspondiente al horario que deseas o escribe '0' para volver al paso anterior."
                )
                context.user_data["disponibilidad"] = disponibilidad
            else:
                await update.message.reply_text("No hay horarios disponibles en los próximos 7 días.")
                context.user_data.clear()

    elif text.lower() == "menu":
        await start(update, context)

# Configuración del bot
def main():
    inicializar_db()  # Inicializar la base de datos al iniciar la aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
"""












































import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import logging
import os
from dotenv import load_dotenv



# Cargar variables de entorno desde .env
load_dotenv()

# Usar el token como variable de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
print("Token:", TELEGRAM_TOKEN)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logging.info("Iniciando el bot...")

# Función para inicializar la base de datos y crear las tablas de turnos y disponibilidad si no existen
def inicializar_db():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT DEFAULT 'DNI',
                    numero_documento TEXT,
                    nombre TEXT,
                    apellido TEXT,
                    placa TEXT,
                    tipo_vehiculo TEXT,
                    tipo_carga TEXT,
                    fecha TEXT,
                    dia TEXT,
                    hora TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS disponibilidad (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    dia TEXT,
                    hora TEXT,
                    disponible INTEGER DEFAULT 1
                )''')
    conn.commit()
    conn.close()
    logging.info("Base de datos inicializada y tablas creadas si no existían.")

# Función para consultar disponibilidad en los próximos 7 días
def consultar_disponibilidad_siete_dias():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    
    fecha_hoy = datetime.now().date()
    fecha_limite = fecha_hoy + timedelta(days=7)

    c.execute("SELECT fecha, dia, hora FROM disponibilidad WHERE fecha BETWEEN ? AND ? AND disponible = 1",
              (fecha_hoy.strftime("%Y-%m-%d"), fecha_limite.strftime("%Y-%m-%d")))
    disponibilidad = c.fetchall()
    conn.close()
    return disponibilidad

# Función para guardar un turno en la base de datos
def guardar_turno(turno):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute('''INSERT INTO turnos (tipo_documento, numero_documento, nombre, apellido, placa, tipo_vehiculo, tipo_carga, fecha, dia, hora)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                 'DNI', turno['numero_documento'], turno['nombre'],
                 turno['apellido'], turno['placa'], turno['tipo_vehiculo'],
                 turno['tipo_carga'], turno['fecha'], turno['dia'], turno['hora']
             ))
    # Marcar la disponibilidad como no disponible después de guardar el turno
    c.execute("UPDATE disponibilidad SET disponible = 0 WHERE fecha = ? AND dia = ? AND hora = ?",
              (turno['fecha'], turno['dia'], turno['hora']))
    conn.commit()
    conn.close()

# Función para manejar el comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Limpiar los datos previos
    await update.message.reply_text(
        "Bienvenido al turnero de IFTS Tech 16. Selecciona una opción:\n"
        "1. Registrar un nuevo turno\n"
        "2. Consultar un turno existente por DNI\n"
        "3. Verificar disponibilidad de horarios\n"
        "4. Cancelar un turno por ID\n"
        "Escribe el número de la opción que deseas elegir."
    )

# Ajuste en la función message_handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    paso_actual = context.user_data.get("paso")

    # Usar expresión regular para capturar "menu" en diferentes formatos
    if re.match(r'^(menu|menú)$', text, re.IGNORECASE):
        await start(update, context)  # Volver al menú principal
        return

    # Opciones de menú
    # Opciones de menú
    if text == "1" and not paso_actual:
        context.user_data["accion"] = "registrar_turno"
        context.user_data["paso"] = "numero_documento"
        await update.message.reply_text("Ingresa tu número de documento (DNI):\nEscribe '0' para volver al menú principal.")

    elif text == "2" and not paso_actual:
        context.user_data["accion"] = "consultar_turno"
        context.user_data["paso"] = "consulta_dni"
        await update.message.reply_text("Por favor, ingresa tu DNI para consultar los turnos existentes o escribe '0' para volver al menú principal.")


    elif text == "3" and not paso_actual:
        context.user_data["accion"] = "verificar_disponibilidad"
        disponibilidad = consultar_disponibilidad_siete_dias()
        if disponibilidad:
            mensaje_disponibilidad = "\n".join(
            [f"{i+1}. {fecha} ({dia}) a las {hora}" for i, (fecha, dia, hora) in enumerate(disponibilidad)]
             )
            await update.message.reply_text(
            f"Horarios disponibles en los próximos 7 días:\n{mensaje_disponibilidad}\n\n"
            "Escribe 'menu' para volver al inicio o 'fin' para cerrar el bot."
             )
        else:
             await update.message.reply_text( "No hay horarios disponibles en los próximos 7 días.\n"
            "Escribe 'menu' para volver al inicio o 'fin' para cerrar el bot.")

    elif text == "4" and not paso_actual:
        context.user_data["accion"] = "cancelar_turno"
        context.user_data["paso"] = "eliminar_dni"
        await update.message.reply_text("Por favor, ingresa tu DNI para ver los turnos y cancelar uno.")

    # Procesamiento de cada paso en el flujo de registro de turno (opción 1)
    elif context.user_data.get("paso") == "numero_documento":
        if text == "0":
            await start(update, context)  # Volver al menú principal
        elif re.match("^[0-9]+$", text):
            context.user_data["numero_documento"] = text
            context.user_data["paso"] = "nombre"
            await update.message.reply_text("Ingresa tu nombre:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El número de documento solo debe contener números. Inténtalo de nuevo.")
    
    # Procesar cada paso del flujo de registro de turno
    elif context.user_data.get("paso") == "numero_documento":
        if text == "0":
            await start(update, context)  # Volver al menú principal
        elif re.match("^[0-9]+$", text):
            context.user_data["numero_documento"] = text
            context.user_data["paso"] = "nombre"
            await update.message.reply_text("Ingresa tu nombre:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El número de documento solo debe contener números. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "nombre":
        if text == "0":
            context.user_data["paso"] = "numero_documento"
            await update.message.reply_text("Ingresa tu número de documento:")
        elif text.isalpha():
            context.user_data["nombre"] = text
            context.user_data["paso"] = "apellido"
            await update.message.reply_text("Ingresa tu apellido:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El nombre solo debe contener letras. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "apellido":
        if text == "0":
            context.user_data["paso"] = "nombre"
            await update.message.reply_text("Ingresa tu nombre:")
        elif text.isalpha():
            context.user_data["apellido"] = text
            context.user_data["paso"] = "placa"
            await update.message.reply_text("Ingresa tu placa:\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("El apellido solo debe contener letras. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "placa":
        if text == "0":
            context.user_data["paso"] = "apellido"
            await update.message.reply_text("Ingresa tu apellido:")
        elif re.match("^[a-zA-Z0-9]+$", text):
            context.user_data["placa"] = text
            context.user_data["paso"] = "tipo_vehiculo"
            await update.message.reply_text("Selecciona el tipo de vehículo:\nA. Camioneta\nB. Camión\nC. Semi\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("La placa solo debe contener letras y números. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "tipo_vehiculo":
        if text == "0":
            context.user_data["paso"] = "placa"
            await update.message.reply_text("Ingresa tu placa:")
        elif text in ["a", "b", "c"]:
            tipos_vehiculo = {"a": "Camioneta", "b": "Camión", "c": "Semi"}
            context.user_data["tipo_vehiculo"] = tipos_vehiculo[text]
            context.user_data["paso"] = "tipo_carga"
            await update.message.reply_text("Selecciona el tipo de carga:\nA. Electrónicos\nB. Materia prima\nC. Alimentos\nD. Ropa\nEscribe '0' para volver al paso anterior.")
        else:
            await update.message.reply_text("Por favor, selecciona una opción válida (A, B, C o 0).")

    elif context.user_data.get("paso") == "tipo_carga":
        if text == "0":
            context.user_data["paso"] = "tipo_vehiculo"
            await update.message.reply_text("Selecciona el tipo de vehículo:\nA. Camioneta\nB. Camión\nC. Semi")
        elif text in ["a", "b", "c", "d"]:
            tipos_carga = {"a": "Electrónicos", "b": "Materia prima", "c": "Alimentos", "d": "Ropa"}
            context.user_data["tipo_carga"] = tipos_carga[text]
            context.user_data["paso"] = "seleccion_horario"
            disponibilidad = consultar_disponibilidad_siete_dias()
            if disponibilidad:
                mensaje_disponibilidad = "\n".join(
                    [f"{i+1}. {fecha} ({dia}) a las {hora}" for i, (fecha, dia, hora) in enumerate(disponibilidad)]
                )
                await update.message.reply_text(
                    f"Horarios disponibles para los próximos 7 días:\n{mensaje_disponibilidad}\n\n"
                    "Selecciona un número correspondiente al horario que deseas o escribe '0' para volver al paso anterior."
                )
                context.user_data["disponibilidad"] = disponibilidad
            else:
                await update.message.reply_text("No hay horarios disponibles en los próximos 7 días.")
                context.user_data.clear()

    elif context.user_data.get("paso") == "seleccion_horario":
        if text == "0":
            context.user_data["paso"] = "tipo_carga"
            await update.message.reply_text("Selecciona el tipo de carga:\nA. Electrónicos\nB. Materia prima\nC. Alimentos\nD. Ropa")
        elif text.isdigit() and 1 <= int(text) <= len(context.user_data["disponibilidad"]):
            seleccion = context.user_data["disponibilidad"][int(text) - 1]
            context.user_data["fecha"] = seleccion[0]
            context.user_data["dia"] = seleccion[1]
            context.user_data["hora"] = seleccion[2]
            context.user_data["paso"] = "confirmacion"
            await update.message.reply_text(
                f"Resumen del turno:\n"
                f"Documento: {context.user_data['numero_documento']}\n"
                f"Nombre: {context.user_data['nombre']} {context.user_data['apellido']}\n"
                f"Placa: {context.user_data['placa']}\n"
                f"Tipo de Vehículo: {context.user_data['tipo_vehiculo']}\n"
                f"Tipo de Carga: {context.user_data['tipo_carga']}\n"
                f"Fecha: {context.user_data['fecha']} ({context.user_data['dia']}) a las {context.user_data['hora']}\n\n"
                "¿Confirmas el registro del turno? (Escribe 'si' para confirmar o '0' para volver al paso anterior)."
            )
        else:
            await update.message.reply_text("Selección inválida. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "confirmacion":
        if text == "0":
            context.user_data["paso"] = "seleccion_horario"
            await update.message.reply_text("Selecciona un número correspondiente al horario que deseas:")
        elif text == "si":
            guardar_turno(context.user_data)
            await update.message.reply_text(
                "Turno registrado exitosamente.\n\n"
                "¿Quieres volver al menú principal o finalizar? Escribe 'menu' para volver al inicio o 'fin' para cerrar el bot."
            )
            context.user_data.clear()
        else:
            await update.message.reply_text("Por favor, responde 'si' para confirmar o '0' para volver.")
    
    elif text == "menu":
        await start(update, context)  # Volver al menú principal

    elif text == "fin":
        await update.message.reply_text("Gracias por contactarnos en IFTS TECH. ¡Hasta luego!")

# Procesamiento de consulta de turnos (Opción 2)
    elif context.user_data.get("paso") == "consulta_dni":
        if re.match("^[0-9]+$", text):
            context.user_data["numero_documento"] = text
            turnos = consultar_turnos_por_dni(text)
            if turnos:
                mensaje_turnos = "\n".join(
                    [f"ID: {t[0]}, Fecha: {t[1]}, Hora: {t[2]}, Vehículo: {t[3]}" for t in turnos]
                )
                await update.message.reply_text(f"Turnos registrados:\n{mensaje_turnos}\n\n"
                                                "Escribe 'menu' para volver al inicio o 'fin' para cerrar el bot.")
            else:
                await update.message.reply_text("No se encontraron turnos con ese DNI.\nEscribe 'menu' para volver al inicio o 'fin' para cerrar el bot.")
            context.user_data.clear()
        else:
            await update.message.reply_text("El DNI solo debe contener números. Inténtalo de nuevo.")

    # Procesamiento de eliminación de turnos (Opción 4)
    elif context.user_data.get("paso") == "eliminar_dni":
        if re.match("^[0-9]+$", text):
            context.user_data["numero_documento"] = text
            turnos = consultar_turnos_por_dni(text)
            if turnos:
                mensaje_turnos = "\n".join(
                    [f"ID: {t[0]}, Fecha: {t[1]}, Hora: {t[2]}, Vehículo: {t[3]}" for t in turnos]
                )
                context.user_data["paso"] = "seleccion_id"
                context.user_data["turnos"] = turnos
                await update.message.reply_text(f"Turnos registrados:\n{mensaje_turnos}\n\n"
                                                "Escribe el ID del turno que deseas cancelar o '0' para volver al menú.")
            else:
                await update.message.reply_text("No se encontraron turnos con ese DNI.\nEscribe 'menu' para volver al inicio o 'fin' para cerrar el bot.")
                context.user_data.clear()
        else:
            await update.message.reply_text("El DNI solo debe contener números. Inténtalo de nuevo.")

    elif context.user_data.get("paso") == "seleccion_id":
        if text == "0":
            await start(update, context)  # Volver al menú principal
        elif re.match("^[0-9]+$", text):
            turno_id = int(text)
            turnos = context.user_data.get("turnos")
            if any(t[0] == turno_id for t in turnos):
                eliminar_turno_por_id(turno_id)
                await update.message.reply_text("Turno eliminado exitosamente.\nEscribe 'menu' para volver al inicio o 'fin' para cerrar el bot.")
                context.user_data.clear()
            else:
                await update.message.reply_text("ID de turno inválido. Inténtalo de nuevo.")
        else:
            await update.message.reply_text("El ID de turno solo debe contener números. Inténtalo de nuevo.")


 # Otros pasos del flujo de registro y confirmación
    elif context.user_data.get("paso") == "confirmacion":
        if text == "0":
            context.user_data["paso"] = "seleccion_horario"
            await update.message.reply_text("Selecciona un número correspondiente al horario que deseas:")
        elif text == "si":
            guardar_turno(context.user_data)
            await update.message.reply_text(
                "Turno registrado exitosamente.\n\n"
                "¿Quieres volver al menú principal o finalizar? Escribe 'menu' para volver al inicio o 'fin' para cerrar el bot."
            )
            context.user_data.clear()
        else:
            await update.message.reply_text("Por favor, responde 'si' para confirmar o '0' para volver.")
    
    elif text == "menu":
        await start(update, context)  # Volver al menú principal

    elif text == "fin":
        await update.message.reply_text("Gracias por usar el bot. ¡Hasta luego!")

# Función para consultar turnos por DNI
def consultar_turnos_por_dni(dni):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("SELECT id, fecha, hora, tipo_vehiculo FROM turnos WHERE numero_documento = ?", (dni,))
    turnos = c.fetchall()
    conn.close()
    return turnos

# Función para eliminar turno por ID
def eliminar_turno_por_id(turno_id):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("DELETE FROM turnos WHERE id = ?", (turno_id,))
    conn.commit()
    conn.close()


# Configuración del bot
def main():
    inicializar_db()  # Inicializar la base de datos al iniciar la aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
