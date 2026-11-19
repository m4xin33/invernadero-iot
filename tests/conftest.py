import sys
from pathlib import Path

# Permite `from core import ...` al ejecutar pytest desde cualquier carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
