# Fix Function Call CFG Edges - 2025-08-14

## Problem
Both languages CFG: Function calls should have an edge from exit going back to the call.

Currently, function calls are treated as simple statements without considering that they:
1. Potentially transfer control to another function
2. Should return control back to the calling statement
3. Need proper CFG representation for inter-procedural analysis

## Current Analysis
Looking at both C and Java implementations:
- Function calls (`call_expression` in C, `method_invocation` in Java) are processed as linear statements
- They create a single STATEMENT node without any special CFG edges
- No consideration for call/return semantics in CFG structure

## Proposed Solution
1. Create a special visitor method for function calls in both languages
2. Function calls should create CFG nodes that represent:
   - Entry to the call
   - Exit from the call (return point)
   - Edge from call to potential callee entry (if available)
   - Edge from callee exit back to the call return point

## Implementation Plan
1. Add `visit_call_expression` method to C CFG visitor
2. Add `visit_method_invocation` method to Java CFG visitor
3. Create special handling for function call CFG edges
4. Test with simple function call examples

## Testing Strategy
- Create simple test files with function calls
- Verify CFG structure shows proper call/return edges
- Ensure existing tests still pass

## Implementation Results - Executive Summary

Successfully implemented function call return edges in both C and Java CFG visitors.

### Changes Made:
1. **Enhanced ControlFlowContext**: Added `function_call_returns` list to track (function_exit_id, call_return_point_id) pairs
2. **Modified create_node method**: When detecting function calls, register return edges from function exits back to call sites
3. **Added postprocessing step**: `_add_function_call_return_edges()` creates the actual return edges with "function_return" labels
4. **Proper call/return structure**: Function calls now have both call edges (to function entry) and return edges (from function exit back to call site)

### Verification:
- Created debug script showing before/after CFG structure
- Function calls now correctly show bidirectional edges: call → function entry, function exit → call site
- All existing C tests (37/37) and Java tests (29/29) continue to pass
- No regressions in CFG structural integrity

### Result:
The first parsing bug "Both languages CFG, Function calls should have an edge from exit going back to the call" is now **FIXED**. Function exits now properly connect back to their call sites, creating complete inter-procedural control flow representation.