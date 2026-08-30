"""Path bootstrap so the bring-up scripts can import ``src`` when run directly."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
