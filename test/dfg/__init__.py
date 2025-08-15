"""
DFG (Data Flow Graph) Test Suite

This package contains comprehensive tests for dataflow analysis including:
- Basic def-use and use-def chain analysis
- Inter-procedural parameter aliasing  
- Complex control flow scenarios
- Language-specific stress tests for C and Java

Test Structure:
- test_dfg_comprehensive.py: Core DFG functionality tests with DSL-like helpers
- test_dfg_stress.py: Complex real-world scenario stress tests
- stress_test_c.c: C stress test program with complex patterns
- stress_test_java.java: Java stress test program with complex patterns
"""