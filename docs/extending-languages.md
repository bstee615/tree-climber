# Extending Tree Sprawler to Support New Languages

This guide provides step-by-step instructions for adding support for a new programming language to Tree Sprawler. The process involves creating language-specific configuration files, implementing AST node handling, and setting up test files.

## Prerequisites

1. Tree-sitter grammar for the target language
2. Node types JSON file describing the AST structure for the language

## Steps Overview

1. Add node types configuration
2. Create language configuration module
3. Set up test files
4. Implement and test

## Detailed Steps

### 1. Add Node Types Configuration

1. Create a new directory under `docs/grammars/<language>/`
2. Add `node-types.json` file containing the AST node type definitions from tree-sitter
   - This file should be obtained from the tree-sitter grammar repository for your language
   - Ensure it contains all node types and their field definitions

### 2. Create Language Configuration Module

1. Create a new Python module at `src/tree_sprawler/cfg/languages/<language>.py`
2. Implement the following components:

```python
from tree_sprawler.cfg.cfg_types import Block, Edge, EdgeType
from tree_sprawler.cfg.visitor import CFGVisitor

class LanguageVisitor(CFGVisitor):
    """Visitor class for building CFG from language-specific AST nodes."""
    
    def __init__(self):
        super().__init__()
        # Add any language-specific initialization
        
    def handles_type(self, node_type: str) -> bool:
        """Define which node types this visitor handles."""
        # Return True for any node types that have handler methods
        return node_type in [
            'if_statement',
            'while_statement',
            # Add other handled node types
        ]

    def handle_if_statement(self, node, **kwargs):
        """Handle if statement nodes.
        
        Required components:
        1. Extract condition from the node
        2. Create condition block
        3. Process true branch
        4. Process false branch if exists
        5. Create merge block if needed
        6. Connect blocks with appropriate edges
        """
        # Implementation

    def handle_while_statement(self, node, **kwargs):
        """Handle while loop nodes.
        
        Required components:
        1. Create loop header block
        2. Extract and process condition
        3. Process loop body
        4. Connect blocks with appropriate edges
        5. Handle continue/break statements
        """
        # Implementation
```

Key implementation notes:

a. Node Creation:
```python
# Create new CFG nodes using:
node = CFGNode(
    id=self.next_id(),  # Get unique node ID
    node_type=NodeType.STATEMENT,  # From NodeType enum
    ast_node=node,  # Original AST node
    source_text=self.get_text(node)  # Source code text
)
```

b. Edge Creation:
```python
# Connect nodes using successors:
source_node.add_successor(target_node.id, label="true")  # Optional label for conditional edges

# Or for more complex cases:
source_node.successors.add(target_node.id)
source_node.edge_labels[target_node.id] = "true"  # For conditional branches
```

### 3. Set Up Test Files

1. Create a test file at `src/tree_sprawler/cfg/test_<language>.py`
2. Create sample code files in `test/test.<language_extension>`
3. Implement test cases modeling after `test_c.py` and `test_java.py`

### 4. Implementation Process

1. Start with basic control flow structures:
   - If statements
   - Loops (while, for)
   - Function definitions
   - Basic blocks (sequences of statements)

2. Add support for language-specific features:
   - Switch/case statements
   - Exception handling
   - Break/continue statements
   - Return statements

3. Follow existing language implementations (e.g., Java, C) as reference
   - Look at how similar constructs are handled
   - Maintain consistent patterns for similar structures

4. Test incrementally:
   - Write tests for each new feature
   - Visualize CFGs to verify correctness
   - Ensure edge cases are covered

## Common Pitfalls

1. **Node Type Mismatches**: Ensure node types in your handlers exactly match those in node-types.json
2. **Missing Fields**: Verify all required node fields are accessed correctly
3. **Edge Connections**: Double-check that all blocks are properly connected
4. **Block Ordering**: Maintain correct execution order in the CFG

## Resources

1. Refer to existing implementations:
   - `src/tree_sprawler/cfg/languages/java.py`
   - `src/tree_sprawler/cfg/languages/c.py`
2. Tree-sitter documentation for your language
3. Language specification for control flow semantics

## Troubleshooting

1. If tests fail:
   - Check node type names match exactly
   - Verify field access paths
   - Compare with working implementations
   - Use visualization to spot structural issues

2. If visualization looks wrong:
   - Check edge connections
   - Verify block creation order
   - Ensure all paths are connected
   - Look for disconnected components

3. Common errors:
   - AttributeError: Usually means incorrect field name
   - KeyError: Missing node field
   - TypeError: Wrong node type handling
