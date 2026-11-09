# Control de Asistencia por Reconocimiento Facial

Proyecto para la práctica de Construcción de Software (UNEMI).
Detecta rostros con OpenCV y registra asistencia automáticamente al
reconocer a cada estudiante previamente registrado, organizada por
carrera, curso, materia y horario de clase.

**Stack:** Django + OpenCV (cv2 + LBPH) + PostgreSQL (Neon).
No se descarga ningún modelo externo: el detector (Haar Cascade) y el
reconocedor (LBPH) vienen incluidos en `opencv-contrib-python`.

## 1. Requisitos previos
- Python 3.10+
- Una base de datos PostgreSQL (por ejemplo, un proyecto en Neon)
- Cámara web

## 2. Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac
# Edita .env con tus credenciales reales de PostgreSQL/Neon y una SECRET_KEY propia.

# 4. Migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Crear usuario profesor
python manage.py createsuperuser

# 6. Ejecutar el servidor
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` e inicia sesión con el usuario creado.

## 3. Configurar Carreras, Materias, Cursos y Horarios
Antes de registrar estudiantes y tomar asistencia, entra a
`http://127.0.0.1:8000/admin/` (con tu usuario profesor) y crea, en este
orden:
1. **Carreras** (ej. "Software")
2. **Materias** (ej. "Construcción de Software", asociada a una carrera)
3. **Cursos** (ej. "Quinto A", asociado a una carrera)
4. **Horarios de clase** (ej. Curso "Quinto A" + Materia "Construcción de
   Software" + día "Lunes" + hora de inicio/fin)

Esto permite que la asistencia se organice por carrera, curso y materia,
y que cada día sea un registro nuevo e independiente por cada sesión de
clase (horario).

## 4. Flujo de uso diario
1. **Estudiantes → Registrar estudiante**: ingresa código, nombre y el
   curso al que pertenece; luego la cámara toma automáticamente 15 fotos
   del rostro.
2. Al completar las fotos, pulsa **"Entrenar modelo"** (esto puede repetirse
   cada vez que agregues un estudiante nuevo).
3. **Tomar asistencia**: primero elige el horario de clase (curso +
   materia + día + hora), luego abre la cámara en vivo. Cuando reconoce a
   un estudiante, marca su asistencia para esa sesión y ese día
   automáticamente (una sola vez por día y por horario, no se duplica).
4. **Historial**: consulta todas las asistencias tomadas, con filtros por
   fecha, carrera, curso, materia o nombre/código de estudiante. Desde
   ahí puedes exportar los resultados filtrados a **Excel** o **PDF**.

## 5. Decisiones de seguridad
- Todas las vistas (excepto el login) requieren sesión iniciada **y**
  que el usuario sea `staff` (profesor), evitando que cualquier
  visitante registre estudiantes o vea asistencias.
- Las fotos de rostros y el modelo entrenado se guardan en `face_data/`,
  **fuera** de las carpetas servidas públicamente (`static/`/`media/`),
  para que nunca queden accesibles por URL.
- Protección CSRF activa en todos los formularios y llamadas AJAX.
- Las imágenes recibidas por la cámara se validan (tipo y tamaño máximo)
  antes de procesarse, para evitar cargas maliciosas.
- Credenciales de base de datos y `SECRET_KEY` se leen desde `.env`
  (nunca quedan escritas en el código ni se suben a GitHub).
- `face_data/` y `.env` están en `.gitignore`: los datos biométricos de
  los estudiantes nunca se suben al repositorio.
- El umbral de confianza del reconocimiento (`LBPH_CONFIDENCE_THRESHOLD`)
  evita que el sistema fuerce una coincidencia cuando no está seguro;
  en ese caso marca el rostro como "no reconocido" en vez de arriesgar
  una asistencia incorrecta.

## 6. Estructura del proyecto
```
asistencia_app/
├── asistencia/        # Configuración del proyecto Django
├── control/            # App principal (modelos, vistas, templates, OpenCV)
│   ├── utils.py         # Lógica de detección y reconocimiento facial
│   ├── exports.py        # Exportación a Excel y PDF
│   ├── models.py         # Carrera, Materia, Curso, Horario, Estudiante, Asistencia
│   └── templates/
├── face_data/           # Fotos y modelo entrenado (NO se sube a git)
├── requirements.txt
├── .env.example
└── manage.py
```

## 7. Notas para el video demostrativo
Con este flujo puedes grabar en menos de 3 minutos:
1. Iniciar sesión y mostrar la configuración (carrera, curso, materia, horario).
2. Registrar un estudiante y capturar su rostro.
3. Entrenar el modelo.
4. Ir a "Tomar asistencia", elegir el horario y mostrar cómo se reconoce
   y se registra automáticamente.
5. Mostrar el "Historial" con un filtro aplicado y exportar a Excel o PDF.
