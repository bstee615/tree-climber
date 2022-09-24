"""
Global configuration
"""

import os

TREEHOUSE_DATAROOT = os.path.expanduser("~/.treehouse/")
TREE_SITTER_LIB_PREFIX = os.environ.get("treehouse__TREE_SITTER_LIB_PREFIX", os.path.join(TREEHOUSE_DATAROOT, "lib"))
DRAW_CFG = os.environ.get("treehouse__DRAW_CFG", False)
