from django.core.exceptions import ValidationError
from django.db import models


def validar_cedula_ecuatoriana(value):
    cedula = str(value).strip()
    if not cedula.isdigit() or len(cedula) != 10:
        raise ValidationError("La cédula debe tener exactamente 10 dígitos numéricos.")
    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError("Los dos primeros dígitos de la cédula no corresponden a ninguna provincia.")
    tercer_digito = int(cedula[2])
    if tercer_digito >= 6:
        raise ValidationError("El tercer dígito de la cédula debe ser menor a 6 para personas naturales.")
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i, coef in enumerate(coeficientes):
        producto = int(cedula[i]) * coef
        if producto >= 10:
            producto -= 9
        total += producto
    digito_verificador = 0 if total % 10 == 0 else 10 - (total % 10)
    if digito_verificador != int(cedula[9]):
        raise ValidationError("La cédula ingresada no es válida.")

DIAS_SEMANA = [
    ("LUN", "Lunes"),
    ("MAR", "Martes"),
    ("MIE", "Miércoles"),
    ("JUE", "Jueves"),
    ("VIE", "Viernes"),
    ("SAB", "Sábado"),
    ("DOM", "Domingo"),
]


class Carrera(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    nombre = models.CharField(max_length=150)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name="materias")

    class Meta:
        ordering = ["nombre"]
        unique_together = ("nombre", "carrera")
        verbose_name = "Materia"
        verbose_name_plural = "Materias"

    def __str__(self):
        return f"{self.nombre} ({self.carrera.nombre})"


class Curso(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Quinto A, Software 5-1")
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name="cursos")

    class Meta:
        ordering = ["carrera__nombre", "nombre"]
        unique_together = ("nombre", "carrera")
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self):
        return f"{self.nombre} - {self.carrera.nombre}"


class Horario(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="horarios")
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]
        verbose_name = "Horario de clase"
        verbose_name_plural = "Horarios de clase"

    def __str__(self):
        return (
            f"{self.curso.nombre} - {self.materia.nombre} - "
            f"{self.get_dia_semana_display()} {self.hora_inicio.strftime('%H:%M')}"
        )


class Estudiante(models.Model):
    cedula = models.CharField(
        max_length=10,
        unique=True,
        help_text="Cédula de identidad ecuatoriana (10 dígitos).",
        validators=[validar_cedula_ecuatoriana],
    )
    nombre = models.CharField(max_length=150)
    curso = models.ForeignKey(
        Curso, on_delete=models.SET_NULL, null=True, blank=True, related_name="estudiantes"
    )
    activo = models.BooleanField(default=True)
    rostro_entrenado = models.BooleanField(
        default=False, help_text="True cuando el modelo ya incluye fotos de este estudiante."
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"


class Asistencia(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="asistencias")
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()
    hora = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ("estudiante", "horario", "fecha")
        ordering = ["-fecha", "-hora"]
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"

    def __str__(self):
        return f"{self.estudiante.nombre} - {self.horario.materia.nombre} - {self.fecha}"
