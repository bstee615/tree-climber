"""
Global configuration
"""

import os

treeclimber_DATAROOT = os.path.expanduser("~/.treeclimber/")
TREE_SITTER_LIB_PREFIX = os.environ.get("treeclimber__TREE_SITTER_LIB_PREFIX", os.path.join(treeclimber_DATAROOT, "lib"))
DRAW_CFG = os.environ.get("treeclimber__DRAW_CFG", False)
