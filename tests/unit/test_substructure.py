"""
Unit tests for Substructure components and IFC integration.
"""
import unittest
from unittest.mock import MagicMock, patch
import math


class TestSubstructureBuilders(unittest.TestCase):
    """Test substructure builder geometric algorithms and metadata."""

    def test_pier_dimensions_and_math(self):
        """Test pier geometry calculations."""
        pier_diameter = 800.0
        pier_height = 3000.0
        rebar_cover = 40.0
        rebar_transverse_dia = 8.0
        rebar_main_dia = 16.0
        rebar_spacing_long = 150.0

        radius = pier_diameter / 2.0
        r_pitch = radius - rebar_cover - rebar_transverse_dia - (rebar_main_dia / 2.0)
        self.assertEqual(radius, 400.0)
        self.assertEqual(r_pitch, 344.0)

        circumference = 2.0 * math.pi * r_pitch
        num_bars = max(6, int(round(circumference / rebar_spacing_long)))
        self.assertGreaterEqual(num_bars, 14)

    def test_pile_cap_and_piles_grid(self):
        """Test 2x2 pile grid coordinates inside pile cap."""
        pile_cap_length = 2200.0
        pile_cap_width = 1200.0
        pile_spacing = 600.0
        pile_diameter = 400.0

        half_s = pile_spacing / 2.0
        offsets = [
            (-half_s, -half_s),
            (half_s, -half_s),
            (-half_s, half_s),
            (half_s, half_s)
        ]
        self.assertEqual(len(offsets), 4)

        # Check that piles fit inside pile cap with clearance
        for dx, dy in offsets:
            pile_x_min = dx - pile_diameter / 2.0
            pile_x_max = dx + pile_diameter / 2.0
            pile_y_min = dy - pile_diameter / 2.0
            pile_y_max = dy + pile_diameter / 2.0

            self.assertGreaterEqual(pile_x_min, -pile_cap_length / 2.0)
            self.assertLessEqual(pile_x_max, pile_cap_length / 2.0)
            self.assertGreaterEqual(pile_y_min, -pile_cap_width / 2.0)
            self.assertLessEqual(pile_y_max, pile_cap_width / 2.0)

    def test_pier_cap_trapezoid_dimensions(self):
        """Test pier cap geometry parameters."""
        top_width = 3000.0
        bottom_width = 1200.0
        depth = 600.0
        length = 1200.0

        self.assertGreater(top_width, bottom_width)
        self.assertEqual(depth, 600.0)
        self.assertEqual(length, 1200.0)


class TestSubstructureIFCExtraction(unittest.TestCase):
    """Test parametric extraction of substructure for IFC export."""

    def test_substructure_extraction(self):
        from osdagbridge.core.ifc_export_bridge.bridge_cad_extraction import PlateGirderIFCExtractor

        mock_cad = MagicMock()
        mock_cad.span_length_L = 20000.0
        mock_cad.girder_section_d = 1500.0
        mock_cad.girder_section_tf_b = 25.0
        mock_cad.skew_angle = 0.0
        mock_cad.pier_diameter = 800.0
        mock_cad.pier_height = 3000.0
        mock_cad.pier_cap_top_width = 3000.0
        mock_cad.pier_cap_bottom_width = 1200.0
        mock_cad.pier_cap_depth = 600.0
        mock_cad.pier_cap_length = 1200.0
        mock_cad.pile_cap_length = 2200.0
        mock_cad.pile_cap_width = 1200.0
        mock_cad.pile_cap_depth = 600.0
        mock_cad.pile_diameter = 400.0
        mock_cad.pile_length = 5000.0
        mock_cad.pile_spacing = 600.0
        mock_cad.rebar_main_diameter = 16.0
        mock_cad.rebar_transverse_diameter = 8.0
        mock_cad.rebar_cover = 40.0
        mock_cad.rebar_spacing_longitudinal = 150.0

        extractor = PlateGirderIFCExtractor(mock_cad)
        data = extractor._extract_substructure()

        # Both Left and Right supports
        self.assertEqual(len(data["pier_caps"]), 2)
        self.assertEqual(len(data["piers"]), 2)
        self.assertEqual(len(data["pile_caps"]), 2)
        self.assertEqual(len(data["piles"]), 8)  # 4 piles per pier cap * 2
        self.assertGreater(len(data["reinforcement"]), 0)

        # Check coordinates of pier columns
        left_pier = data["piers"][0]
        right_pier = data["piers"][1]
        self.assertEqual(left_pier.origin[0], 0.0)
        self.assertEqual(right_pier.origin[0], 20000.0)
        self.assertEqual(left_pier.diameter, 800.0)
        self.assertEqual(left_pier.height, 3000.0)


if __name__ == "__main__":
    unittest.main()

