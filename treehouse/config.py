"""
Global configuration
"""

import os


TREE_SITTER_C_PREFIX = os.environ.get("treehouse__TREE_SITTER_C_PREFIX", "lib")
DRAW_CFG = os.environ.get("treehouse__DRAW_CFG", False)
