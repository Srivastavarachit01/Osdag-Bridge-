"""
Pile Builder for Foundation
===========================

This module generates parametric 3D CAD models of circular piles arranged in a 2x2 grid
and their internal reinforcement cages using pythonOCC.

Parameters:
    - n_piles_per_cap: Number of piles (default: 4)
    - pile_diameter: Circular pile diameter (default: 400 mm)
    - pile_length: Pile vertical embedment length (default: 5000 mm)
    - pile_spacing: Center-to-center pile spacing (default: 600 mm)
    - rebar_main_diameter: Main longitudinal bar diameter (default: 16 mm)
    - rebar_spacing_longitudinal: Spacing between bars on pitch circle (default: 150 mm)
    - rebar_transverse_diameter: Spiral/tie bar diameter (default: 8 mm)
    - rebar_spacing_transverse: Vertical pitch between ties (default: 200 mm)
    - rebar_cover: Clear concrete cover (default: 40 mm)
"""

import math
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Ax2, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound


def _translate(shape, dx=0.0, dy=0.0, dz=0.0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, dy, dz))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _rotate_z(shape, angle_degrees, center_x=0.0, center_y=0.0):
    if angle_degrees == 0:
        return shape
    trsf = gp_Trsf()
    axis = gp_Ax1(gp_Pnt(center_x, center_y, 0), gp_Dir(0, 0, 1))
    trsf.SetRotation(axis, math.radians(angle_degrees))
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


def build_pile_geometry(
    *,
    n_piles_per_cap: int = 4,
    pile_diameter: float = 400.0,
    pile_length: float = 5000.0,
    pile_spacing: float = 600.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
    top_z: float = 0.0,
    skew_angle: float = 0.0,
    rebar_main_diameter: float = 16.0,
    rebar_spacing_longitudinal: float = 150.0,
    rebar_transverse_diameter: float = 8.0,
    rebar_spacing_transverse: float = 200.0,
    rebar_cover: float = 40.0,
    include_reinforcement: bool = True
) -> dict:
    """
    Build parametric circular piles arranged in a 2x2 grid with reinforcement cages.

    Args:
        n_piles_per_cap: Number of piles (default 4)
        pile_diameter: Circular pile diameter (mm)
        pile_length: Pile embedment depth (mm)
        pile_spacing: Center-to-center spacing between piles (mm)
        center_x: Center X coordinate of the pile group (mm)
        center_y: Center Y coordinate of the pile group (mm)
        top_z: Top elevation of piles (interface with pile cap soffit) (mm)
        skew_angle: Skew angle in degrees
        rebar_main_diameter: Longitudinal bar diameter (mm)
        rebar_spacing_longitudinal: Nominal bar spacing (mm)
        rebar_transverse_diameter: Lateral tie diameter (mm)
        rebar_spacing_transverse: Tie spacing (mm)
        rebar_cover: Concrete cover (mm)
        include_reinforcement: Whether to generate rebar solids

    Returns:
        dict: List of pile solids, rebar shapes, and metadata.
    """
    bottom_z = top_z - pile_length
    radius = pile_diameter / 2.0
    bar_radius = rebar_main_diameter / 2.0
    tie_thickness = rebar_transverse_diameter

    # 2x2 grid relative offsets
    half_s = pile_spacing / 2.0
    offsets = [
        (-half_s, -half_s),
        (half_s, -half_s),
        (-half_s, half_s),
        (half_s, half_s)
    ]

    piles_concrete = []
    rebar_main = []
    rebar_ties = []

    # Cage pitch circle radius
    r_pitch = radius - rebar_cover - rebar_transverse_diameter - bar_radius
    num_bars = 6 if r_pitch <= 0 else max(6, int(round((2.0 * math.pi * r_pitch) / rebar_spacing_longitudinal)))
    d_theta = (2.0 * math.pi) / num_bars

    bar_len = pile_length - (2.0 * rebar_cover)
    bar_start_z = bottom_z + rebar_cover

    num_tie_segments = 12
    seg_d_theta = (2.0 * math.pi) / num_tie_segments
    r_tie_center = radius - rebar_cover - (rebar_transverse_diameter / 2.0)
    tie_z_start = bottom_z + rebar_cover + (rebar_transverse_diameter / 2.0)
    tie_z_end = top_z - rebar_cover - (rebar_transverse_diameter / 2.0)
    num_ties = max(2, int((tie_z_end - tie_z_start) / (rebar_spacing_transverse * 2.0)) + 1)
    actual_tie_pitch = (tie_z_end - tie_z_start) / max(1, num_ties - 1)

    for px_off, py_off in offsets:
        px = center_x + px_off
        py = center_y + py_off

        # 1. Concrete cylinder
        p_axis = gp_Ax2(gp_Pnt(px, py, bottom_z), gp_Dir(0, 0, 1))
        p_solid = BRepPrimAPI_MakeCylinder(p_axis, radius, pile_length).Shape()
        piles_concrete.append(p_solid)

        # 2. Reinforcement cage for this pile
        if include_reinforcement and r_pitch > 0:
            # Longitudinal bars
            for b_idx in range(num_bars):
                ang = b_idx * d_theta
                bx = px + r_pitch * math.cos(ang)
                by = py + r_pitch * math.sin(ang)
                b_ax = gp_Ax2(gp_Pnt(bx, by, bar_start_z), gp_Dir(0, 0, 1))
                bar_solid = BRepPrimAPI_MakeCylinder(b_ax, bar_radius, bar_len).Shape()
                rebar_main.append(bar_solid)

            # Transverse ties
            for k in range(num_ties):
                tz = tie_z_start + k * actual_tie_pitch
                for s_idx in range(num_tie_segments):
                    ang1 = s_idx * seg_d_theta
                    ang2 = (s_idx + 1) * seg_d_theta
                    p1 = gp_Pnt(px + r_tie_center * math.cos(ang1), py + r_tie_center * math.sin(ang1), tz)
                    p2 = gp_Pnt(px + r_tie_center * math.cos(ang2), py + r_tie_center * math.sin(ang2), tz)
                    dx = p2.X() - p1.X()
                    dy = p2.Y() - p1.Y()
                    seg_len = math.sqrt(dx*dx + dy*dy)
                    if seg_len > 1e-4:
                        seg_dir = gp_Dir(dx / seg_len, dy / seg_len, 0)
                        seg_ax = gp_Ax2(p1, seg_dir)
                        seg_cyl = BRepPrimAPI_MakeCylinder(seg_ax, tie_thickness / 2.0, seg_len).Shape()
                        rebar_ties.append(seg_cyl)

    if skew_angle != 0.0:
        piles_concrete = [_rotate_z(p, skew_angle, center_x, center_y) for p in piles_concrete]
        rebar_main = [_rotate_z(b, skew_angle, center_x, center_y) for b in rebar_main]
        rebar_ties = [_rotate_z(t, skew_angle, center_x, center_y) for t in rebar_ties]

    all_rebars = rebar_main + rebar_ties
    rebar_compound = _make_compound(all_rebars)
    concrete_compound = _make_compound(piles_concrete)

    return {
        "concrete": piles_concrete,
        "concrete_compound": concrete_compound,
        "rebar_main": rebar_main,
        "rebar_ties": rebar_ties,
        "rebars": all_rebars,
        "rebar_compound": rebar_compound,
        "n_piles": n_piles_per_cap,
        "pile_diameter": pile_diameter,
        "pile_length": pile_length,
        "pile_spacing": pile_spacing,
        "center_x": center_x,
        "center_y": center_y,
        "top_z": top_z,
        "bottom_z": bottom_z
    }

