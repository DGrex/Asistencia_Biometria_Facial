# Sistema de Control de Asistencia por Reconocimiento Facial

Sistema web que detecta y reconoce rostros en tiempo real para registrar asistencia de estudiantes de forma automática. Organiza los registros por carrera, curso, materia y horario de clase.

**Stack:** Django · OpenCV (Haar Cascade + LBPH) · PostgreSQL

No requiere descargar modelos externos: el detector y el reconocedor vienen incluidos en `opencv-contrib-python`.

---

## Requisitos

- Python 3.10+
- PostgreSQL (local o en la nube, por ejemplo [Neon](https://neon.tech))
- Cámara web

## Instalación

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
# Edita .env con tus credenciales de PostgreSQL y una SECRET_KEY propia.

# 4. Aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Crear usuario administrador (profesor)
python manage.py createsuperuser

# 6. Iniciar el servidor
python manage.py runserver
```

Accede en `http://127.0.0.1:8000/` e inicia sesión con el usuario creado.

---

## Configuración inicial

Antes de registrar estudiantes, entra al panel de administración (`/admin/`) y crea los siguientes elementos **en orden**:

1. **Carreras** — ej. "Ingeniería en Software"
2. **Materias** — ej. "Bases de Datos", asociada a una carrera
3. **Cursos** — ej. "Quinto A", asociado a una carrera
4. **Horarios de clase** — combinación de curso + materia + día + hora de inicio/fin

Cada sesión de asistencia queda vinculada a un horario específico, lo que permite tener registros independientes por día y por materia.

---

## Uso

### 1. Registrar un estudiante
Ve a **Estudiantes → Registrar estudiante**, ingresa el código, nombre y curso. La cámara captura automáticamente 15 fotos del rostro del estudiante.

### 2. Entrenar el modelo
Después de registrar uno o más estudiantes, pulsa **"Entrenar modelo"**. Repite este paso cada vez que agregues un nuevo estudiante.

### 3. Tomar asistencia
En **Tomar asistencia**, selecciona el horario de la sesión (curso + materia + día + hora) y activa la cámara. El sistema reconoce los rostros en tiempo real y marca la asistencia automáticamente. Cada estudiante solo se registra una vez por sesión.

### 4. Consultar historial
La sección **Historial** muestra todos los registros con filtros por fecha, carrera, curso, materia y nombre/código de estudiante. Desde ahí se puede exportar a **Excel** o **PDF**.

---

## Seguridad

- Todas las vistas requieren sesión activa con permisos de staff (profesor).
- Las fotos y el modelo entrenado se almacenan en `face_data/`, fuera de las carpetas públicas, inaccesibles por URL.
- Protección CSRF activa en formularios y llamadas AJAX.
- Las imágenes recibidas por la cámara se validan (tipo y tamaño) antes de procesarse.
- Credenciales y `SECRET_KEY` se leen desde `.env`, nunca escritas en el código.
- `face_data/` y `.env` están en `.gitignore`: los datos biométricos nunca se suben al repositorio.
- El umbral de confianza LBPH evita coincidencias forzadas; cuando no hay seguridad suficiente, el rostro se marca como "no reconocido".

---

## Estructura del proyecto

```
asistencia_app/
├── asistencia/          # Configuración del proyecto Django
├── control/             # App principal
│   ├── models.py        # Carrera, Materia, Curso, Horario, Estudiante, Asistencia
│   ├── views.py         # Vistas y lógica de negocio
│   ├── utils.py         # Detección y reconocimiento facial (OpenCV)
│   ├── exports.py       # Exportación a Excel y PDF
│   └── templates/       # Plantillas HTML
├── face_data/           # Fotos y modelo entrenado (no se sube a git)
├── requirements.txt
├── .env.example
└── manage.py
```
