import sys
from pathlib import Path

# Add src to path so tests can import sandbox_plugin
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
