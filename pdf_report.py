"""
PDF Report Generator for Water Quality Prediction
Uses reportlab to produce a clean, readable report
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Colour palette ─────────────────────────────────────────────────────────────
PURPLE      = colors.HexColor('#667eea')
DARK        = colors.HexColor('#1e293b')
SLATE       = colors.HexColor('#64748b')
GREEN       = colors.HexColor('#10b981')
RED         = colors.HexColor('#ef4444')
AMBER       = colors.HexColor('#f59e0b')
LIGHT_GREEN = colors.HexColor('#d1fae5')
LIGHT_RED   = colors.HexColor('#fee2e2')
LIGHT_AMBER = colors.HexColor('#fef3c7')
LIGHT_GREY  = colors.HexColor('#f8fafc')
BORDER      = colors.HexColor('#e2e8f0')
WHITE       = colors.white

SAFE_RANGES = {
    'pH':              {'min': 6.0,  'max': 8.5,  'unit': ''},
    'Hardness':        {'min': 0,    'max': 400,   'unit': 'mg/L'},
    'TDS':             {'min': 0,    'max': 350,   'unit': 'mg/L'},
    'Chlorine':        {'min': 0,    'max': 4,     'unit': 'mg/L'},
    'Sulfate':         {'min': 0,    'max': 250,   'unit': 'mg/L'},
    'Conductivity':    {'min': 0,    'max': 800,   'unit': 'μS/cm'},
    'Organic Carbon':  {'min': 0,    'max': 2,     'unit': 'mg/L'},
    'Trihalomethanes': {'min': 0,    'max': 80,    'unit': 'μg/L'},
    'Turbidity':       {'min': 0,    'max': 5,     'unit': 'NTU'},
}

PARAM_KEYS = {
    'pH': 'ph', 'Hardness': 'hardness', 'TDS': 'tds',
    'Chlorine': 'chlorine', 'Sulfate': 'sulfate',
    'Conductivity': 'conductivity', 'Organic Carbon': 'organic_carbon',
    'Trihalomethanes': 'trihalomethanes', 'Turbidity': 'turbidity',
}


def generate_pdf(prediction_data: dict) -> bytes:
    """
    Generate a PDF report from prediction data.

    Args:
        prediction_data: dict with keys:
            features_dict, prediction, confidence, timestamp,
            location_name (optional), water_source (optional)

    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Custom styles ──────────────────────────────────────────────────────────
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', textColor=PURPLE,
        alignment=TA_CENTER, spaceAfter=4)

    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica', textColor=SLATE,
        alignment=TA_CENTER, spaceAfter=2)

    section_style = ParagraphStyle('Section', parent=styles['Normal'],
        fontSize=13, fontName='Helvetica-Bold', textColor=DARK,
        spaceBefore=14, spaceAfter=6)

    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica', textColor=DARK,
        leading=16)

    caption_style = ParagraphStyle('Caption', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica', textColor=SLATE,
        alignment=TA_CENTER)

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("💧 Water Quality Prediction Report", title_style))
    story.append(Paragraph("AI-Powered Water Contamination Analysis", subtitle_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        caption_style
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=12))

    # ── Prediction result banner ───────────────────────────────────────────────
    prediction  = prediction_data.get('prediction', 0)
    confidence  = prediction_data.get('confidence', 0)
    timestamp   = prediction_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    features    = prediction_data.get('features_dict', {})
    location    = prediction_data.get('location_name', 'Not specified')
    source      = prediction_data.get('water_source', 'Not specified')

    is_safe = prediction == 1
    result_label = "SAFE WATER" if is_safe else "CONTAMINATED WATER"
    result_color = GREEN if is_safe else RED
    result_bg    = LIGHT_GREEN if is_safe else LIGHT_RED
    result_icon  = "✓ SAFE" if is_safe else "✕ CONTAMINATED"

    result_table = Table(
        [[result_icon, f"Confidence: {confidence:.2f}%"]],
        colWidths=[10 * cm, 7 * cm]
    )
    result_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), result_bg),
        ('TEXTCOLOR',    (0, 0), (0, 0),   result_color),
        ('TEXTCOLOR',    (1, 0), (1, 0),   DARK),
        ('FONTNAME',     (0, 0), (0, 0),   'Helvetica-Bold'),
        ('FONTNAME',     (1, 0), (1, 0),   'Helvetica'),
        ('FONTSIZE',     (0, 0), (0, 0),   16),
        ('FONTSIZE',     (1, 0), (1, 0),   12),
        ('ALIGN',        (0, 0), (0, 0),   'LEFT'),
        ('ALIGN',        (1, 0), (1, 0),   'RIGHT'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6]),
        ('BOX',          (0, 0), (-1, -1), 1.5, result_color),
        ('TOPPADDING',   (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 12),
        ('LEFTPADDING',  (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Sample info ────────────────────────────────────────────────────────────
    story.append(Paragraph("📋 Sample Information", section_style))

    info_data = [
        ['Field', 'Value'],
        ['Analysis Date & Time', timestamp],
        ['Location', location],
        ['Water Source', source],
        ['Prediction Result', result_label],
        ['Confidence Score', f"{confidence:.2f}%"],
    ]

    info_table = Table(info_data, colWidths=[6 * cm, 11 * cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  PURPLE),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  WHITE),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 10),
        ('BACKGROUND',   (0, 1), (-1, -1), LIGHT_GREY),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ('GRID',         (0, 0), (-1, -1), 0.5, BORDER),
        ('FONTNAME',     (0, 1), (0, -1),  'Helvetica-Bold'),
        ('TEXTCOLOR',    (0, 1), (0, -1),  SLATE),
        ('TOPPADDING',   (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Parameter analysis ─────────────────────────────────────────────────────
    story.append(Paragraph("🔬 Water Quality Parameter Analysis", section_style))

    param_data = [['Parameter', 'Measured Value', 'Safe Range', 'Status']]
    violations = []

    for param, cfg in SAFE_RANGES.items():
        key = PARAM_KEYS[param]
        val = features.get(key, 0)
        unit = cfg['unit']
        safe_range = f"{cfg['min']} – {cfg['max']} {unit}".strip()
        measured   = f"{val:.2f} {unit}".strip()

        if val < cfg['min']:
            status = "⬇ Too Low"
            violations.append((param, val, unit, 'Low', cfg['min'], cfg['max']))
        elif val > cfg['max']:
            status = "⬆ Too High"
            violations.append((param, val, unit, 'High', cfg['min'], cfg['max']))
        else:
            status = "✓ Normal"

        param_data.append([param, measured, safe_range, status])

    param_table = Table(param_data, colWidths=[4.5*cm, 4*cm, 4.5*cm, 4*cm])
    param_style = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  PURPLE),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  WHITE),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 0), (0, -1),  'LEFT'),
    ])

    # Row colouring based on status
    for i, row in enumerate(param_data[1:], start=1):
        status = row[3]
        if 'High' in status or 'Low' in status:
            param_style.add('BACKGROUND', (0, i), (-1, i), LIGHT_RED)
            param_style.add('TEXTCOLOR',  (3, i), (3, i),  RED)
            param_style.add('FONTNAME',   (3, i), (3, i),  'Helvetica-Bold')
        else:
            bg = WHITE if i % 2 == 0 else LIGHT_GREY
            param_style.add('BACKGROUND', (0, i), (-1, i), bg)
            param_style.add('TEXTCOLOR',  (3, i), (3, i),  GREEN)
            param_style.add('FONTNAME',   (3, i), (3, i),  'Helvetica-Bold')

    param_table.setStyle(param_style)
    story.append(param_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Contamination reasons ──────────────────────────────────────────────────
    if violations:
        story.append(Paragraph("⚠️ Contamination Reasons", section_style))

        for param, val, unit, direction, safe_min, safe_max in violations:
            direction_text = "exceeds maximum" if direction == 'High' else "is below minimum"
            limit = safe_max if direction == 'High' else safe_min
            text = (f"<b>{param}</b>: Measured {val:.2f} {unit} — "
                    f"{direction_text} safe limit of {limit} {unit}.")
            story.append(Paragraph(f"• {text}", body_style))

        story.append(Spacer(1, 0.3 * cm))

        advisory_data = [[
            Paragraph(
                "<b>⚠️ Health Advisory</b><br/>"
                "This water may pose health risks. Recommended actions:<br/>"
                "• Do not use for drinking or cooking without treatment<br/>"
                "• Install appropriate filtration or purification systems<br/>"
                "• Consult a water quality expert or local authority<br/>"
                "• Retest after treatment to confirm safety",
                ParagraphStyle('Advisory', parent=styles['Normal'],
                    fontSize=9, fontName='Helvetica', textColor=DARK, leading=15)
            )
        ]]
        advisory_table = Table(advisory_data, colWidths=[17 * cm])
        advisory_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_AMBER),
            ('BOX',           (0, 0), (-1, -1), 1, AMBER),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ]))
        story.append(advisory_table)

    elif is_safe:
        safe_note = Table([[
            Paragraph(
                "✓ <b>All parameters are within WHO/EPA safe drinking water limits.</b> "
                "This water is suitable for consumption.",
                ParagraphStyle('SafeNote', parent=styles['Normal'],
                    fontSize=9, fontName='Helvetica', textColor=DARK, leading=14)
            )
        ]], colWidths=[17 * cm])
        safe_note.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_GREEN),
            ('BOX',           (0, 0), (-1, -1), 1, GREEN),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ]))
        story.append(safe_note)

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Water Quality AI System  |  Powered by Random Forest ML  |  Based on WHO & EPA Standards",
        caption_style
    ))

    doc.build(story)
    return buffer.getvalue()
