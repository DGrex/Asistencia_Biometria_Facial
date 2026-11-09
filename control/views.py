import datetime
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import exports, utils
from .models import Asistencia, Carrera, Curso, Estudiante, Horario, Materia

# Solo usuarios "staff" (profesores/administradores) pueden usar el sistema.
solo_staff = user_passes_test(lambda u: u.is_staff, login_url="login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("dashboard")
        form.add_error(None, "Credenciales inválidas o usuario sin permisos de profesor.")
    return render(request, "control/login.html", {"form": form})


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
@solo_staff
def dashboard(request):
    hoy = datetime.date.today()
    asistencias_hoy = (
        Asistencia.objects.filter(fecha=hoy)
        .select_related("estudiante", "horario", "horario__curso", "horario__materia")
    )
    return render(
        request,
        "control/dashboard.html",
        {
            "total_estudiantes": Estudiante.objects.filter(activo=True).count(),
            "total_cursos": Curso.objects.count(),
            "asistencias_hoy": asistencias_hoy,
            "hoy": hoy,
        },
    )


# ----------------------------------------------------------------------
# Estudiantes
# ----------------------------------------------------------------------

@login_required(login_url="login")
@solo_staff
def lista_estudiantes(request):
    q = request.GET.get("q", "").strip()
    curso_id = request.GET.get("curso", "")

    estudiantes = Estudiante.objects.select_related("curso", "curso__carrera")
    if q:
        from django.db.models import Q

        estudiantes = estudiantes.filter(Q(nombre__icontains=q) | Q(cedula__icontains=q))
    if curso_id:
        estudiantes = estudiantes.filter(curso_id=curso_id)

    return render(
        request,
        "control/estudiantes.html",
        {
            "estudiantes": estudiantes,
            "cursos": Curso.objects.select_related("carrera"),
            "q": q,
            "curso_id": curso_id,
        },
    )


@login_required(login_url="login")
@solo_staff
def registrar_estudiante(request):
    from django.core.exceptions import ValidationError
    from .models import validar_cedula_ecuatoriana

    error = None
    if request.method == "POST":
        cedula = request.POST.get("cedula", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        curso_id = request.POST.get("curso") or None
        if not cedula or not nombre:
            error = "Cédula y nombre son obligatorios."
        else:
            try:
                validar_cedula_ecuatoriana(cedula)
            except ValidationError as exc:
                error = exc.message
        if not error:
            if Estudiante.objects.filter(cedula=cedula).exists():
                error = "Ya existe un estudiante con esa cédula."
            else:
                Estudiante.objects.create(cedula=cedula, nombre=nombre, curso_id=curso_id)
                return redirect("capturar_rostro", cedula=cedula)
    return render(
        request,
        "control/registrar.html",
        {"error": error, "cursos": Curso.objects.select_related("carrera")},
    )


@login_required(login_url="login")
@solo_staff
def capturar_rostro(request, cedula):
    estudiante = Estudiante.objects.filter(cedula=cedula).first()
    if not estudiante:
        return redirect("registrar_estudiante")
    return render(
        request,
        "control/capturar.html",
        {
            "estudiante": estudiante,
            "fotos_requeridas": utils.FOTOS_POR_ESTUDIANTE,
            "fotos_actuales": utils.contar_muestras(cedula),
        },
    )


@login_required(login_url="login")
@solo_staff
@require_POST
def api_capturar_foto(request, cedula):
    estudiante = Estudiante.objects.filter(cedula=cedula).first()
    if not estudiante:
        return JsonResponse({"ok": False, "error": "Estudiante no encontrado."}, status=404)

    try:
        payload = json.loads(request.body)
        img = utils.decodificar_imagen_base64(payload.get("imagen"))
    except (utils.ImagenInvalidaError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    rostro, error = utils.recortar_rostro_principal(img)
    if error:
        return JsonResponse({"ok": False, "error": error}, status=422)

    total = utils.guardar_muestra_rostro(cedula, rostro, utils.contar_muestras(cedula) + 1)
    listo = total >= utils.FOTOS_POR_ESTUDIANTE
    return JsonResponse({"ok": True, "total": total, "listo": listo})


@login_required(login_url="login")
@solo_staff
@require_POST
def api_entrenar(request):
    try:
        n_estudiantes, n_fotos = utils.entrenar_modelo()
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    from django.conf import settings

    Estudiante.objects.update(rostro_entrenado=False)
    muestras_dir = settings.FACE_DATA_DIR / "muestras"
    codigos_entrenados = (
        [p.name for p in muestras_dir.iterdir() if p.is_dir()] if muestras_dir.exists() else []
    )
    Estudiante.objects.filter(cedula__in=codigos_entrenados).update(rostro_entrenado=True)

    return JsonResponse({"ok": True, "estudiantes": n_estudiantes, "fotos": n_fotos})


# ----------------------------------------------------------------------
# Tomar asistencia (por horario / sesión de clase del día)
# ----------------------------------------------------------------------

@login_required(login_url="login")
@solo_staff
def tomar_asistencia(request):
    horario_id = request.GET.get("horario")
    horario = None
    if horario_id:
        horario = get_object_or_404(
            Horario.objects.select_related("curso", "curso__carrera", "materia"), pk=horario_id
        )

    horarios = Horario.objects.select_related("curso", "curso__carrera", "materia")
    return render(
        request,
        "control/tomar_asistencia.html",
        {"horarios": horarios, "horario": horario},
    )


@login_required(login_url="login")
@solo_staff
@require_POST
def api_reconocer(request):
    try:
        payload = json.loads(request.body)
        horario_id = payload.get("horario_id")
        img = utils.decodificar_imagen_base64(payload.get("imagen"))
    except (utils.ImagenInvalidaError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    if not horario_id:
        return JsonResponse({"ok": False, "error": "Falta seleccionar el horario de clase."}, status=400)
    horario = Horario.objects.filter(pk=horario_id).first()
    if not horario:
        return JsonResponse({"ok": False, "error": "Horario no válido."}, status=404)

    resultados = utils.reconocer_rostros(img)
    hoy = datetime.date.today()
    respuesta = []

    for r in resultados:
        item = {"bbox": r["bbox"], "nombre": None, "estado": "desconocido"}
        if r["cedula"]:
            estudiante = Estudiante.objects.filter(cedula=r["cedula"], activo=True).first()
            if estudiante:
                item["nombre"] = estudiante.nombre
                _, creada = Asistencia.objects.get_or_create(
                    estudiante=estudiante, horario=horario, fecha=hoy
                )
                item["estado"] = "nueva" if creada else "ya_registrada"
        respuesta.append(item)

    return JsonResponse({"ok": True, "resultados": respuesta})


# ----------------------------------------------------------------------
# Historial de asistencias + exportación
# ----------------------------------------------------------------------

def _historial_queryset(request):
    qs = Asistencia.objects.select_related(
        "estudiante", "horario", "horario__curso", "horario__curso__carrera", "horario__materia"
    )

    fecha_desde = request.GET.get("desde", "")
    fecha_hasta = request.GET.get("hasta", "")
    carrera_id = request.GET.get("carrera", "")
    curso_id = request.GET.get("curso", "")
    materia_id = request.GET.get("materia", "")
    q = request.GET.get("q", "").strip()

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if carrera_id:
        qs = qs.filter(horario__curso__carrera_id=carrera_id)
    if curso_id:
        qs = qs.filter(horario__curso_id=curso_id)
    if materia_id:
        qs = qs.filter(horario__materia_id=materia_id)
    if q:
        from django.db.models import Q

        qs = qs.filter(Q(estudiante__nombre__icontains=q) | Q(estudiante__cedula__icontains=q))

    filtros = {
        "desde": fecha_desde,
        "hasta": fecha_hasta,
        "carrera": carrera_id,
        "curso": curso_id,
        "materia": materia_id,
        "q": q,
    }
    return qs, filtros


@login_required(login_url="login")
@solo_staff
def historial(request):
    qs, filtros = _historial_queryset(request)
    return render(
        request,
        "control/historial.html",
        {
            "asistencias": qs[:500],
            "total": qs.count(),
            "filtros": filtros,
            "carreras": Carrera.objects.all(),
            "cursos": Curso.objects.select_related("carrera"),
            "materias": Materia.objects.select_related("carrera"),
        },
    )


@login_required(login_url="login")
@solo_staff
def historial_exportar_excel(request):
    qs, _ = _historial_queryset(request)
    return exports.exportar_excel(qs)


@login_required(login_url="login")
@solo_staff
def historial_exportar_pdf(request):
    qs, _ = _historial_queryset(request)
    return exports.exportar_pdf(qs)
