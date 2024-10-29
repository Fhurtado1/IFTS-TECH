#Sistema de Gestión de Turnos para Plantas Logísticas
Descripción
Este proyecto es un bot de Telegram diseñado para gestionar turnos en plantas logísticas, permitiendo a los usuarios registrar, consultar, verificar disponibilidad y cancelar turnos mediante la aplicación de mensajería.

Características
Registro de Turnos: Los usuarios pueden registrar un turno especificando detalles como su identificación, tipo de vehículo y tipo de carga.
Consulta de Turnos: Permite a los usuarios consultar los turnos registrados mediante su número de documento.
Verificación de Disponibilidad: Muestra los horarios disponibles en los próximos 7 días.
Cancelación de Turnos: Los usuarios pueden cancelar turnos previamente registrados.
Tecnologías Utilizadas
Python: Lenguaje principal para la lógica del bot.
SQLite: Base de datos para almacenar información de turnos y disponibilidad.
Telegram Bot API: Para la comunicación con los usuarios a través de Telegram.
dotenv: Para gestionar las variables de entorno y proteger el token de acceso del bot.
Instalación
Clona este repositorio:

bash
Copiar código
git clone https://github.com/tu_usuario/nombre_del_repositorio.git
cd nombre_del_repositorio
Crea un entorno virtual y actívalo (opcional pero recomendado):

bash
Copiar código
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
Instala las dependencias:

bash
Copiar código
pip install -r requirements.txt
Configura el archivo .env:

Crea un archivo llamado .env en la raíz del proyecto y añade la siguiente línea:
plaintext
Copiar código
TELEGRAM_TOKEN=tu_token_de_telegram
Nota: No incluyas el archivo .env en el repositorio para proteger tu token.
Inicia el bot:

bash
Copiar código
python nombre_del_archivo_principal.py
Uso
/start: Inicia el bot y muestra el menú de opciones.
1: Registrar un nuevo turno.
2: Consultar un turno existente por DNI.
3: Verificar disponibilidad de horarios en los próximos 7 días.
4: Cancelar un turno por ID.
Consideraciones de Seguridad
El archivo .env contiene el token de acceso al bot de Telegram y no debe compartirse públicamente.
El archivo .gitignore incluye .env para evitar que se suba accidentalmente al repositorio.
Próximas Mejoras
Notificaciones de Recordatorio: Enviar recordatorios automáticos de turnos a los usuarios.
Interfaz Web: Añadir una interfaz web para facilitar el acceso a los administradores.
Informes y Estadísticas: Generación de informes de uso y estadísticas de disponibilidad.
