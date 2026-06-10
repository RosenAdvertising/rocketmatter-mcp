from pathlib import Path

from mcp_test_kit.config import ResilienceConfig, SpecCheckConfig, ToolkitConfig
from rocketmatter_mcp.server import mcp

_TESTS_DIR = Path(__file__).parent

TOOLKIT = ToolkitConfig(
    mcp_server=mcp,
    spec_check=SpecCheckConfig(
        endpoints_path=_TESTS_DIR.parent / "endpoints.yaml",
        openapi_path=_TESTS_DIR.parent
        / "endpoints.yaml",  # dummy — contract tier skipped
    ),
    source_path=_TESTS_DIR.parent / "rocketmatter_mcp",
    module_path="rocketmatter_mcp",
    server_path=_TESTS_DIR.parent / "rocketmatter_mcp" / "server.py",
    resilience=ResilienceConfig(tools_to_timeout_test=["list_matters"]),
    skip_tiers={
        "contract": "RocketMatter API spec is OpenAPI 2.0 — contract tier requires OpenAPI 3.x",
        "smoke": "requires live sandbox credentials",
    },
)
