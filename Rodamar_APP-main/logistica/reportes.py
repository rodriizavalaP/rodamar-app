"""Generación del PDF de reporte diario (sin dependencias de Django, para poder probarlo solo)."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL = colors.HexColor('#1D4ED8')
GRIS = colors.HexColor('#F1F5F9')
BORDE = colors.HexColor('#CBD5E1')

ESTADOS = {
    'NO_ENCONTRADO': 'No encontrado',
    'ENCONTRADO': 'Encontrado',
    'EN_PROCESO': 'En proceso',
    'EN_CAMINO': 'En traslado',
    'ENTREGADO': 'Entregado',
}


def _p(texto, estilo):
    return Paragraph(escape(str(texto if texto not in (None, '') else '-')), estilo)


def _tabla(encabezados, filas, anchos, estilo_celda, estilo_cab):
    datos = [[_p(h, estilo_cab) for h in encabezados]]
    datos += [[_p(c, estilo_celda) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS]),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return t


def generar_reporte_pdf(fecha, movimientos, fotos, generado_por, generado_en):
    """
    fecha: date. movimientos: lista de dicts (hora, chasis, vehiculo, cliente, anterior, nuevo,
    ubicacion, ciguena, nota, usuario) ya ordenados por hora. fotos: lista de dicts
    (hora, chasis, tipo, descripcion, usuario). Devuelve los bytes del PDF.
    """
    base = getSampleStyleSheet()
    titulo = ParagraphStyle('t', parent=base['Title'], fontName='Helvetica-Bold', fontSize=18,
                            textColor=AZUL, alignment=0, spaceAfter=2)
    sub = ParagraphStyle('s', parent=base['Normal'], fontSize=9, textColor=colors.HexColor('#475569'))
    h2 = ParagraphStyle('h2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=12,
                        textColor=colors.HexColor('#0A192F'), spaceBefore=10, spaceAfter=4)
    celda = ParagraphStyle('c', parent=base['Normal'], fontSize=7.5, leading=9)
    cab = ParagraphStyle('cab', parent=celda, textColor=colors.white, fontName='Helvetica-Bold')
    vacio = ParagraphStyle('v', parent=base['Normal'], fontSize=9, textColor=colors.HexColor('#64748B'))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=f"Reporte diario RODAMAR {fecha:%d-%m-%Y}", author='RODAMAR')
    ancho = landscape(A4)[0] - 24 * mm
    el = [
        Paragraph('RODAMAR · Reporte diario de operaciones', titulo),
        Paragraph(escape(f"Fecha del reporte: {fecha:%d/%m/%Y} · Generado el {generado_en:%d/%m/%Y %H:%M} "
                         f"por {generado_por}"), sub),
        Spacer(1, 6),
    ]

    # Resumen
    por_estado = {}
    chasis = set()
    for m in movimientos:
        chasis.add(m['chasis'])
        por_estado[m['nuevo']] = por_estado.get(m['nuevo'], 0) + 1
    resumen = [[
        f"{len(movimientos)}", f"{len(chasis)}",
        f"{por_estado.get('ENTREGADO', 0)}", f"{por_estado.get('EN_CAMINO', 0)}", f"{len(fotos)}",
    ]]
    cab_res = ['Movimientos', 'Vehículos movidos', 'Entregados / despachados', 'Salidas en traslado', 'Fotos de chequeo']
    t = Table([[_p(c, cab) for c in cab_res], [_p(x, ParagraphStyle('n', parent=celda, fontSize=14, leading=16)) for x in resumen[0]]],
              colWidths=[ancho / 5] * 5)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), AZUL), ('GRID', (0, 0), (-1, -1), 0.4, BORDE),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 4),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    el += [Paragraph('Resumen del día', h2), t]

    def seccion(nombre, filas, encabezados, anchos):
        el.append(Paragraph(nombre, h2))
        if filas:
            el.append(_tabla(encabezados, filas, anchos, celda, cab))
        else:
            el.append(Paragraph('Sin registros este día.', vacio))

    entregados = [[m['hora'], m['chasis'], m['vehiculo'], m['cliente'], m['usuario']]
                  for m in movimientos if m['nuevo'] == 'ENTREGADO']
    seccion('Entregados / despachados', entregados, ['Hora', 'Chasis', 'Vehículo', 'Cliente', 'Registrado por'],
            [ancho * x for x in (0.08, 0.22, 0.25, 0.28, 0.17)])

    traslados = [[m['hora'], m['chasis'], m['vehiculo'], m['ciguena'] or 'Por sus propios medios', m['nota'], m['usuario']]
                 for m in movimientos if m['nuevo'] == 'EN_CAMINO']
    seccion('Salidas en traslado', traslados, ['Hora', 'Chasis', 'Vehículo', 'Cigüeña / modo', 'Nota', 'Registrado por'],
            [ancho * x for x in (0.07, 0.2, 0.2, 0.18, 0.22, 0.13)])

    detalle = [[m['hora'], m['chasis'], m['vehiculo'], m['cliente'],
                f"{ESTADOS.get(m['anterior'], m['anterior'] or '-')} > {ESTADOS.get(m['nuevo'], m['nuevo'])}",
                m['ubicacion'], m['ciguena'], m['nota'], m['usuario']] for m in movimientos]
    seccion('Registro cronológico de movimientos', detalle,
            ['Hora', 'Chasis', 'Vehículo', 'Cliente', 'Cambio de estado', 'Ubicación', 'Cigüeña', 'Nota', 'Usuario'],
            [ancho * x for x in (0.05, 0.15, 0.13, 0.14, 0.15, 0.09, 0.08, 0.12, 0.09)])

    seccion('Fotos de chequeo subidas', [[f['hora'], f['chasis'], f['tipo'], f['descripcion'], f['usuario']] for f in fotos],
            ['Hora', 'Chasis', 'Tipo', 'Observación', 'Subida por'],
            [ancho * x for x in (0.08, 0.22, 0.17, 0.35, 0.18)])

    def pie(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(12 * mm, 8 * mm, f"RODAMAR · Reporte del {fecha:%d/%m/%Y}")
        canvas.drawRightString(landscape(A4)[0] - 12 * mm, 8 * mm, f"Página {doc_.page}")
        canvas.restoreState()

    doc.build(el, onFirstPage=pie, onLaterPages=pie)
    return buf.getvalue()
