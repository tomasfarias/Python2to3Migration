import sys
from lib2to3.main import main
from pathlib import Path

sys.path.append(Path.cwd())
sys.exit(main('fixes'))