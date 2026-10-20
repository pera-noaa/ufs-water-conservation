#!/usr/bin/env python3
"""wrapper: fix_trsamf.py t1 <tree>"""
import sys, subprocess
from pathlib import Path
sys.exit(subprocess.call([sys.executable, '-I', str(Path(__file__).with_name('fix_trsamf.py')), 't1', sys.argv[1]]))
