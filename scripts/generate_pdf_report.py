"""
Generate PDF Technical Report for OsdagBridge Substructure Modeling & IFC Integration.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#555555"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "OsdagBridge: Parametric 3D CAD Substructure & IFC4 Integration")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Screening Task Submission — Osdag Bridge Team (IIT Bombay)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def generate_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
        backColor=colors.HexColor("#EDF2F7"),
        borderColor=colors.HexColor("#CBD5E0"),
        borderWidth=0.5,
        borderPadding=4,
        spaceAfter=6,
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2D3748"),
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("Technical Report: Parametric 3D CAD Modeling of Bridge Substructure and IFC Workflow Integration", title_style))
    story.append(Paragraph("<b>Project:</b> OsdagBridge (IIT Bombay) &nbsp;|&nbsp; <b>Module:</b> Plate Girder Bridge Substructure & OpenBIM IFC4", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceBefore=0, spaceAfter=10))

    # Section 1: Methodology
    story.append(Paragraph("1. Methodology", h1_style))
    story.append(Paragraph(
        "Bridge substructures transfer dead loads, vehicular live loads, and lateral braking/seismic forces from the bridge superstructure to competent foundation strata. Prior to this contribution, OsdagBridge implemented complete steel plate girder superstructure geometry (web, flanges, stiffeners, cross bracings, deck slab, crash barriers, and railings), while the substructure builders remained empty stubs.",
        body_style
    ))

    story.append(Paragraph("1.1 Structural Components & Parametric Geometry", h2_style))
    story.append(Paragraph("<b>1. Hammerhead Pier Cap:</b> Inverted trapezoidal concrete cap extending transversely (Y) beneath the girders. Formed in OpenCASCADE by sweeping a polygonal wire across length L_cap along X via BRepPrimAPI_MakePrism. Top width = 3000 mm, bottom width = 1200 mm, depth = 600 mm, length = 1200 mm.", bullet_style))
    story.append(Paragraph("<b>2. Circular Pier Column:</b> Central RCC column supporting the pier cap soffit. Modeled using BRepPrimAPI_MakeCylinder centered at (center_x, center_y). Default diameter = 800 mm, height = 3000 mm.", bullet_style))
    story.append(Paragraph("<b>3. Rectangular Pile Cap:</b> Heavy foundation footing distributing column axial forces and moments into the pile grid. Modeled via BRepPrimAPI_MakeBox. Dimensions: length = 2200 mm, width = 1200 mm, depth = 600 mm.", bullet_style))
    story.append(Paragraph("<b>4. Group Piles (2x2 Grid):</b> Four bored cast-in-place circular piles arranged symmetrically at (±s/2, ±s/2) with spacing s = 600 mm c/c. Diameter = 400 mm, length = 5000 mm.", bullet_style))
    story.append(Paragraph("<b>5. Internal Reinforcement:</b> Complete physical rebars modeled as solid cylinders: main longitudinal bars (dia 16 mm @ 150 mm spacing) and transverse circular ties / stirrup cages (dia 8 mm @ 200 mm spacing) with 40 mm clear cover.", bullet_style))

    story.append(Paragraph("1.2 Coordinate System & Elevation Alignment", h2_style))
    story.append(Paragraph(
        "To ensure mathematical precision with existing superstructure components, substructures are generated at longitudinal coordinates X = 0 (left bearing) and X = L_span (right bearing). The vertical datum is aligned using the girder contact elevation Z_contact = -D/2 - T_fb. Pier cap top is set directly under bearing pedestals at Z_cap_top = Z_contact - 120 mm. Subsequent elevations follow directly: Z_pier_top = Z_cap_top - D_cap, Z_pile_cap_top = Z_pier_top - H_pier, and Z_pile_top = Z_pile_cap_top - D_pile_cap.",
        body_style
    ))

    story.append(Paragraph("1.3 OpenCASCADE & UI Rendering Integration", h2_style))
    story.append(Paragraph(
        "In cad_generator.py (Step 12), the substructure geometry is generated and aggregated into model_data with keys substructure_concrete and substructure_rebar. In the Qt3D display window (cad_3d.py), concrete shapes are registered with transparency = 0.65 (opacity = 0.35) and a clean architectural concrete tone, while internal rebars are rendered opaque with a distinctive steel color (RGB 180, 80, 45). Independent UI toggle checkboxes allow users to inspect each element individually.",
        body_style
    ))

    story.append(Spacer(1, 8))

    # Section 2: IFC Integration
    story.append(Paragraph("2. IFC4 Workflow Integration", h1_style))
    story.append(Paragraph(
        "OpenBIM workflows mandate standard semantic classification and property attachment according to ISO 16739-1:2018 (IFC4). The substructure integration bridges OpenCASCADE geometric representations with semantic IFC product definitions.",
        body_style
    ))

    story.append(Paragraph("2.1 Semantic Entity Mapping & Spatial Hierarchy", h2_style))
    story.append(Paragraph("The spatial hierarchy is structured into dedicated storeys: <b>IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey ['Superstructure', 'Substructure']</b>. Substructure components are mapped as follows:", body_style))
    story.append(Paragraph("• <b>Pier Column:</b> Mapped to <code>IfcColumn</code> with swept solid circular profile (<code>IfcCircleProfileDef</code>).", bullet_style))
    story.append(Paragraph("• <b>Pier Cap:</b> Mapped to <code>IfcBeam</code> with <code>IfcArbitraryClosedProfileDef</code> trapezoidal section.", bullet_style))
    story.append(Paragraph("• <b>Pile Cap:</b> Mapped to <code>IfcFooting</code> with <code>PredefinedType='PAD_FOOTING'</code>.", bullet_style))
    story.append(Paragraph("• <b>Piles:</b> Mapped to <code>IfcPile</code> with <code>PredefinedType='BORED'</code>.", bullet_style))
    story.append(Paragraph("• <b>Rebar Elements:</b> Mapped to <code>IfcReinforcingBar</code> with <code>NominalDiameter</code>.", bullet_style))

    story.append(Paragraph("2.2 Property Sets (Pset_OsdagSubstructure & Pset_OsdagRebar)", h2_style))
    story.append(Paragraph(
        "Parametric metadata is attached via <code>IfcRelDefinesByProperties</code> to support downstream automated quantity takeoffs (BOQ), structural scheduling, and clash detection in software like Autodesk Revit, Navisworks, and Solibri:",
        body_style
    ))
    story.append(Paragraph("• <b>Pset_OsdagSubstructure:</b> ComponentType, Diameter_m, Height_m, Length_m, Width_m, Depth_m, Material ('Reinforced Concrete'), ConcreteGrade ('M35' / 'M40').", bullet_style))
    story.append(Paragraph("• <b>Pset_OsdagRebar:</b> ComponentType ('Reinforcing Bar'), NominalDiameter_mm (16.0 / 8.0), BarLength_m, SteelGrade ('Fe 500').", bullet_style))

    story.append(Spacer(1, 8))

    # Section 3: Challenges & Solutions
    story.append(Paragraph("3. Challenges & Technical Solutions", h1_style))

    table_data = [
        [
            Paragraph("Challenge Encountered", table_header),
            Paragraph("Root Cause", table_header),
            Paragraph("Solution Implemented", table_header),
        ],
        [
            Paragraph("Coordinate System & Skew Inversion", table_cell),
            Paragraph("Girder CAD historically negates skew angle to match 2D drafting conventions.", table_cell),
            Paragraph("Substructure builders accept explicit center_x, center_y, top_z and skew_angle, applying gp_Ax1 vertical column rotations.", table_cell),
        ],
        [
            Paragraph("Rebar Visibility Inside Concrete", table_cell),
            Paragraph("Default OCC AIS objects are fully opaque, obscuring internal steel cages.", table_cell),
            Paragraph("Applied transparency=0.65 (opacity=0.35) to concrete solids in cad_3d.py and assigned vivid metallic contrast to rebars.", table_cell),
        ],
        [
            Paragraph("OCC Boolean Cut Performance Bottleneck", table_cell),
            Paragraph("Using BRepAlgoAPI_Cut to hollow out circular hoops caused extreme CPU lag and kernel crashes.", table_cell),
            Paragraph("Modeled circular ties as segmented cylindrical sweeps along the pitch circle, achieving 100% robust solid geometry without Booleans.", table_cell),
        ],
        [
            Paragraph("IFC Spatial Hierarchy Validation", table_cell),
            Paragraph("Original exporter lumped all elements into a single Superstructure storey.", table_cell),
            Paragraph("Extended initialize_file() with a dedicated Substructure storey related via IfcRelAggregates, satisfying strict IFC4 WR21 rules.", table_cell),
        ],
    ]

    col_widths = [120, 180, 204]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))

    # Section 4: References
    story.append(Paragraph("4. References & Codes of Practice", h1_style))
    story.append(Paragraph("1. <b>OpenCASCADE Technology (OCCT):</b> 3D Surface & Solid Modeling Library, version 7.x documentation.", bullet_style))
    story.append(Paragraph("2. <b>pythonocc-core:</b> Python bindings for OpenCASCADE Technology (OCC).", bullet_style))
    story.append(Paragraph("3. <b>BuildingSMART International:</b> Industry Foundation Classes (IFC) 4 (ISO 16739-1:2018) Specification.", bullet_style))
    story.append(Paragraph("4. <b>IfcOpenShell:</b> Open-source IFC library and geometry compilation engine.", bullet_style))
    story.append(Paragraph("5. <b>IRC:5-2015:</b> Standard Specifications and Code of Practice for Road Bridges, Section I - General Features of Design.", bullet_style))
    story.append(Paragraph("6. <b>IRC:112-2020:</b> Code of Practice for Concrete Road Bridges (Design and Detailing of RCC Members).", bullet_style))
    story.append(Paragraph("7. <b>IS 1786:2008:</b> High Strength Deformed Steel Bars and Wires for Concrete Reinforcement.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Report generated successfully at: {output_path}")


if __name__ == "__main__":
    out = "/Users/srivrac10/Desktop/Osdag/OsdagBridge/docs/SUBSTRUCTURE_AND_IFC_REPORT.pdf"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    generate_pdf(out)
