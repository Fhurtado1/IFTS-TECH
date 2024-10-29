# Usa una imagen de Python
FROM python:3.10

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia todos los archivos de tu bot al contenedor
COPY . .

# Instala las dependencias del bot
RUN pip install -r requirements.txt

# Ejecuta el bot al iniciar el contenedor
CMD ["python", "init_db.py"]

