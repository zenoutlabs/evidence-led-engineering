import asyncio
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp import Client, MCPError
from mcp.client.stdio import StdioServerParameters
from server import mcp


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_discovery_call_resource_and_invalid_input(self):
        params = StdioServerParameters(command=sys.executable,
                                       args=[str(Path(__file__).resolve().parents[1] / "server.py")])
        async def check():
            async with Client(params, read_timeout_seconds=5) as client:
                tools = await client.list_tools()
                self.assertEqual([tool.name for tool in tools.tools], ["review_measurements"])
                result = await client.call_tool("review_measurements", {
                    "baseline_ms": [12, 10, 11], "candidate_ms": [4, 5, 6], "evidence": {},
                })
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["observed_median_speedup"], 2.2)
                self.assertEqual(len(result.structured_content["missing_declared_evidence"]), 6)
                invalid = await client.call_tool("review_measurements", {
                    "baseline_ms": [0, 1, 2], "candidate_ms": [1, 2, 3], "evidence": {},
                })
                self.assertTrue(invalid.is_error)
                resource = await client.read_resource("evidence-led://guide/method")
                self.assertIn("Evidence-Led Engineering", resource.contents[0].text)
        await asyncio.wait_for(check(), timeout=15)

    async def test_in_memory_resource_boundary_and_unknown_arguments(self):
        async with Client(mcp, read_timeout_seconds=5) as client:
            result = await client.call_tool("review_measurements", {
                "baseline_ms": [1, 2, 3], "candidate_ms": [1, 2, 3],
                "evidence": {"command": "do not execute"},
            })
            self.assertTrue(result.is_error)
            with self.assertRaises(MCPError) as missing:
                await client.read_resource("evidence-led://guide/not-a-section")
            self.assertEqual(missing.exception.error.code, -32602)

    async def test_tool_rejects_coercion_size_and_unequal_sample_counts(self):
        async with Client(mcp, read_timeout_seconds=5) as client:
            for change in (
                {"baseline_ms": [True, 2, 3]},
                {"unknown": True},
                {"baseline_ms": ["1", 2, 3]},
                {"baseline_ms": [1] * 101},
                {"baseline_ms": [1, 2, 3, 4]},
                {"evidence": {"outputs_verified": "true"}},
            ):
                arguments = {"baseline_ms": [1, 2, 3], "candidate_ms": [1, 2, 3], "evidence": {}}
                arguments.update(change)
                with self.subTest(change=change):
                    result = await client.call_tool("review_measurements", arguments)
                    self.assertTrue(result.is_error)


if __name__ == "__main__":
    unittest.main()
