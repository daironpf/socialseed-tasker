"""Configure test environment."""
import sys
from pathlib import Path

# Add src and project root to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))
