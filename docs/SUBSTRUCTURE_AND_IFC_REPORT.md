# Technical Report: Parametric 3D CAD Modeling of Bridge Substructure and IFC Workflow Integration

**Project**: OsdagBridge (IIT Bombay / Osdag Team)  
**Module**: Steel Plate Girder Bridge Substructure Modeling & OpenBIM (IFC4) Workflow  
**Author / Contributor**: Screening Task Submission  

---

## 1. Methodology

### 1.1 Structural Architecture & Scope
Bridge substructures transfer dead loads, live traffic loads, and environmental forces (wind, seismic, braking) from the bridge superstructure down to competent bearing strata. In the OsdagBridge architecture, the superstructure (steel plate girders, cross bracings, concrete deck slab, crash barriers, and railings) was previously implemented, but the substructure modules remained empty stubs.

This implementation introduces complete parametric 3D CAD geometry for:
1. **Hammerhead / Inverted Trapezoidal Pier Cap**:
   - Cantilevers symmetrically outward in the transverse ($Y$) direction to support multiple steel plate girders via elastomeric/steel bearing pedestals.
   - Profile defined in the $Y$-$Z$ plane and extruded longitudinally along the $X$-axis.
2. **Circular Pier Column**:
   - Central compression column transferring load from the pier cap soffit to the pile cap.
   - Modeled with OpenCASCADE `BRepPrimAPI_MakeCylinder`.
3. **Rectangular Pile Cap**:
   - Rigid reinforced concrete footing distributing column axial force and moments across a group of foundation piles.
   - Modeled with `BRepPrimAPI_MakeBox`.
4. **Group Piles (2×2 Grid)**:
   - Deep foundation bored cast-in-place circular piles arranged symmetrically beneath the pile cap.
5. **Visible Internal Steel Reinforcement**:
   - Longitudinal main tension/compression bars placed on pitch circles and planar mats.
   - Transverse lateral ties (stirrups and circular hoops) placed along column and pile heights at structural pitch.

### 1.2 Coordinate System Alignment
To guarantee seamless compatibility with the superstructure:
- **Global $X$-axis**: Longitudinal span direction ($X = 0$ at left bearing centerline, $X = L$ at right bearing centerline).
- **Global $Y$-axis**: Transverse direction (bridge centerline at $Y = 0$, deck extends from $-W_{deck}/2$ to $+W_{deck}/2$).
- **Global $Z$-axis**: Vertical elevation ($Z = 0$ at girder bottom flange datum, positive upwards).
- **Substructure Positioning**:
  - Left support unit placed at $X = 0$, $Y = 0$.
  - Right support unit placed at $X = L$, $Y = 0$.
  - Pier Cap Top Elevation: Positioned directly beneath bearing assemblies:
    $$Z_{cap\_top} = Z_{contact} - h_{bearing} = -D/2 - T_{fb} - 120\text{ mm}$$
  - Pier Column Top: $Z_{pier\_top} = Z_{cap\_top} - D_{cap}$
  - Pile Cap Top: $Z_{pile\_cap\_top} = Z_{pier\_top} - H_{pier}$
  - Piles Top: $Z_{pile\_top} = Z_{pile\_cap\_top} - D_{pile\_cap}$

### 1.3 PythonOCC Geometric Algorithms
- **Pier (`sub_structure/pier/builder.py`)**:
  - Uses `gp_Ax2` and `BRepPrimAPI_MakeCylinder` for column concrete.
  - Rebar cage pitch circle radius:
    $$R_{pc} = R_{pier} - \text{cover} - \phi_{tie} - \frac{\phi_{main}}{2} = 400 - 40 - 8 - 8 = 344\text{ mm}$$
  - Main bars distributed radially at $\theta_i = \frac{2\pi i}{N_{bars}}$.
  - Circular hoops segmented into 16 cylindrical arc primitives along the height at spacing $s_t = 200\text{ mm}$.
- **Pier Cap (`sub_structure/pier_cap/builder.py`)**:
  - Trapezoid polygon face formed via `BRepBuilderAPI_MakePolygon` and `BRepBuilderAPI_MakeFace`.
  - Linear extrusion along $X$ via `BRepPrimAPI_MakePrism`.
  - Closed stirrup loops constructed with 4 corner cylindrical legs.
- **Pile Cap (`foundation/pile_cap/builder.py`)**:
  - `BRepPrimAPI_MakeBox` centered in $X$ and $Y$.
  - Orthogonal top and bottom rebar mats with longitudinal ($X$) and transverse ($Y$) cylindrical bars honoring $40\text{ mm}$ clear cover.
