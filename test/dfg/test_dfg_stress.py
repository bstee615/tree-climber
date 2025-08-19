"""
DFG Stress Tests - Complex real-world scenarios

This module tests the DFG implementation against complex, real-world code patterns
using the stress test programs in C and Java.
"""

import os
from test.dfg.test_dfg_comprehensive import DFGTestHelper

import pytest


class TestDFGStressC:
    """Stress tests using the C stress test program."""

    def setup_method(self):
        self.helper = DFGTestHelper("c")
        self.stress_file = os.path.join(os.path.dirname(__file__), "stress_test_c.c")

    def test_basic_function_analysis(self):
        """Test DFG analysis on basic functions from stress test."""
        code = """
        int add(int a, int b) {
            int result = a + b;
            return result;
        }
        
        int main() {
            int x = 5;
            int y = 3;
            int sum = add(x, y);
            return sum;
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Test parameter aliasing
        self.helper.assert_parameter_alias(
            def_use_result,
            "a",
            "x = 5",
            "result = a + b",
            "Parameter 'a' should alias to argument 'x'",
        )
        self.helper.assert_parameter_alias(
            def_use_result,
            "b",
            "y = 3",
            "result = a + b",
            "Parameter 'b' should alias to argument 'y'",
        )

        # Test return value usage
        self.helper.assert_def_use_chain(
            def_use_result,
            "sum",
            "sum = add(x, y)",
            "return sum",
            "sum should be defined by function call and used in return",
        )

    def test_parameter_modification(self):
        """Test functions that modify their parameters."""
        code = """
        int increment(int x) {
            x = x + 1;
            int doubled = x * 2;
            return doubled;
        }
        
        int main() {
            int val = 10;
            int result = increment(val);
            return result;
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Parameter x should have multiple definitions
        x_chains = def_use_result.chains.get("x", [])
        assert (
            len(x_chains) >= 2
        ), f"Expected at least 2 def-use chains for x, got {len(x_chains)}"

        # Original parameter should alias to argument
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "val = 10",
            "x = x + 1",
            "Original parameter should alias to argument",
        )

    def test_nested_function_calls(self):
        """Test complex nested function call patterns."""
        code = """
        int add(int a, int b) {
            return a + b;
        }
        
        int increment(int x) {
            x = x + 1;
            return x * 2;
        }
        
        int nested_calls(int val) {
            int processed = increment(val);
            int doubled = add(processed, processed);
            return doubled;
        }
        
        int main() {
            int input = 5;
            int result = nested_calls(input);
            return result;
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Test the aliasing chain through nested calls
        self.helper.assert_parameter_alias(
            def_use_result,
            "val",
            "input = 5",
            "increment(val)",
            "Parameter 'val' should alias to 'input'",
        )

        # Test that processed variable connects to function result
        self.helper.assert_def_use_chain(
            def_use_result,
            "processed",
            "processed = increment(val)",
            "add(processed, processed)",
            "processed should be used in nested function call",
        )

    def test_loops_with_function_calls(self):
        """Test dataflow analysis with loops containing function calls."""
        code = """
        int increment(int x) {
            return x + 1;
        }
        
        int main() {
            int sum = 0;
            for (int i = 0; i < 3; i++) {
                sum = sum + increment(i);
            }
            return sum;
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # sum should have multiple definitions due to loop
        sum_chains = def_use_result.chains.get("sum", [])
        assert (
            len(sum_chains) >= 2
        ), f"Expected at least 2 def-use chains for sum, got {len(sum_chains)}"

        # Loop variable i should be aliased to parameter x
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "i = 0",
            "return x + 1",
            "Loop variable should alias to function parameter",
        )

    def test_complex_control_flow(self):
        """Test DFG with complex control flow including conditionals and loops."""
        code = """
        int process(int val) {
            return val * 2;
        }
        
        int main() {
            int x = 5;
            int result = 0;
            
            if (x > 0) {
                result = process(x);
                while (result < 20) {
                    result = result + process(1);
                }
            } else {
                result = x * -1;
            }
            
            return result;
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Test parameter aliasing in conditional context
        self.helper.assert_parameter_alias(
            def_use_result,
            "val",
            "x = 5",
            "return val * 2",
            "Parameter should alias through conditional call",
        )

        # result should have multiple definitions
        result_chains = def_use_result.chains.get("result", [])
        assert (
            len(result_chains) >= 2
        ), f"Expected multiple def-use chains for result, got {len(result_chains)}"


class TestDFGStressJava:
    """Stress tests using the Java stress test program."""

    def setup_method(self):
        self.helper = DFGTestHelper("java")
        self.stress_file = os.path.join(
            os.path.dirname(__file__), "stress_test_java.java"
        )

    def test_basic_method_analysis(self):
        """Test DFG analysis on basic Java methods."""
        code = """
        public class Test {
            public static int add(int a, int b) {
                int result = a + b;
                return result;
            }
            
            public static void main(String[] args) {
                int x = 5;
                int y = 3;
                int sum = add(x, y);
            }
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Test parameter aliasing
        self.helper.assert_parameter_alias(
            def_use_result,
            "a",
            "x = 5",
            "result = a + b",
            "Parameter 'a' should alias to argument 'x'",
        )
        self.helper.assert_parameter_alias(
            def_use_result,
            "b",
            "y = 3",
            "result = a + b",
            "Parameter 'b' should alias to argument 'y'",
        )

    def test_enhanced_for_loop(self):
        """Test Java enhanced for loop with method calls."""
        code = """
        public class Test {
            public static int increment(int x) {
                return x + 1;
            }
            
            public static void main(String[] args) {
                int[] numbers = {1, 2, 3};
                int sum = 0;
                for (int num : numbers) {
                    sum = sum + increment(num);
                }
            }
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Enhanced for loop should create proper dataflow
        sum_chains = def_use_result.chains.get("sum", [])
        assert (
            len(sum_chains) >= 1
        ), f"Expected at least 1 def-use chain for sum, got {len(sum_chains)}"

        # Parameter x should be aliased to loop variable num
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "num",
            "return x + 1",
            "Enhanced for loop variable should alias to parameter",
        )

    def test_exception_handling(self):
        """Test DFG analysis with try-catch blocks."""
        code = """
        public class Test {
            public static int process(int x) {
                return x * 2;
            }
            
            public static void main(String[] args) {
                int result = 0;
                int input = 5;
                try {
                    result = process(input);
                    result = result + 1;
                } catch (Exception e) {
                    result = input * -1;
                }
            }
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Parameter should be aliased even in exception context
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "input = 5",
            "return x * 2",
            "Parameter should alias in try-catch context",
        )

        # result should have definitions from both try and catch blocks
        result_chains = def_use_result.chains.get("result", [])
        assert (
            len(result_chains) >= 2
        ), f"Expected multiple def-use chains for result, got {len(result_chains)}"

    def test_switch_with_method_calls(self):
        """Test DFG analysis with switch statements containing method calls."""
        code = """
        public class Test {
            public static int increment(int x) {
                return x + 1;
            }
            
            public static int process(int x) {
                return x * 2;
            }
            
            public static void main(String[] args) {
                int value = 2;
                int result = 0;
                
                switch (value) {
                    case 1:
                        result = increment(value);
                        break;
                    case 2:
                        result = process(value);
                        break;
                    default:
                        result = value;
                }
            }
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Parameters should be aliased in switch context
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "value = 2",
            "return x * 2",
            "Parameter should alias in switch case",
        )

        # result should have multiple possible definitions
        result_chains = def_use_result.chains.get("result", [])
        assert (
            len(result_chains) >= 1
        ), f"Expected at least 1 def-use chain for result, got {len(result_chains)}"

    def test_recursive_methods(self):
        """Test DFG analysis with recursive method calls."""
        code = """
        public class Test {
            public static int factorial(int n) {
                if (n <= 1) {
                    return 1;
                }
                return n * factorial(n - 1);
            }
            
            public static void main(String[] args) {
                int input = 5;
                int result = factorial(input);
            }
        }
        """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Test parameter aliasing in recursive context
        self.helper.assert_parameter_alias(
            def_use_result,
            "n",
            "input = 5",
            "n <= 1",
            "Parameter should alias in recursive method",
        )

        # n should be used in multiple places within the recursive method
        n_chains = def_use_result.chains.get("n", [])
        assert (
            len(n_chains) >= 1
        ), f"Expected at least 1 def-use chain for n, got {len(n_chains)}"


class TestDFGEdgeCases:
    """Test edge cases and boundary conditions for DFG analysis."""

    @pytest.fixture(params=["c", "java"])
    def helper(self, request):
        return DFGTestHelper(request.param)

    def test_empty_functions(self, helper):
        """Test DFG analysis with empty functions."""
        if helper.language == "c":
            code = """
            void empty() {
            }
            
            int main() {
                empty();
                return 0;
            }
            """
        else:  # java
            code = """
            public class Test {
                public static void empty() {
                }
                
                public static void main(String[] args) {
                    empty();
                }
            }
            """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Should handle empty functions gracefully
        assert (
            len(def_use_result.chains) >= 0
        ), "Should handle empty functions without error"

    def test_functions_with_no_parameters(self, helper):
        """Test functions that have no parameters."""
        if helper.language == "c":
            code = """
            int get_constant() {
                int value = 42;
                return value;
            }
            
            int main() {
                int result = get_constant();
                return result;
            }
            """
        else:  # java
            code = """
            public class Test {
                public static int getConstant() {
                    int value = 42;
                    return value;
                }
                
                public static void main(String[] args) {
                    int result = getConstant();
                }
            }
            """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Should track local variables even without parameter aliasing
        self.helper.assert_def_use_chain(
            def_use_result,
            "value",
            "value = 42",
            "return value",
            "Local variable should have proper def-use chain",
        )

    def test_unreachable_code(self, helper):
        """Test DFG analysis with unreachable code."""
        if helper.language == "c":
            code = """
            int test_unreachable(int x) {
                return x * 2;
                int unreachable = 999;  // Unreachable
                return unreachable;     // Unreachable
            }
            
            int main() {
                int result = test_unreachable(5);
                return result;
            }
            """
        else:  # java
            code = """
            public class Test {
                public static int testUnreachable(int x) {
                    return x * 2;
                    // Unreachable code would cause compilation error in Java
                }
                
                public static void main(String[] args) {
                    int result = testUnreachable(5);
                }
            }
            """

        cfg, def_use_result, use_def_result = self.helper.build_dfg_from_code(code)

        # Should handle unreachable code gracefully
        self.helper.assert_parameter_alias(
            def_use_result,
            "x",
            "5",
            "return x * 2",
            "Should handle parameter aliasing even with unreachable code",
        )


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
