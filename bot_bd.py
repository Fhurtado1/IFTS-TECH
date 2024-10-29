import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Usar el token como variable de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def init_db():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS disponibilidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT,
            hora TEXT,
            disponible INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            placa TEXT,
            tipo_vehiculo TEXT,
            tipo_operacion TEXT,
            tipo_carga TEXT,
            dia TEXT,
            hora TEXT
        )
    ''')
    dias_y_horas = [("Lunes", "10:00", 1), ("Lunes", "11:00", 1), ("Martes", "10:00", 1), ("Martes", "11:00", 1)]
    c.executemany("INSERT INTO disponibilidad (dia, hora, disponible) VALUES (?, ?, ?)", dias_y_horas)
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido al turnero de IFTS Tech 16. ¿Quieres agregar un turno nuevo o consultar uno existente?")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "agregar turno" in text:
        await update.message.reply_text("Consulta de disponibilidad:")
        disponibilidad = consultar_disponibilidad()
        if disponibilidad:
            mensaje_disponibilidad = "\n".join([f"{dia} a las {hora}" for dia, hora in disponibilidad])
            await update.message.reply_text(f"Horarios disponibles:\n{mensaje_disponibilidad}\n\nSelecciona un día y una hora.")
            context.user_data["accion"] = "agregar_turno"
        else:
            await update.message.reply_text("No hay horarios disponibles.")

    elif context.user_data.get("accion") == "agregar_turno":
        dia, hora = text.split(" a las ")
        context.user_data["dia"] = dia
        context.user_data["hora"] = hora
        await update.message.reply_text("Ingresa tu nombre:")
        context.user_data["paso"] = "nombre"
    
    elif context.user_data.get("paso") == "nombre":
        context.user_data["nombre"] = text
        await update.message.reply_text("Ingresa tu apellido:")
        context.user_data["paso"] = "apellido"
        
    elif context.user_data.get("paso") == "apellido":
        context.user_data["apellido"] = text
        await update.message.reply_text("Ingresa tu placa:")
        context.user_data["paso"] = "placa"

    elif context.user_data.get("paso") == "placa":
        context.user_data["placa"] = text
        await update.message.reply_text("Ingresa el tipo de vehículo:")
        context.user_data["paso"] = "tipo_vehiculo"

    elif context.user_data.get("paso") == "tipo_vehiculo":
        context.user_data["tipo_vehiculo"] = text
        await update.message.reply_text("Selecciona el tipo de operación (1. carga, 2. descarga):")
        context.user_data["paso"] = "tipo_operacion"
        
    elif context.user_data.get("paso") == "tipo_operacion":
        operacion = "carga" if text == "1" else "descarga"
        context.user_data["tipo_operacion"] = operacion
        await update.message.reply_text("Selecciona el tipo de carga (1. electrónicos, 2. materia prima, 3. alimentos, 4. ropa):")
        context.user_data["paso"] = "tipo_carga"
        
    elif context.user_data.get("paso") == "tipo_carga":
        carga = ["electrónicos", "materia prima", "alimentos", "ropa"][int(text) - 1]
        context.user_data["tipo_carga"] = carga
        registrar_turno(context.user_data)
        await update.message.reply_text("¡Turno registrado exitosamente!")
        context.user_data.clear()

def consultar_disponibilidad():
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("SELECT dia, hora FROM disponibilidad WHERE disponible = 1")
    disponibilidad = c.fetchall()
    conn.close()
    return disponibilidad

def registrar_turno(datos):
    conn = sqlite3.connect('turnero.db')
    c = conn.cursor()
    c.execute("INSERT INTO turnos (nombre, apellido, placa, tipo_vehiculo, tipo_operacion, tipo_carga, dia, hora) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (datos["nombre"], datos["apellido"], datos["placa"], datos["tipo_vehiculo"], datos["tipo_operacion"], datos["tipo_carga"], datos["dia"], datos["hora"]))
    conn.commit()
    conn.close()

def main():
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
