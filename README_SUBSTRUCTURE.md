# OsdagBridge Substructure CAD & IFC Integration

This repository extension introduces full parametric 3D CAD modeling of the bridge substructure (Pier, Pier Cap, Pile Cap, Piles, and Reinforcement) using OpenCASCADE (`pythonocc-core`), seamlessly integrated into the OsdagBridge CAD generation, GUI rendering, and IFC4 BIM export workflows.

---

## File Structure & Module Organization

```
OsdagBridge/
├── src/osdagbridge/
│   ├── core/
│   │   ├── bridge_components/
│   │   │   ├── sub_structure/
│   │   │   │   ├── pier/
│   │   │   │   │   ├── builder.py            # [NEW] Parametric circular column & rebar cage builder
│   │   │   │   │   ├── geometry.py
│   │   │   │   │   └── checks.py
│   │   │   │   └── pier_cap/
│   │   │   │       ├── builder.py            # [NEW] Hammerhead/trapezoidal cap & stirrup builder
│   │   │   │       └── geometry.py
│   │   │   └── foundation/
│   │   │       ├── pile_cap/
│   │   │       │   ├── builder.py            # [NEW] Rectangular pile cap & 2-way mat rebar builder
│   │   │       │   └── geometry.py
│   │   │       └── pile/
│   │   │           ├── builder.py            # [NEW] 2x2 circular pile grid & cage builder
│   │   │           ├── geometry.py
│   │   │           └── checks.py
│   │   ├── bridge_types/plate_girder/
│   │   │   ├── cad_generator.py              # [MODIFIED] Added substructure placement & compound integration
│   │   │   └── dto.py                        # [MODIFIED] Added default parametric dimensions to BridgeParametersDTO
│   │   └── ifc_export_bridge/
│   │       ├── bridge_geometry_mapper.py     # [MODIFIED] Added native circle profile translator
│   │       ├── bridge_cad_extraction.py      # [MODIFIED] Added substructure object extractor
│   │       └── bridge_ifc_generator.py       # [MODIFIED] Created Substructure storey & mapped IFC entities
│   └── desktop/ui/
│       └── cad_3d.py                         # [MODIFIED] Registered AIS shapes (semi-transparent concrete & opaque rebar) + selector checkboxes
└── tests/unit/
    └── test_substructure.py                  # [NEW] Comprehensive unit test suite
```

---

## Parametric Dimensions (Default in mm)

| Component | Parameter | Default Value | Notes |
|:---|:---|:---:|:---|
| **Pier Column** | `pier_diameter`<br>`pier_height` | `800 mm`<br>`3000 mm` | Circular column extending from pile cap to pier cap soffit |
| **Pier Cap** | `pier_cap_top_width`<br>`pier_cap_bottom_width`<br>`pier_cap_depth`<br>`pier_cap_length` | `3000 mm`<br>`1200 mm`<br>`600 mm`<br>`1200 mm` | Inverted trapezoid / hammerhead shape; parameterized along transverse axis |
| **Pile Cap** | `pile_cap_length`<br>`pile_cap_width`<br>`pile_cap_depth` | `2200 mm`<br>`1200 mm`<br>`600 mm` | Rectangular footing prism |
| **Piles** | `n_piles_per_cap`<br>`pile_diameter`<br>`pile_length`<br>`pile_spacing` | `4`<br>`400 mm`<br>`5000 mm`<br>`600 mm` | Arranged symmetrically in a 2×2 grid |
| **Reinforcement** | `rebar_main_diameter`<br>`rebar_spacing_longitudinal`<br>`rebar_transverse_diameter`<br>`rebar_spacing_transverse`<br>`rebar_cover` | `16 mm`<br>`150 mm`<br>`8 mm`<br>`200 mm`<br>`40 mm` | Longitudinal main bars on pitch circle; circular ties/hoops; orthogonal mats |

---

## Visualization & UI Controls

- **Concrete solids**: Semi-transparent rendering (`transparency = 0.65`, corresponding to `opacity = 0.35`) in `cad_3d.py`.
- **Rebar solids**: Opaque steel/rust colored cylinders (`REBAR_COLOR = Quantity_Color(180/255, 80/255, 45/255, Quantity_TOC_RGB)`).
- **Interactive Checkboxes**:
  - `Bridge` (Model toggle): Shows full assembly (superstructure + substructure).
  - `Pier Cap`, `Pier`, `Pile Cap`, `Pile`: Toggle individual concrete components.
  - `Reinforcement`: Toggle internal steel rebar cages and mats.

---

## IFC4 BIM Export Architecture

When exporting to IFC (`File` ➔ `Save 3D CAD Model` ➔ `.ifc`):
1. **Spatial Decomposition**:
   - `IfcProject` ➔ `IfcSite` ➔ `IfcBuilding`
     - `IfcBuildingStorey` ("Superstructure"): Girders, cross bracings, deck slab, crash barriers, railings.
     - `IfcBuildingStorey` ("Substructure"): Pier caps (`IfcBeam`), piers (`IfcColumn`), pile caps (`IfcFooting`), piles (`IfcPile`), and rebars (`IfcReinforcingBar`).
2. **Metadata & Property Sets**:
   - `Pset_OsdagSubstructure`: Component dimensions, concrete grade, materials.
   - `Pset_OsdagRebar`: Bar diameter, cut length, steel grade.
   - Fully compatible with BIM authoring tools (Autodesk Revit, Solibri, BIMcollab) for automated Bill of Quantities (BOQ).

---

## Running the Application

```bash
# 1. Activate environment
conda activate osdagbridge-env

# 2. Launch OsdagBridge GUI
cd src
python -m osdagbridge.desktop
```
