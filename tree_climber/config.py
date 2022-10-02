"""
Global configuration
"""

import os

tree_climber_DATAROOT = os.path.expanduser("~/.tree_climber/")
TREE_SITTER_LIB_PREFIX = os.environ.get("tree_climber__TREE_SITTER_LIB_PREFIX", os.path.join(tree_climber_DATAROOT, "lib"))
DRAW_CFG = os.environ.get("tree_climber__DRAW_CFG", False)