- **Piles (`foundation/pile/builder.py`)**:
  - 4 cylinders located at $(\pm s_p/2, \pm s_p/2)$ where $s_p = 600\text{ mm}$.
  - Internal 6-bar circular cage per pile.

---

## 2. IFC4 Workflow Integration

### 2.1 OpenBIM Architecture
Building Information Modeling (BIM) mandates structured spatial decomposition and semantic typing:
- **Spatial Hierarchy**:
  $$\text{IfcProject} \longrightarrow \text{IfcSite} \longrightarrow \text{IfcBuilding} \longrightarrow \begin{cases} \text{IfcBuildingStorey [Superstructure]} \\ \text{IfcBuildingStorey [Substructure]} \end{cases}$$
- **Substructure Semantic Entity Mapping**:
  - Pier Columns $\rightarrow$ `IfcColumn`
  - Pier Cap $\rightarrow$ `IfcBeam` (or `IfcFooting`)
  - Pile Cap $\rightarrow$ `IfcFooting` (`PredefinedType="PAD_FOOTING"`)
  - Piles $\rightarrow$ `IfcPile` (`PredefinedType="BORED"`)
  - Internal Rebars $\rightarrow$ `IfcReinforcingBar`

### 2.2 Extraction & Mapping Engine
1. **Extraction (`PlateGirderIFCExtractor`)**:
   - `_extract_substructure()` computes exact world coordinates and returns standardized `ExtractedObject` records.
2. **Geometry Mapping (`BridgeGeometryMapper`)**:
   - Added `create_circle_profile(radius)` utilizing `IfcCircleProfileDef`.
   - Extruded swept solid representations (`IfcExtrudedAreaSolid`) ensuring lightweight, non-tessellated parametric geometry.
3. **Metadata & Property Sets (`BridgeMetadataMapper`)**:
   - `Pset_OsdagSubstructure`:
     - `ComponentType`, `Diameter_m`, `Length_m`, `Depth_m`, `ConcreteGrade`, `Material`.
   - `Pset_OsdagRebar`:
     - `NominalDiameter_mm`, `BarLength_m`, `SteelGrade="Fe 500"`.
   - Guarantees immediate compatibility with Revit, Navisworks, and Solibri for automated Bill of Quantities (BOQ).

---

## 3. Challenges & Solutions

| Challenge | Root Cause | Solution Implemented |
|:---|:---|:---|
| **Coordinate System Inversion** | Plate girder CAD generation historically negates skew angle to match 2D drafting conventions ($Y$-inversion). | Substructure builders accept explicit `center_x`, `center_y`, `top_z`, and `skew_angle`, performing rotation around the vertical column axis $Z$ through `gp_Ax1`. |
| **Rebar Visibility through Concrete** | OpenCASCADE AIS rendering hides internal shapes if concrete is opaque. | Configured `cad_3d.py` and `cad_generator.py` with `transparency = 0.65` (`opacity = 0.35`) for concrete solids and opaque steel color (`RGB 180, 80, 45`) for rebars. |
| **Boolean Cut Performance for Hoops** | Applying `BRepAlgoAPI_Cut` on cylinders to create hollow circular ties causes high CPU overhead and topological instability. | Modeled circular ties and stirrups as segmented cylindrical sweeps along the pitch circle, yielding 100% robust solid geometry without Boolean bottlenecks. |
| **Dual Storey IFC Hierarchy** | Previous IFC generator contained only a single `Superstructure` storey. | Extended `initialize_file()` with a dedicated `Substructure` storey related via `IfcRelAggregates`, maintaining strict IFC4 WR21 schema validation. |

---

## 4. References

1. **OpenCASCADE Technology (OCCT)**: 3D Surface & Solid Modeling Library, version 7.x documentation.
2. **pythonocc-core**: Python bindings for OpenCASCADE Technology (OCC).
3. **BuildingSMART International**: Industry Foundation Classes (IFC) 4 (ISO 16739-1:2018) Specification.
4. **IfcOpenShell**: Open source IFC library and geometry engine.
5. **IRC:5-2015**: Standard Specifications and Code of Practice for Road Bridges, Section I - General Features of Design.
6. **IRC:112-2020**: Code of Practice for Concrete Road Bridges (Design & Detailing of RCC Members).
7. **IS 1786:2008**: High Strength Deformed Steel Bars and Wires for Concrete Reinforcement.

