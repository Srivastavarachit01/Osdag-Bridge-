"""
End-to-end integration test for Substructure 3D CAD modeling and IFC Export.
"""
import os
import unittest
import ifcopenshell

from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
)
from osdagbridge.core.bridge_types.plate_girder.cad_generator import PlateGirderCADGenerator
from osdagbridge.core.ifc_export_bridge.bridge_cad_extraction import PlateGirderIFCExtractor
from osdagbridge.core.ifc_export_bridge.bridge_ifc_generator import BridgeIfcGenerator


class TestSubstructureIFCE2E(unittest.TestCase):
    """End-to-end test verifying CAD generation and IFC export with Substructure."""

    @classmethod
    def setUpClass(cls):
        _dims = SectionDimsDTO(leg_h=100.0, leg_w=50.0, connection_type="LONGER_LEG")
        _idims = ISectionDimsDTO(depth=500.0, flange_width=200.0, web_thickness=10.0, flange_thickness=16.0)

        cls.dto = BridgeParametersDTO(
            steel_grade="E250",
            concrete_grade="M35",
            span_length_L=20000.0,
            girder_section_d=1200.0,
            girder_section_bf=400.0,
            girder_section_bf_b=400.0,
            girder_section_tf=25.0,
            girder_section_tf_b=25.0,
            girder_section_tw=12.0,
            num_girders=3,
            girder_spacing=2500.0,
            skew_angle=0.0,
            carriageway_width=7500.0,
            deck_thickness=250.0,
            footpath_config="NONE",
            footpath_width=0.0,
            railing_width=300.0,
            barrier_type="Rigid",
            crash_barrier_subtype="Concrete Barrier",
            enable_median=False,
            median_type="",
            rail_count=3,
            railing_type="steel",
            include_intermediate_stiffeners=False,
            intermediate_stiffener_spacing=2000.0,
            intermediate_stiffener_thickness=12.0,
            intermediate_stiffener_outstand=None,
            num_end_stiffener_pairs=2,
            end_stiffener_thickness=16.0,
            end_stiffener_outstand=None,
            include_longitudinal_stiffeners=False,
            num_longitudinal_stiffeners=1,
            longitudinal_stiffener_thickness=12.0,
            longitudinal_stiffener_outstand=None,
            cross_bracing_spacing=5000.0,
            bracing_type="X",
            x_bracket_option="NONE",
            k_top_bracket=False,
            diagonal_section_type="ANGLE",
            diagonal_section_dims=_dims,
            diagonal_thickness=8.0,
            top_chord_section_type="ANGLE",
            top_chord_section_dims=_dims,
            top_chord_thickness=8.0,
            bottom_chord_section_type="ANGLE",
            bottom_chord_section_dims=_dims,
            bottom_chord_thickness=8.0,
            end_diaphragm_type="Cross Bracing",
            end_diaphragm_spacing=100.0,
            end_diaphragm_bracing_type="X",
            end_diaphragm_diagonal_section_type="ANGLE",
            end_diaphragm_diagonal_section_dims=_dims,
            end_diaphragm_diagonal_thickness=8.0,
            end_diaphragm_top_chord_section_type="ANGLE",
            end_diaphragm_top_chord_section_dims=_dims,
            end_diaphragm_top_chord_thickness=8.0,
            end_diaphragm_bottom_chord_section_type="ANGLE",
            end_diaphragm_bottom_chord_section_dims=_dims,
            end_diaphragm_bottom_chord_thickness=8.0,
            end_diaphragm_section="I_SECTION",
            end_diaphragm_dims=_idims,
            # Substructure parameters
            pier_diameter=800.0,
            pier_height=3000.0,
            pier_cap_top_width=3000.0,
            pier_cap_bottom_width=1200.0,
            pier_cap_depth=600.0,
            pier_cap_length=1200.0,
            pile_cap_length=2200.0,
            pile_cap_width=1200.0,
            pile_cap_depth=600.0,
            n_piles_per_cap=4,
            pile_diameter=400.0,
            pile_length=5000.0,
            pile_spacing=600.0,
            rebar_main_diameter=16.0,
            rebar_spacing_longitudinal=150.0,
            rebar_transverse_diameter=8.0,
            rebar_spacing_transverse=200.0,
            rebar_cover=40.0,
        )

        cls.generator = PlateGirderCADGenerator(cls.dto)
        cls.model_data = cls.generator.generate(cls.dto)

    def test_01_cad_model_data_contains_substructure(self):
        """Verify CAD model_data dictionary includes all substructure components."""
        expected_keys = [
            "substructure_concrete",
            "substructure_rebar",
            "pier_caps",
            "piers",
            "pile_caps",
            "piles",
        ]
        for key in expected_keys:
            self.assertIn(key, self.model_data, f"Missing key in model_data: {key}")
            val = self.model_data[key]
            self.assertIsNotNone(val, f"Value for {key} is None")
            if isinstance(val, list):
                self.assertGreater(len(val), 0, f"List for {key} is empty")
                for item in val:
                    self.assertFalse(item.IsNull(), f"Item in {key} is null")
            else:
                self.assertFalse(val.IsNull(), f"OpenCASCADE shape for {key} is null")

    def test_02_ifc_extraction(self):
        """Verify PlateGirderIFCExtractor extracts substructure records."""
        extractor = PlateGirderIFCExtractor(self.generator)
        extracted = extractor.extract()

        # Check pier caps
        self.assertIn("pier_caps", extracted)
        self.assertEqual(len(extracted["pier_caps"]), 2)
        for pc in extracted["pier_caps"]:
            self.assertEqual(pc.top_width, 3000.0)
            self.assertEqual(pc.bottom_width, 1200.0)
            self.assertEqual(pc.depth, 600.0)
            self.assertEqual(pc.length, 1200.0)

        # Check piers
        self.assertIn("piers", extracted)
        self.assertEqual(len(extracted["piers"]), 2)
        for p in extracted["piers"]:
            self.assertEqual(p.diameter, 800.0)
            self.assertEqual(p.height, 3000.0)

        # Check pile caps
        self.assertIn("pile_caps", extracted)
        self.assertEqual(len(extracted["pile_caps"]), 2)
        for pc in extracted["pile_caps"]:
            self.assertEqual(pc.length, 2200.0)
            self.assertEqual(pc.width, 1200.0)
            self.assertEqual(pc.depth, 600.0)

        # Check piles (2 substructures * 4 piles = 8 piles)
        self.assertIn("piles", extracted)
        self.assertEqual(len(extracted["piles"]), 8)
        for pl in extracted["piles"]:
            self.assertEqual(pl.diameter, 400.0)
            self.assertEqual(pl.length, 5000.0)

        # Check rebars
        self.assertIn("reinforcement", extracted)
        self.assertGreater(len(extracted["reinforcement"]), 0)

    def test_03_ifc_generation_and_semantic_validation(self):
        """Generate IFC file and validate entities, properties, and spatial structure."""
        extractor = PlateGirderIFCExtractor(self.generator)
        extracted = extractor.extract()

        output_path = "/tmp/test_plate_girder_bridge_substructure.ifc"
        if os.path.exists(output_path):
            os.remove(output_path)

        ifc_gen = BridgeIfcGenerator(output_path)
        ifc_gen.generate_from_extracted_data(extracted, self.generator)
        self.assertTrue(os.path.exists(output_path), "IFC file was not created on disk")

        # Open and inspect with ifcopenshell
        ifc_file = ifcopenshell.open(output_path)

        # Check schema
        self.assertEqual(ifc_file.schema, "IFC4")

        # 1. Check spatial hierarchy
        storeys = ifc_file.by_type("IfcBuildingStorey")
        storey_names = [s.Name for s in storeys]
        self.assertIn("Substructure", storey_names, "Missing Substructure building storey")

        # 2. Check semantic entities
        columns = ifc_file.by_type("IfcColumn")
        self.assertGreaterEqual(len(columns), 2, "Expected at least 2 IfcColumn (piers)")

        beams = ifc_file.by_type("IfcBeam")
        pier_cap_beams = [b for b in beams if b.Name and "Pier Cap" in b.Name]
        self.assertEqual(len(pier_cap_beams), 2, "Expected 2 IfcBeam representing Pier Caps")

        footings = ifc_file.by_type("IfcFooting")
        self.assertGreaterEqual(len(footings), 2, "Expected at least 2 IfcFooting (pile caps)")

        piles = ifc_file.by_type("IfcPile")
        self.assertEqual(len(piles), 8, "Expected 8 IfcPile (2x2 piles at 2 locations)")

        rebars = ifc_file.by_type("IfcReinforcingBar")
        self.assertGreater(len(rebars), 0, "Expected IfcReinforcingBar entities")

        # 3. Check property sets (Pset_OsdagSubstructure and Pset_OsdagRebar)
        rel_defines = ifc_file.by_type("IfcRelDefinesByProperties")
        psets = [r.RelatingPropertyDefinition for r in rel_defines if r.RelatingPropertyDefinition.is_a("IfcPropertySet")]
        pset_names = [p.Name for p in psets]

        self.assertIn("Pset_OsdagSubstructure", pset_names, "Missing Pset_OsdagSubstructure")
        self.assertIn("Pset_OsdagRebar", pset_names, "Missing Pset_OsdagRebar")

        # Inspect properties in Pset_OsdagSubstructure
        sub_psets = [p for p in psets if p.Name == "Pset_OsdagSubstructure"]
        self.assertGreater(len(sub_psets), 0)
        pier_pset = None
        for p in sub_psets:
            props = {prop.Name: prop.NominalValue.wrappedValue for prop in p.HasProperties}
            if props.get("ComponentType") == "Pier Column":
                pier_pset = props
                break
        self.assertIsNotNone(pier_pset, "Pier Column Pset_OsdagSubstructure not found")
        self.assertAlmostEqual(pier_pset["Diameter_m"], 0.8)
        self.assertAlmostEqual(pier_pset["Height_m"], 3.0)
        self.assertEqual(pier_pset["Material"], "Reinforced Concrete")

        # Inspect properties in Pset_OsdagRebar
        rebar_psets = [p for p in psets if p.Name == "Pset_OsdagRebar"]
        self.assertGreater(len(rebar_psets), 0)
        first_rebar_props = {prop.Name: prop.NominalValue.wrappedValue for prop in rebar_psets[0].HasProperties}
        self.assertIn("NominalDiameter_mm", first_rebar_props)
        self.assertIn("BarLength_m", first_rebar_props)
        self.assertIn("SteelGrade", first_rebar_props)
        self.assertIn(first_rebar_props["NominalDiameter_mm"], [8.0, 16.0])

        print(f"\n[SUCCESS] E2E Integration Test Passed!")
        print(f"Generated IFC file size: {os.path.getsize(output_path)} bytes")
        print(f"Entities summary: {len(columns)} columns, {len(pier_cap_beams)} pier caps, {len(footings)} footings, {len(piles)} piles, {len(rebars)} rebars")


if __name__ == "__main__":
    unittest.main()
