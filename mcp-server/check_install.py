"""Build and verify the shipped wheel in an isolated environment outside the checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

PROBE = r'''
import asyncio, json, os, subprocess, sys
from importlib.metadata import version
from pathlib import Path
from mcp import Client, MCPError, types
from mcp.client.stdio import StdioServerParameters

async def check_raw_session(command):
    process = await asyncio.create_subprocess_exec(command, stdin=asyncio.subprocess.PIPE,
                                                  stdout=asyncio.subprocess.PIPE,
                                                  stderr=asyncio.subprocess.PIPE)
    async def send(message):
        process.stdin.write((json.dumps(message)+"\n").encode())
        await process.stdin.drain()
    async def response(request_id):
        while True:
            line = await asyncio.wait_for(process.stdout.readline(), timeout=5)
            assert line, "Server closed before responding"
            message = json.loads(line)
            if message.get("id") == request_id:
                return message
    try:
        await send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
            "protocolVersion":types.LATEST_PROTOCOL_VERSION,"capabilities":{},
            "clientInfo":{"name":"installed-artifact-check","version":"1"}}})
        assert "result" in await response(1)
        await send({"jsonrpc":"2.0","method":"notifications/initialized"})
        # Malformed input must not prevent the next valid request.
        process.stdin.write(b"not-json\n")
        await process.stdin.drain()
        await send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
        assert len((await response(2))["result"]["tools"]) == 1
        await send({"jsonrpc":"2.0","id":3,"method":"no_such_method","params":{}})
        assert (await response(3))["error"]["code"] == -32601
        process.stdin.close()
        await process.stdin.wait_closed()
        assert await asyncio.wait_for(process.wait(), timeout=5) == 0
        return True
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()

async def check():
    command = str(Path(sys.executable).with_name("evidence-led-engineering-mcp"))
    assert version("evidence-led-engineering-mcp") == "1.0.0"
    version_check = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=5, check=True)
    assert version_check.stdout.strip() == "1.0.0"
    eof_check = subprocess.run([command], input="", capture_output=True, text=True, timeout=5, check=True)
    assert not eof_check.stdout
    params = StdioServerParameters(command=command, args=[], cwd=os.getcwd())
    async with Client(params, read_timeout_seconds=5) as client:
        tools = (await client.list_tools()).tools
        assert [t.name for t in tools] == ["review_measurements"]
        tool = tools[0]
        assert tool.input_schema["additionalProperties"] is False
        assert tool.output_schema["additionalProperties"] is False
        required = tool.output_schema["required"]
        assert "schema_version" in required and "independent_verification_performed" in required
        arguments = {"baseline_ms":[12,10,11],"candidate_ms":[4,5,6],"evidence":{}}
        result = await client.call_tool("review_measurements", arguments)
        assert not result.is_error
        data = result.structured_content
        assert data["observed_median_speedup"] == 2.2
        assert data["independent_verification_performed"] is False
        assert data["schema_version"] == 1
        assert len(data["missing_declared_evidence"]) == 6
        assert set(data) == set(required)
        for patch in [{"unknown": True}, {"baseline_ms":[0,1,2]}, {"scope":"production"},
                      {"evidence":{"unknown":True}}, {"baseline_ms":[True,2,3]},
                      {"candidate_ms":[1]*101}, {"evidence":{"same_workload":"true"}}]:
            failed = await client.call_tool("review_measurements", {**arguments, **patch})
            assert failed.is_error, patch
        unknown = await client.call_tool("no_such_tool", {})
        assert unknown.is_error
        resources = []
        for section in ["method","measurement","semantics","patterns","sources"]:
            resource = await client.read_resource("evidence-led://guide/"+section)
            assert len(resource.contents[0].text)>100
            resources.append(section)
        for section in ["unknown", "../server.py", "%2e%2e%2fserver.py"]:
            try:
                await client.read_resource("evidence-led://guide/"+section)
            except MCPError:
                pass
            else:
                raise AssertionError("Unexpected resource access: "+section)
        recovered = await client.call_tool("review_measurements", arguments)
        assert not recovered.is_error
    assert await check_raw_session(command)
    print(json.dumps({"package_version":version("evidence-led-engineering-mcp"),
                      "python":sys.version.split()[0],"platform":sys.platform,
                      "entry_point":True,"outside_checkout":True,
                      "strict_input":True,"structured_output":True,
                      "resources":resources,"error_recovery":True,"sdk_session_cleanup":True,
                      "eof_exit_zero":True,"initialized_session_exit_zero":True,
                      "malformed_input_recovery":True}))

asyncio.run(asyncio.wait_for(check(), timeout=25))
'''


def run(*args, **kwargs):
    return subprocess.run(args, check=True, timeout=120, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    project = Path(__file__).resolve().parent
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("Install uv before running the installed-artifact check.")
    with tempfile.TemporaryDirectory(prefix="evidence-led-install-") as directory:
        temp = Path(directory)
        run(uv, "build", "--project", str(project), "--out-dir", str(temp/"dist"))
        wheel = next((temp/"dist").glob("*.whl"))
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            assert sum("/guides/" in n and n.endswith(".md") for n in names) == 5
            assert any(n.endswith("/licenses/LICENSE") for n in names)
        requirements = temp/"dependencies.txt"
        run(uv, "export", "--project", str(project), "--frozen", "--no-dev",
            "--no-emit-project", "--output-file", str(requirements), stdout=subprocess.DEVNULL)
        run(uv, "venv", "--python", sys.executable, str(temp/"environment"))
        python = temp/"environment"/("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        run(uv, "pip", "install", "--python", str(python), "--require-hashes", "-r", str(requirements))
        run(uv, "pip", "install", "--python", str(python), "--no-deps", str(wheel))
        probe = temp/"probe.py"
        probe.write_text(PROBE, encoding="utf-8")
        result = run(str(python), "-I", str(probe), cwd=temp, capture_output=True, text=True)
        evidence = json.loads(result.stdout)
        evidence["wheel_sha256"] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        evidence["locked_dependency_hashes"] = True
        if options.output:
            options.output.write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
