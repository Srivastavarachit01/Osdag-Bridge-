"""
Pier Builder for Bridge Substructure
====================================

This module generates parametric 3D CAD models of circular pier columns
and their internal steel reinforcement using pythonOCC.

Parameters:
    - pier_diameter: Column diameter (default: 800 mm)
    - pier_height: Column vertical height (default: 3000 mm)
    - rebar_main_diameter: Main longitudinal bar diameter (default: 16 mm)
    - rebar_spacing_longitudinal: Nominal bar spacing along circumference (default: 150 mm)
    - rebar_transverse_diameter: Lateral tie/spiral diameter (default: 8 mm)
    - rebar_spacing_transverse: Pitch between transverse ties (default: 200 mm)
    - rebar_cover: Clear concrete cover (default: 40 mm)
"""

import math
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax2, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound


def _translate(shape, dx=0.0, dy=0.0, dz=0.0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, dy, dz))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _make_compound(shapes):
    if not shapes:
        return None
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for s in shapes:
        if s is not None and not s.IsNull():
            builder.Add(compound, s)
    return compound


def build_pier_geometry(
    *,
    pier_diameter: float = 800.0,
    pier_height: float = 3000.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
    top_z: float = 0.0,
    rebar_main_diameter: float = 16.0,
    rebar_spacing_longitudinal: float = 150.0,
    rebar_transverse_diameter: float = 8.0,
    rebar_spacing_transverse: float = 200.0,
    rebar_cover: float = 40.0,
    include_reinforcement: bool = True
) -> dict:
    """
    Build parametric circular pier column and reinforcement cage.

    Args:
        pier_diameter: Outer diameter of circular column (mm)
        pier_height: Height of column (mm)
        center_x: Center X coordinate (mm)
        center_y: Center Y coordinate (mm)
        top_z: Elevation of top of column (mm)
        rebar_main_diameter: Diameter of longitudinal rebars (mm)
        rebar_spacing_longitudinal: Center-to-center spacing along perimeter (mm)
        rebar_transverse_diameter: Diameter of lateral ties (mm)
        rebar_spacing_transverse: Vertical pitch between ties (mm)
        rebar_cover: Clear concrete cover (mm)
        include_reinforcement: Whether to generate rebar solids

    Returns:
        dict: Containing concrete solid, rebar shapes, and coordinate metadata.
    """
    radius = pier_diameter / 2.0
    bottom_z = top_z - pier_height

    # 1. Concrete Pier Solid
    # Local Z direction from bottom_z up to top_z
    pier_axis = gp_Ax2(gp_Pnt(center_x, center_y, bottom_z), gp_Dir(0, 0, 1))
    concrete_solid = BRepPrimAPI_MakeCylinder(pier_axis, radius, pier_height).Shape()

    rebar_main = []
    rebar_ties = []

    if include_reinforcement:
        # Pitch circle radius for longitudinal bars
        r_pitch = radius - rebar_cover - rebar_transverse_diameter - (rebar_main_diameter / 2.0)
        if r_pitch > 0:
            circumference = 2.0 * math.pi * r_pitch
            num_bars = max(6, int(round(circumference / rebar_spacing_longitudinal)))
            d_theta = (2.0 * math.pi) / num_bars

            bar_z_start = bottom_z + rebar_cover
            bar_length = pier_height - (2.0 * rebar_cover)
            bar_radius = rebar_main_diameter / 2.0

            # Vertical longitudinal main bars
            for i in range(num_bars):
                angle = i * d_theta
                bx = center_x + r_pitch * math.cos(angle)
                by = center_y + r_pitch * math.sin(angle)
                b_axis = gp_Ax2(gp_Pnt(bx, by, bar_z_start), gp_Dir(0, 0, 1))
                bar_solid = BRepPrimAPI_MakeCylinder(b_axis, bar_radius, bar_length).Shape()
                rebar_main.append(bar_solid)

            # Transverse circular ties (modeled as polygonal rings or cylindrical discs)
            tie_radius_outer = radius - rebar_cover
            tie_radius_inner = tie_radius_outer - rebar_transverse_diameter
            tie_z_start = bottom_z + rebar_cover + (rebar_transverse_diameter / 2.0)
            tie_z_end = top_z - rebar_cover - (rebar_transverse_diameter / 2.0)

            num_ties = max(2, int((tie_z_end - tie_z_start) / rebar_spacing_transverse) + 1)
            # Represent each circular tie with segments of cylinders along pitch circle
            num_tie_segments = 16
            seg_d_theta = (2.0 * math.pi) / num_tie_segments
            r_tie_center = (tie_radius_outer + tie_radius_inner) / 2.0
            tie_thickness = rebar_transverse_diameter

            for k in range(num_ties):
                tz = tie_z_start + k * rebar_spacing_transverse
                if tz > tie_z_end:
                    break
                # Create a cylinder representing the tie at level tz
                t_axis = gp_Ax2(gp_Pnt(center_x, center_y, tz), gp_Dir(0, 0, 1))
                # For solid representation without Boolean cut performance overhead:
                # build circular ring segments
                for s_idx in range(num_tie_segments):
                    ang1 = s_idx * seg_d_theta
                    ang2 = (s_idx + 1) * seg_d_theta
                    p1 = gp_Pnt(center_x + r_tie_center * math.cos(ang1), center_y + r_tie_center * math.sin(ang1), tz)
                    p2 = gp_Pnt(center_x + r_tie_center * math.cos(ang2), center_y + r_tie_center * math.sin(ang2), tz)
                    dx = p2.X() - p1.X()
                    dy = p2.Y() - p1.Y()
                    seg_len = math.sqrt(dx*dx + dy*dy)
                    if seg_len > 1e-4:
                        seg_dir = gp_Dir(dx / seg_len, dy / seg_len, 0)
                        seg_ax = gp_Ax2(p1, seg_dir)
                        seg_cyl = BRepPrimAPI_MakeCylinder(seg_ax, tie_thickness / 2.0, seg_len).Shape()
                        rebar_ties.append(seg_cyl)

    all_rebars = rebar_main + rebar_ties
    rebar_compound = _make_compound(all_rebars)

    return {
        "concrete": concrete_solid,
        "rebar_main": rebar_main,
        "rebar_ties": rebar_ties,
        "rebars": all_rebars,
        "rebar_compound": rebar_compound,
        "pier_diameter": pier_diameter,
        "pier_height": pier_height,
        "center_x": center_x,
        "center_y": center_y,
        "top_z": top_z,
        "bottom_z": bottom_z
    }

