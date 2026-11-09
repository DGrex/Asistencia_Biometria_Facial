from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),

    path("estudiantes/", views.lista_estudiantes, name="lista_estudiantes"),
    path("estudiantes/nuevo/", views.registrar_estudiante, name="registrar_estudiante"),
    path("estudiantes/<str:cedula>/capturar/", views.capturar_rostro, name="capturar_rostro"),
    path("api/capturar/<str:cedula>/", views.api_capturar_foto, name="api_capturar_foto"),
    path("api/entrenar/", views.api_entrenar, name="api_entrenar"),

    path("asistencia/", views.tomar_asistencia, name="tomar_asistencia"),
    path("api/reconocer/", views.api_reconocer, name="api_reconocer"),

    path("historial/", views.historial, name="historial"),
    path("historial/exportar/excel/", views.historial_exportar_excel, name="historial_exportar_excel"),
    path("historial/exportar/pdf/", views.historial_exportar_pdf, name="historial_exportar_pdf"),
]
