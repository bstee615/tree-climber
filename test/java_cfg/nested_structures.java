/*
 * Nested Control Flow Structures for Java CFG Testing
 * 
 * Purpose: This file contains complex nested combinations of control flow
 * constructs to validate CFG generation for realistic code patterns.
 * These tests ensure proper context management for nested structures.
 * 
 * CFG Testing Strategy:
 * - Validate proper nesting context management (loop/switch/exception stacks)
 * - Ensure break/continue statements connect to correct targets
 * - Verify exception handling integrates correctly with other constructs
 * - Test complex control flow interactions
 * - Validate that inner constructs don't interfere with outer construct connectivity
 * 
 * Key Test Areas:
 * - Conditional statements within loops
 * - Loops within conditional statements  
 * - Nested loops with break/continue
 * - Switch statements within loops
 * - Exception handling within loops and conditionals
 * - Multiple levels of nesting
 * 
 * Context Management:
 * - Loop contexts must be properly stacked for break/continue targets
 * - Switch contexts must be properly stacked for break targets
 * - Exception contexts must be properly stacked for exception flow
 * - Inner contexts should not affect outer context connectivity
 * 
 * Expected Behavior:
 * - Break statements connect to immediate enclosing loop/switch exit
 * - Continue statements connect to immediate enclosing loop header/update
 * - Exception flow should bypass normal control flow
 * - Finally blocks should execute regardless of normal/exception flow
 * 
 * Created: 2025-08-14
 * Test Category: Nested Control Flow Structures
 */

public class NestedStructures {
    
    /**
     * Test 1: If Statement Inside While Loop
     * Expected CFG: Complex branching with loop back-edge and conditional paths
     * Context: Loop context for break/continue, conditional context for if
     * Variables: i (def), conditions use i, inner statements modify i
     */
    public static void ifInWhileLoop() {
        int i = 0;
        while (i < 100) {
            if (i % 10 == 0) {
                System.out.println("Multiple of 10: " + i);
            } else {
                System.out.println("Regular: " + i);
            }
            i++;
        }
    }
    
    /**
     * Test 2: While Loop Inside If Statement
     * Expected CFG: Conditional entry to loop, loop contained within true branch
     * Context: Conditional branches, loop context within true branch
     * Variables: x (def), condition uses x, loop modifies x
     */
    public static void whileLoopInIf() {
        int x = 10;
        if (x > 0) {
            while (x > 0) {
                x--;
                System.out.println(x);
            }
        } else {
            System.out.println("x is not positive");
        }
    }
    
