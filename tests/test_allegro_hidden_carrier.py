"""Parcels hidden in a carrier account must stay hidden in Allegro."""

import ast
import runpy
import unittest
from pathlib import Path


COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "polish_shipment_tracking"
HELPERS = runpy.run_path(str(COMPONENT / "helpers.py"))


class ShipmentCoordinator:
    pass


def _load_carrier_tracking_numbers():
    # Home Assistant is not installed here: load only the one method.
    tree = ast.parse((COMPONENT / "coordinator.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_carrier_tracking_numbers":
            module = ast.Module(body=[node], type_ignores=[])
            namespace = {
                "DOMAIN": "polish_shipment_tracking",
                "ShipmentCoordinator": ShipmentCoordinator,
                "get_parcel_tracking_numbers": HELPERS["get_parcel_tracking_numbers"],
            }
            exec(compile(module, "coordinator.py", "exec"), namespace)
            return namespace["_carrier_tracking_numbers"]
    raise AssertionError("_carrier_tracking_numbers not found")


class FakeHass:
    def __init__(self):
        self.data = {}


def _coordinator(courier, data, hidden=()):
    coordinator = ShipmentCoordinator()
    coordinator.courier = courier
    coordinator.data = data
    coordinator.hidden_tracking_numbers = set(hidden)
    return coordinator


class AllegroHiddenCarrierTests(unittest.TestCase):
    def setUp(self):
        self.carrier_tracking_numbers = _load_carrier_tracking_numbers()
        self.allegro = _coordinator("allegro", [])
        self.allegro.hass = FakeHass()

    def test_hidden_carrier_number_counts_as_tracked(self):
        inpost = _coordinator("inpost", [], hidden={"620012345678"})
        self.allegro.hass.data["polish_shipment_tracking"] = {"inpost": inpost}
        self.assertIn("620012345678", self.carrier_tracking_numbers(self.allegro))

    def test_visible_carrier_parcel_still_counts(self):
        inpost = _coordinator("inpost", [{"shipmentNumber": "620099999999"}])
        self.allegro.hass.data["polish_shipment_tracking"] = {"inpost": inpost}
        self.assertIn("620099999999", self.carrier_tracking_numbers(self.allegro))


if __name__ == "__main__":
    unittest.main()
