# This module runs automated tests from "parse tree specs", snapshots of what a parse tree should look like for a given program.
"""
Format: <Testcase Name>.md

# Code
```language
<code to parse>
```

# Tree
```json
<expected parse tree>
```
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pytest
from tree_sitter_languages import get_parser

from tree_sprawler.cfg.builder import CFGBuilder

C_TEST_DIR = Path(__file__).parent / "parse_trees" / "c"
DELIMITER = "\n" + "=" * 25 + "\n"
PARSER = get_parser("markdown")


@dataclass
class TreeSpec:
    name: str
    code: str
    expected: dict


@dataclass
class WIPTreeSpec:
    name: str
    code: Optional[str]
    expected: Optional[dict]

    def formalize(self) -> TreeSpec:
        if self.code is None or self.expected is None:
            raise ValueError("Code and expected must be set")
        return TreeSpec(
            name=self.name,
            code=self.code,
            expected=self.expected,
        )


def parse_tree_file(file_path: Path) -> TreeSpec:
    with open(file_path, "rb") as f:
        tree = PARSER.parse(f.read())
    root = tree.root_node
    assert root.type == "document", f"Expected 'document': {root.type}"
    wip_spec = WIPTreeSpec(
        name=file_path.stem,
        code=None,
        expected=None,
    )
    for i in range(root.child_count):
        child = root.child(i)
        assert child is not None, f"Child {i} is None"
        assert child.type in ["atx_heading", "fenced_code_block"], (
            f"Unexpected child type: {child.type}"
        )
        if child.type == "atx_heading":
            content = (
                next(ch for ch in child.children if ch.type == "heading_content")
                .text.decode("utf-8")
                .strip()
            )
            match content:
                case "Code":
                    code_block = next(
                        ch for ch in root.children[i:] if ch.type == "fenced_code_block"
                    )
                    wip_spec.code = (
                        next(
                            ch
                            for ch in code_block.children
                            if ch.type == "code_fence_content"
                        )
                        .text.decode("utf-8")
                        .strip()
                    )
                case "Tree":
                    block = next(
                        ch for ch in root.children[i:] if ch.type == "fenced_code_block"
                    )
                    content = (
                        next(
                            ch
                            for ch in block.children
                            if ch.type == "code_fence_content"
                        )
                        .text.decode("utf-8")
                        .strip()
                    )
                    # TODO: Parse XML
                case _:
                    raise ValueError(f"Unexpected heading content: {content}")
    return wip_spec.formalize()


@pytest.mark.parametrize("test_file", C_TESTS)
def test_c(test_file: Path):
    spec = parse_tree_file(test_file)
    print(f"Running test: {spec.name}")
    # Create and setup CFG builder
    language = "c"
    builder = CFGBuilder(language)
    builder.setup_parser()
    assert builder.parser is not None, f"Parser for {language} not set up correctly."

    # Parse source code to get AST
    tree = builder.parser.parse(bytes(spec.code, "utf8"))
    assert tree is not None, "Failed to parse source code."

    # Build CFG from AST
    cfg = builder.build_cfg(tree=tree)
    assert cfg is not None, "Failed to build CFG."

    assert_graphs_match(cfg, spec.expected)