    /**
     * Test 3: Nested For Loops
     * Expected CFG: Outer loop with inner loop completely contained
     * Context: Nested loop contexts, break/continue target management
     * Variables: i (def), j (def), nested loop conditions
     */
    public static void nestedForLoops() {
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 3; j++) {
                System.out.println("i=" + i + ", j=" + j);
                if (i * j > 5) {
                    break;  // Should break inner loop only
                }
            }
            System.out.println("Outer loop iteration " + i);
        }
    }
    
    /**
     * Test 4: Break from Nested Loop
     * Expected CFG: Break statement connects to inner loop exit, not outer loop
     * Context: Proper break target identification in nested contexts
     * Variables: i (def), j (def), conditions use both variables
     */
    public static void breakFromNestedLoop() {
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                if (i + j > 8) {
                    break;  // Breaks from inner loop only
                }
                System.out.println("Sum: " + (i + j));
            }
            System.out.println("Inner loop completed for i=" + i);
        }
    }
    
    /**
     * Test 5: Continue in Nested Loop
     * Expected CFG: Continue connects to inner loop update, not outer loop
     * Context: Proper continue target identification in nested contexts
     * Variables: i (def), j (def), conditions use both variables
     */
    public static void continueInNestedLoop() {
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                if ((i + j) % 2 == 0) {
                    continue;  // Continues inner loop only
                }
                System.out.println("Odd sum: " + (i + j));
            }
        }
    }
    
    /**
     * Test 6: Switch Inside For Loop
     * Expected CFG: Switch completely contained within loop iteration
     * Context: Loop and switch contexts properly managed
     * Variables: i (def), switch uses i, cases modify different variables
     */
    public static void switchInForLoop() {
        int sum = 0;
        for (int i = 0; i < 10; i++) {
            switch (i % 3) {
                case 0:
                    sum += i;
                    break;
                case 1:
                    sum += i * 2;
                    break;
                default:
                    sum += i * 3;
            }
        }
        System.out.println("Sum: " + sum);
    }
    
    /**
     * Test 7: Nested Switch Statements
     * Expected CFG: Inner switch completely contained within outer switch case
     * Context: Nested switch contexts, break targets properly managed
     * Variables: x (def), y (def), both switches use different variables
     */
    public static void nestedSwitchStatements() {
        int x = 2;
        int y = 1;
        switch (x) {
            case 1:
                System.out.println("x is 1");
                break;
            case 2:
                switch (y) {
                    case 1:
                        System.out.println("x=2, y=1");
                        break;
                    case 2:
                        System.out.println("x=2, y=2");
                        break;
                    default:
                        System.out.println("x=2, y=other");
                }
                break;
            default:
                System.out.println("x is other");
        }
    }
    
    /**
     * Test 8: Try-Catch Inside Loop
     * Expected CFG: Exception handling paths within loop iteration
     * Context: Loop and exception contexts managed together
     * Variables: i (def), exception flow bypasses normal loop flow
     */
    public static void tryCatchInLoop() {
        for (int i = 0; i < 10; i++) {
            try {
                int result = 100 / (i - 5);  // Will throw when i=5
                System.out.println("Result: " + result);
            } catch (ArithmeticException e) {
                System.out.println("Division by zero at i=" + i);
            }
        }
    }
    
    /**
     * Test 9: Loop Inside Try-Catch
     * Expected CFG: Loop completely contained within try block
     * Context: Exception context encompasses entire loop
     * Variables: i (def), exception can exit loop early
     */
    public static void loopInTryCatch() {
        try {
            for (int i = 0; i < 10; i++) {
                if (i == 7) {
                    throw new RuntimeException("Error at i=7");
                }
                System.out.println("i: " + i);
            }
        } catch (RuntimeException e) {
            System.out.println("Caught exception: " + e.getMessage());
        }
    }
    
    /**
     * Test 10: Try-Catch-Finally with Complex Flow
     * Expected CFG: Finally block reachable from try, catch, and normal flow
     * Context: Exception handling with guaranteed finally execution
     * Variables: x (def), exception flow and normal flow both reach finally
     */
    public static void tryCatchFinally() {
        int x = 5;
        try {
            if (x > 0) {
                x = x / 0;  // Throws exception
            }
            System.out.println("After division");
        } catch (ArithmeticException e) {
            System.out.println("Arithmetic error");
            x = -1;
        } finally {
            System.out.println("Finally block, x=" + x);
        }
    }
    
    /**
     * Test 11: Deeply Nested Structures
     * Expected CFG: Multiple levels of nesting with proper context management
     * Context: Multiple nested contexts (loop, conditional, exception)
     * Variables: Multiple variables with complex interactions
     */
    public static void deeplyNestedStructures() {
        for (int i = 0; i < 5; i++) {
            if (i % 2 == 0) {
                try {
                    for (int j = 0; j < 3; j++) {
                        switch (j) {
                            case 0:
                                if (i == 0) {
                                    continue;  // Continue inner loop
                                }
                                break;
                            case 1:
                                throw new RuntimeException("Test exception");
                            default:
                                System.out.println("i=" + i + ", j=" + j);
                        }
                    }
                } catch (RuntimeException e) {
                    System.out.println("Exception in iteration " + i);
                }
            }
        }
    }
    
    /**
     * Test 12: Method with Multiple Nested Returns
     * Expected CFG: Multiple return paths from different nesting levels
     * Context: Returns should connect to method exit from any nesting level
     * Variables: x (param), multiple conditional paths
     */
    public static int multipleNestedReturns(int x) {
        if (x > 10) {
            for (int i = 0; i < x; i++) {
                if (i * i > x) {
                    return i;  // Return from within nested loop
                }
            }
            return x;  // Return from if block
        } else {
            while (x > 0) {
                if (x % 2 == 0) {
                    return x / 2;  // Return from within while loop
                }
                x--;
            }
        }
        return 0;  // Default return
    }
}