1. [x] Parse linear statements into one single CFG node.
2. [x] Label true and false branches on conditional nodes.
3. [x] Label nodes like "for condition" with the text of the condition, etc for exit and init.
4. [x] Update type hints Any to tree_sitter.Node in visitors
5. [x] Remove comments from the CFG.

# Active Work Items

## PBI-1: Implement Def-Use Chain Analysis

### Overview
Add def-use chain analysis to support dataflow analysis in the tree-sprawler project.

### Tasks

| Task ID | Name | Status | Description |
|---------|------|--------|-------------|
| 1-1 | @Add dataflow types | Proposed | Add DefUseChain and DataFlowState types to support dataflow analysis |
| 1-2 | @Implement def-use solver | Proposed | Implement the iterative worklist algorithm for def-use chain analysis |
| 1-3 | @Add def-use chain visualization | Proposed | Add visualization support for def-use chains |

### Conditions of Satisfaction
- [ ] Can analyze simple programs and identify def-use chains
- [ ] Works with existing CFG implementation
- [ ] Handles loops and branches correctly
- [ ] Performance is reasonable for typical code sizes
- [ ] Includes visualization of def-use chains
