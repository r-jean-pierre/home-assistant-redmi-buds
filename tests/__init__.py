"""Integration and protocol tests."""

import sys
from pathlib import Path

# Import the standalone MMA package without importing Home Assistant in unit tests.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "redmi_buds")
)
