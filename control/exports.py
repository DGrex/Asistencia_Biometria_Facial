"""Generación de informes de asistencia en Excel (.xlsx) y PDF."""
import io

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

COLUMNAS = ["Fecha", "Hora", "Estudiante", "Cédula", "Carrera", "Curso", "Materia", "Día de clase"]


def _filas(queryset):
    filas = []
    for a in queryset:
        filas.append(
            [
                a.fecha.strftime("%d/%m/%Y"),
                a.hora.strftime("%H:%M"),
                a.estudiante.nombre,
                a.estudiante.cedula,
                a.horario.curso.carrera.nombre,
                a.horario.curso.nombre,
                a.horario.materia.nombre,
                a.horario.get_dia_semana_display(),
            ]
        )
    return filas


def exportar_excel(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencias"

    ws.append(COLUMNAS)
    for celda in ws[1]:
        celda.font = Font(bold=True)

    for fila in _filas(queryset):
        ws.append(fila)

    for columna in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in columna)
        ws.column_dimensions[columna[0].column_letter].width = max_len + 4

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="informe_asistencias.xlsx"'
    return response


def exportar_pdf(queryset, titulo="Informe de asistencias"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), topMargin=1.5 * cm, bottomMargin=1.5 * cm
    )
    estilos = getSampleStyleSheet()
    elementos = [Paragraph(titulo, estilos["Title"]), Spacer(1, 0.5 * cm)]

    datos = [COLUMNAS] + _filas(queryset)
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="informe_asistencias.pdf"'
    return response
