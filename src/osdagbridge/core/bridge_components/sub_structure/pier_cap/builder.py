"""
Pier Cap Builder for Bridge Substructure
========================================

This module generates parametric 3D CAD models of trapezoidal / hammerhead pier caps
and their internal steel reinforcement using pythonOCC.

Parameters:
    - pier_cap_top_width: Transverse width at top surface (default: 3000 mm)
    - pier_cap_bottom_width: Transverse width at bottom soffit (default: 1200 mm)
    - pier_cap_depth: Overall vertical depth (default: 600 mm)
    - pier_cap_length: Longitudinal dimension along span (default: 1200 mm)
    - rebar_main_diameter: Longitudinal bar diameter (default: 16 mm)
    - rebar_transverse_diameter: Stirrup bar diameter (default: 8 mm)
    - rebar_spacing_transverse: Spacing between stirrup frames (default: 200 mm)
    - rebar_cover: Clear concrete cover (default: 40 mm)
"""

import math
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Ax2, gp_Dir
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder
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


def build_pier_cap_geometry(
    *,
    pier_cap_top_width: float = 3000.0,
    pier_cap_bottom_width: float = 1200.0,
    pier_cap_depth: float = 600.0,
    pier_cap_length: float = 1200.0,
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
    Build parametric hammerhead/trapezoidal pier cap solid and reinforcement.

    Args:
        pier_cap_top_width: Width at top surface along transverse Y (mm)
        pier_cap_bottom_width: Width at bottom soffit along transverse Y (mm)
        pier_cap_depth: Depth/height of cap along Z (mm)
        pier_cap_length: Length of cap along longitudinal X (mm)
        center_x: Center X coordinate (mm)
        center_y: Center Y coordinate (mm)
        top_z: Top surface Z elevation (mm)
        skew_angle: Skew angle in degrees
        rebar_main_diameter: Main rebar diameter (mm)
        rebar_spacing_longitudinal: Spacing between longitudinal rebars (mm)
        rebar_transverse_diameter: Stirrup rebar diameter (mm)
        rebar_spacing_transverse: Spacing between stirrups (mm)
        rebar_cover: Concrete cover (mm)
        include_reinforcement: Whether to generate rebar solids

    Returns:
        dict: Concrete solid, rebar shapes, and metadata.
    """
    bottom_z = top_z - pier_cap_depth
    half_top_w = pier_cap_top_width / 2.0
    half_bot_w = pier_cap_bottom_width / 2.0
    half_l = pier_cap_length / 2.0

    # 1. Concrete Pier Cap Solid
    # Profile in Y-Z plane at local X = -half_l
    p1 = gp_Pnt(0.0, -half_top_w, top_z)
    p2 = gp_Pnt(0.0, half_top_w, top_z)
    p3 = gp_Pnt(0.0, half_bot_w, bottom_z)
    p4 = gp_Pnt(0.0, -half_bot_w, bottom_z)

    poly = BRepBuilderAPI_MakePolygon(p1, p2, p3, p4, True)
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()

    # Extrude along X by pier_cap_length
    prism = BRepPrimAPI_MakePrism(face, gp_Vec(pier_cap_length, 0.0, 0.0)).Shape()

    # Center along X at 0
    concrete_solid = _translate(prism, -half_l + center_x, center_y, 0.0)

    # Apply skew angle if present
    if skew_angle != 0.0:
        concrete_solid = _rotate_z(concrete_solid, skew_angle, center_x, center_y)

    rebar_main = []
    rebar_stirrups = []

    if include_reinforcement:
        # Generate rebar within the trapezoidal cross-section
        bar_rad = rebar_main_diameter / 2.0
        stirrup_rad = rebar_transverse_diameter / 2.0

        # Top longitudinal bars running along Y
        top_bar_z = top_z - rebar_cover - stirrup_rad - bar_rad
        bot_bar_z = bottom_z + rebar_cover + stirrup_rad + bar_rad

        # Widths available inside stirrups
        inner_top_half_w = half_top_w - rebar_cover - rebar_transverse_diameter
        inner_bot_half_w = half_bot_w - rebar_cover - rebar_transverse_diameter
        inner_half_l = half_l - rebar_cover - rebar_transverse_diameter

        # Longitudinal bars running along X (spanning the length of the pier cap)
        # Top layer bars
        num_x_bars_top = max(3, int((2.0 * inner_top_half_w) / rebar_spacing_longitudinal) + 1)
        step_y_top = (2.0 * inner_top_half_w) / max(1, num_x_bars_top - 1)
        for i in range(num_x_bars_top):
            by = -inner_top_half_w + i * step_y_top
            start_pt = gp_Pnt(-inner_half_l, by, top_bar_z)
            b_axis = gp_Ax2(start_pt, gp_Dir(1, 0, 0))
            bar = BRepPrimAPI_MakeCylinder(b_axis, bar_rad, 2.0 * inner_half_l).Shape()
            rebar_main.append(bar)

        # Bottom layer bars
        num_x_bars_bot = max(2, int((2.0 * inner_bot_half_w) / rebar_spacing_longitudinal) + 1)
        step_y_bot = (2.0 * inner_bot_half_w) / max(1, num_x_bars_bot - 1)
        for i in range(num_x_bars_bot):
            by = -inner_bot_half_w + i * step_y_bot
            start_pt = gp_Pnt(-inner_half_l, by, bot_bar_z)
            b_axis = gp_Ax2(start_pt, gp_Dir(1, 0, 0))
            bar = BRepPrimAPI_MakeCylinder(b_axis, bar_rad, 2.0 * inner_half_l).Shape()
            rebar_main.append(bar)

        # Transverse stirrup hoops along X
        num_stirrups = max(2, int((2.0 * inner_half_l) / rebar_spacing_transverse) + 1)
        stirrup_step_x = (2.0 * inner_half_l) / max(1, num_stirrups - 1)

        for k in range(num_stirrups):
            sx = -inner_half_l + k * stirrup_step_x
            # 4 corners of stirrup in Y-Z plane
            sp1 = gp_Pnt(sx, -inner_top_half_w, top_z - rebar_cover)
            sp2 = gp_Pnt(sx, inner_top_half_w, top_z - rebar_cover)
            sp3 = gp_Pnt(sx, inner_bot_half_w, bottom_z + rebar_cover)
            sp4 = gp_Pnt(sx, -inner_bot_half_w, bottom_z + rebar_cover)

            # Create 4 cylindrical legs of stirrup
            corners = [sp1, sp2, sp3, sp4]
            for c_idx in range(4):
                ca = corners[c_idx]
                cb = corners[(c_idx + 1) % 4]
                v_dx = cb.X() - ca.X()
                v_dy = cb.Y() - ca.Y()
                v_dz = cb.Z() - ca.Z()
                leg_len = math.sqrt(v_dx*v_dx + v_dy*v_dy + v_dz*v_dz)
                if leg_len > 1e-4:
                    leg_dir = gp_Dir(v_dx / leg_len, v_dy / leg_len, v_dz / leg_len)
                    leg_ax = gp_Ax2(ca, leg_dir)
                    leg_solid = BRepPrimAPI_MakeCylinder(leg_ax, stirrup_rad, leg_len).Shape()
                    rebar_stirrups.append(leg_solid)

        # Translate and rotate rebars
        rebar_main = [_rotate_z(_translate(b, center_x, center_y, 0.0), skew_angle, center_x, center_y) for b in rebar_main]
        rebar_stirrups = [_rotate_z(_translate(s, center_x, center_y, 0.0), skew_angle, center_x, center_y) for s in rebar_stirrups]

    all_rebars = rebar_main + rebar_stirrups
    rebar_compound = _make_compound(all_rebars)

    return {
        "concrete": concrete_solid,
        "rebar_main": rebar_main,
        "rebar_stirrups": rebar_stirrups,
        "rebars": all_rebars,
        "rebar_compound": rebar_compound,
        "top_width": pier_cap_top_width,
        "bottom_width": pier_cap_bottom_width,
        "depth": pier_cap_depth,
        "length": pier_cap_length,
        "center_x": center_x,
        "center_y": center_y,
        "top_z": top_z,
        "bottom_z": bottom_z
    }

