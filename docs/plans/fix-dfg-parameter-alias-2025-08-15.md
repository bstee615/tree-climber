# Fix DFG Parameter Alias - 2025-08-15

## Problem
Both languages DFG: Function parameters should alias def uses.

Currently, function parameters are not properly treated as definitions that can alias uses within the function scope. This means that when a parameter is used within a function, the dataflow analysis doesn't correctly identify the parameter declaration as the source definition.

## Analysis Needed
1. Examine current DFG implementation for both C and Java
2. Understand how function parameters are currently handled
3. Identify where parameter aliasing should occur
4. Determine the correct dataflow relationship between parameter definitions and uses

## Investigation Plan
1. Look at dataflow analysis code structure ✓
2. Create test cases showing current vs expected behavior ✓
3. Identify the specific issue in parameter handling ✓
4. Implement the fix for both languages

## Analysis Results
The issue is now clear: **Inter-procedural parameter aliasing is missing**.

### Current Behavior
- Intra-procedural DFG works correctly (within functions)
- Function parameters are defined in ENTRY nodes
- Function arguments are used at call sites
- **Missing**: No connection between arguments and parameters across function boundaries

### Example Issue
```c
void helper(int a) {
    int b = a + 1;  // 'a' should alias to argument 'x' from call site
}

int main() {
    int x = 5;
    helper(x);  // 'x' should alias to parameter 'a' in helper
}
```

**Current**: `x` defined at node 5, used at node 6. `a` defined at node 0, used at node 2. No connection.
**Expected**: `x` definition at node 5 should also reach uses of `a` inside `helper`.

## Implementation Plan
1. ~~Extend ReachingDefinitionsGenKill to handle function call parameter aliasing~~ (attempted but complex)
2. Create mapping from call arguments to function parameters ✓
3. ~~Add alias facts for inter-procedural parameter passing~~ (replaced with direct approach)
4. Test with both C and Java examples ✓

## Final Implementation Results - Executive Summary

Successfully implemented inter-procedural parameter aliasing for both C and Java DFG analysis.

### Approach Taken:
**Direct Parameter Alias Resolution in Def-Use Solvers**

Instead of propagating alias facts through the complex CFG dataflow, implemented direct parameter alias resolution in both `UseDefSolver` and `DefUseSolver` classes.

### Key Changes:
1. **Added `_find_parameter_aliases()` method**: Directly maps function call arguments to parameters when processing parameter uses
2. **Added `_reaches_call_site()` method**: Checks if argument definitions reach call sites without being killed
3. **Enhanced both solvers**: Modified to include parameter aliases when computing def-use chains

### How It Works:
1. When processing a parameter use (e.g., `a` in `int b = a + 1`):
   - Find the ENTRY node that defines this parameter
   - Find call sites that call this function (e.g., `helper(x)`)
   - Extract call arguments and map to parameters
   - Find argument definitions that reach the call site
   - Include these as alias definitions for the parameter use

### Verification Results:
**Before Fix:**
```
Variable 'a':
  Definition at node 0: 'helper'
    -> Used at node 2: 'int b = a + 1;'
```

**After Fix:**
```
Variable 'a':
  Definition at node 0: 'helper'           ← Original parameter definition
    -> Used at node 2: 'int b = a + 1;'
  Definition at node 5: 'int x = 5;'       ← NEW: Aliased argument definition  
    -> Used at node 2: 'int b = a + 1;'
```

### Result:
The second parsing bug "Both languages DFG, Function parameters should alias def uses" is now **FIXED**. Function arguments at call sites correctly alias to parameter uses within called functions, enabling proper inter-procedural dataflow analysis.