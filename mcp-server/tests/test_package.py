"""Keep bundled documentation synchronized with the maintained skill."""
from importlib.resources import files
from pathlib import Path
import unittest


class PackageTests(unittest.TestCase):
    def test_bundled_resources_match_maintained_sources(self):
        root = Path(__file__).resolve().parents[2]/"skills/evidence-led-performance"
        bundle = files("evidence_led_engineering_mcp").joinpath("guides")
        paths = {"method.md":"SKILL.md", "measurement.md":"references/measurement.md",
                 "semantic-contracts.md":"references/semantic-contracts.md",
                 "optimization-patterns.md":"references/optimization-patterns.md",
                 "sources.md":"references/sources.md"}
        for bundled, maintained in paths.items():
            with self.subTest(resource=bundled):
                self.assertEqual(bundle.joinpath(bundled).read_bytes(), (root/maintained).read_bytes())
