from django.contrib import admin

from .models import Asistencia, Carrera, Curso, Estudiante, Horario, Materia


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "carrera")
    list_filter = ("carrera",)
    search_fields = ("nombre",)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "carrera")
    list_filter = ("carrera",)
    search_fields = ("nombre",)


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("curso", "materia", "dia_semana", "hora_inicio", "hora_fin")
    list_filter = ("curso__carrera", "curso", "materia", "dia_semana")


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("cedula", "nombre", "curso", "activo", "rostro_entrenado", "creado")
    list_filter = ("curso__carrera", "curso", "activo")
    search_fields = ("cedula", "nombre")


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "horario", "fecha", "hora")
    list_filter = ("fecha", "horario__curso", "horario__materia")
    search_fields = ("estudiante__nombre", "estudiante__cedula")
