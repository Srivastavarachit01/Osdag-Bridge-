"""
Pile Cap Builder for Foundation
===============================

This module generates parametric 3D CAD models of rectangular pile caps
and their internal orthogonal reinforcement mats using pythonOCC.

Parameters:
    - pile_cap_length: Dimension along longitudinal X (default: 2200 mm)
    - pile_cap_width: Dimension along transverse Y (default: 1200 mm)
    - pile_cap_depth: Vertical thickness (default: 600 mm)
    - rebar_main_diameter: Mat bar diameter (default: 16 mm)
    - rebar_spacing_longitudinal: Grid spacing between bars (default: 150 mm)
    - rebar_transverse_diameter: Secondary/transverse bar diameter (default: 8 mm)
    - rebar_spacing_transverse: Transverse bar spacing (default: 200 mm)
    - rebar_cover: Clear concrete cover (default: 40 mm)
"""

import math
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Ax2, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
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


def build_pile_cap_geometry(
    *,
    pile_cap_length: float = 2200.0,
    pile_cap_width: float = 1200.0,
    pile_cap_depth: float = 600.0,
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
    Build parametric rectangular pile cap solid and internal reinforcement mats.

    Args:
        pile_cap_length: Dimension along X (mm)
        pile_cap_width: Dimension along Y (mm)
        pile_cap_depth: Thickness along Z (mm)
        center_x: Center X coordinate (mm)
        center_y: Center Y coordinate (mm)
        top_z: Elevation of top surface (mm)
        skew_angle: Skew angle in degrees
        rebar_main_diameter: Diameter of mat reinforcement (mm)
        rebar_spacing_longitudinal: Spacing of bars along X grid (mm)
        rebar_transverse_diameter: Diameter of tie/transverse reinforcement (mm)
        rebar_spacing_transverse: Spacing of bars along Y grid (mm)
        rebar_cover: Concrete cover (mm)
        include_reinforcement: Whether to generate rebar solids

    Returns:
        dict: Concrete solid, rebar shapes, and metadata.
    """
    bottom_z = top_z - pile_cap_depth
    half_l = pile_cap_length / 2.0
    half_w = pile_cap_width / 2.0

    # 1. Concrete Pile Cap Solid (Box)
    box = BRepPrimAPI_MakeBox(pile_cap_length, pile_cap_width, pile_cap_depth).Shape()
    concrete_solid = _translate(
        box,
        center_x - half_l,
        center_y - half_w,
        bottom_z
    )

    if skew_angle != 0.0:
        concrete_solid = _rotate_z(concrete_solid, skew_angle, center_x, center_y)

    rebar_mats = []

    if include_reinforcement:
        bar_rad = rebar_main_diameter / 2.0
        inner_half_l = half_l - rebar_cover
        inner_half_w = half_w - rebar_cover
        span_x = 2.0 * inner_half_l
        span_y = 2.0 * inner_half_w

        # Bottom Mat: X-direction and Y-direction bars
        bot_z_x = bottom_z + rebar_cover + bar_rad
        bot_z_y = bottom_z + rebar_cover + 2.0 * bar_rad + bar_rad

        # Top Mat: X-direction and Y-direction bars
        top_z_y = top_z - rebar_cover - bar_rad
        top_z_x = top_z - rebar_cover - 2.0 * bar_rad - bar_rad

        # X-direction bars for bottom and top mats (running along X)
        num_bars_y = max(3, int(span_y / rebar_spacing_longitudinal) + 1)
        step_y = span_y / max(1, num_bars_y - 1)

        for i in range(num_bars_y):
            by = -inner_half_w + i * step_y
            # Bottom mat X-bar
            b_pt_bot = gp_Pnt(-inner_half_l, by, bot_z_x)
            b_ax_bot = gp_Ax2(b_pt_bot, gp_Dir(1, 0, 0))
            rebar_mats.append(BRepPrimAPI_MakeCylinder(b_ax_bot, bar_rad, span_x).Shape())

            # Top mat X-bar
            b_pt_top = gp_Pnt(-inner_half_l, by, top_z_x)
            b_ax_top = gp_Ax2(b_pt_top, gp_Dir(1, 0, 0))
            rebar_mats.append(BRepPrimAPI_MakeCylinder(b_ax_top, bar_rad, span_x).Shape())

        # Y-direction bars for bottom and top mats (running along Y)
        num_bars_x = max(3, int(span_x / rebar_spacing_transverse) + 1)
        step_x = span_x / max(1, num_bars_x - 1)

        for j in range(num_bars_x):
            bx = -inner_half_l + j * step_x
            # Bottom mat Y-bar
            b_pt_bot = gp_Pnt(bx, -inner_half_w, bot_z_y)
            b_ax_bot = gp_Ax2(b_pt_bot, gp_Dir(0, 1, 0))
            rebar_mats.append(BRepPrimAPI_MakeCylinder(b_ax_bot, bar_rad, span_y).Shape())

            # Top mat Y-bar
            b_pt_top = gp_Pnt(bx, -inner_half_w, top_z_y)
            b_ax_top = gp_Ax2(b_pt_top, gp_Dir(0, 1, 0))
            rebar_mats.append(BRepPrimAPI_MakeCylinder(b_ax_top, bar_rad, span_y).Shape())

        # Position and rotate mats
        rebar_mats = [_rotate_z(_translate(m, center_x, center_y, 0.0), skew_angle, center_x, center_y) for m in rebar_mats]

    rebar_compound = _make_compound(rebar_mats)

    return {
        "concrete": concrete_solid,
        "rebar_mats": rebar_mats,
        "rebars": rebar_mats,
        "rebar_compound": rebar_compound,
        "pile_cap_length": pile_cap_length,
        "pile_cap_width": pile_cap_width,
        "pile_cap_depth": pile_cap_depth,
        "center_x": center_x,
        "center_y": center_y,
        "top_z": top_z,
        "bottom_z": bottom_z
    }

