/*
 * Basic Control Flow Constructs for Java CFG Testing
 * 
 * Purpose: This file contains isolated examples of fundamental Java control flow
 * constructs to validate CFG generation accuracy. Each method demonstrates a
 * specific construct in its simplest form.
 * 
 * CFG Testing Strategy:
 * - Each method should generate a well-formed CFG with proper entry/exit nodes
 * - Sequential statements should be connected linearly
 * - Conditional statements should have true/false labeled edges
 * - Loop constructs should have proper back-edges and exit conditions
 * - Jump statements should connect to appropriate targets
 * - Method definitions should capture parameters in entry node metadata
 * 
 * Expected Node Types:
 * - ENTRY: Method entry points with parameters
 * - EXIT: Method exit points
 * - STATEMENT: Sequential statements (assignments, calls, declarations)
 * - CONDITION: If statement conditions
 * - LOOP_HEADER: Loop condition evaluations
 * - BREAK/CONTINUE: Jump statements within loops
 * - RETURN: Method exit statements
 * - SWITCH_HEAD: Switch expression evaluation
 * - CASE: Switch case labels (may be removed by post-processing)
 * 
 * Variable Analysis:
 * - Variable definitions should be tracked in node metadata
 * - Variable uses should be identified correctly
 * - Method calls should be captured in node metadata
 * 
 * Created: 2025-08-14
 * Test Category: Basic Control Flow Constructs
 */

public class BasicConstructs {
    
    /**
     * Test 1: Sequential Statements
     * Expected CFG: ENTRY -> STATEMENT -> STATEMENT -> STATEMENT -> EXIT
     * Variables: a (def), b (def), c (def)
     */
    public static void sequentialStatements() {
        int a = 5;
        int b = a + 10;
        int c = a * b;
    }
    
    /**
     * Test 2: Method with Parameters
     * Expected CFG: ENTRY(params: x, y) -> STATEMENT -> EXIT
     * Variables: x (param), y (param), result (def)
     */
    public static int methodWithParameters(int x, int y) {
        int result = x + y;
        return result;
    }
    
    /**
     * Test 3: Empty Method
     * Expected CFG: ENTRY -> EXIT (direct connection)
     * Variables: none
     */
    public static void emptyMethod() {
    }
    
    /**
     * Test 4: Simple If Statement (no else)
     * Expected CFG: ENTRY -> CONDITION -> [true: STATEMENT] -> EXIT
     *                                  -> [false: EXIT]
     * Variables: x (def), condition uses x
     */
    public static void simpleIf() {
        int x = 5;
        if (x > 0) {
            x = x + 1;
        }
    }
    
    /**
     * Test 5: If-Else Statement
     * Expected CFG: ENTRY -> CONDITION -> [true: STATEMENT] -> EXIT
     *                                  -> [false: STATEMENT] -> EXIT
     * Variables: x (def), condition and statements use x
     */
    public static void ifElse() {
        int x = 5;
        if (x > 0) {
            x = x + 1;
        } else {
            x = x - 1;
        }
    }
    
    /**
     * Test 6: While Loop
     * Expected CFG: ENTRY -> LOOP_HEADER -> [true: STATEMENT] -> (back to LOOP_HEADER)
     *                                    -> [false: EXIT]
     * Variables: i (def), condition and body use/modify i
     */
    public static void whileLoop() {
        int i = 0;
        while (i < 10) {
            i = i + 1;
        }
    }
    
    /**
     * Test 7: For Loop
     * Expected CFG: ENTRY -> STATEMENT(init) -> LOOP_HEADER(condition) -> 
     *               [true: STATEMENT(body)] -> STATEMENT(update) -> (back to LOOP_HEADER)
     *               [false: EXIT]
     * Variables: i (def in init), condition and update use/modify i
     */
    public static void forLoop() {
        for (int i = 0; i < 10; i++) {
            System.out.println(i);
        }
    }
    
    /**
     * Test 8: Enhanced For Loop (for-each)
     * Expected CFG: ENTRY -> LOOP_HEADER(hasNext) -> 
     *               [true: STATEMENT(element assignment)] -> STATEMENT(body) -> (back to LOOP_HEADER)
     *               [false: EXIT]
     * Variables: arr (def), item (def in loop), loop uses arr
     */
    public static void enhancedForLoop() {
        int[] arr = {1, 2, 3, 4, 5};
        for (int item : arr) {
            System.out.println(item);
        }
    }
    
    /**
     * Test 9: Do-While Loop
     * Expected CFG: ENTRY -> STATEMENT(body) -> LOOP_HEADER(condition) ->
     *               [true: back to STATEMENT(body)]
     *               [false: EXIT]
     * Variables: i (def), condition and body use/modify i
     */
    public static void doWhileLoop() {
        int i = 0;
        do {
            i = i + 1;
        } while (i < 10);
    }
    
    /**
     * Test 10: Break in Loop
     * Expected CFG: ENTRY -> LOOP_HEADER -> [true: CONDITION] -> [true: BREAK -> EXIT]
     *                                                         -> [false: STATEMENT] -> (back to LOOP_HEADER)
     *                                    -> [false: EXIT]
     * Variables: i (def), conditions use i
     */
    public static void breakInLoop() {
        for (int i = 0; i < 100; i++) {
            if (i == 5) {
                break;
            }
            System.out.println(i);
        }
    }
    
    /**
     * Test 11: Continue in Loop
     * Expected CFG: ENTRY -> LOOP_HEADER -> [true: CONDITION] -> [true: CONTINUE -> update]
     *                                                         -> [false: STATEMENT] -> update -> LOOP_HEADER
     *                                    -> [false: EXIT]
     * Variables: i (def), conditions use i
     */
    public static void continueInLoop() {
        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                continue;
            }
            System.out.println(i);
        }
    }
    
    /**
     * Test 12: Return Statement
     * Expected CFG: ENTRY -> STATEMENT -> CONDITION -> [true: RETURN -> EXIT]
     *                                                -> [false: RETURN -> EXIT]
     * Variables: x (def), condition uses x
     */
    public static int returnStatement() {
        int x = 5;
        if (x > 0) {
            return x;
        }
        return -x;
    }
    
    /**
     * Test 13: Switch Statement with Breaks
     * Expected CFG: ENTRY -> SWITCH_HEAD -> [1: STATEMENT -> BREAK -> EXIT]
     *                                    -> [2: STATEMENT -> BREAK -> EXIT]
     *                                    -> [default: STATEMENT -> EXIT]
     * Variables: x (def), value (def), switch uses value
     */
    public static void switchWithBreaks() {
        int value = 2;
        int x = 0;
        switch (value) {
            case 1:
                x = 10;
                break;
            case 2:
                x = 20;
                break;
            default:
                x = -1;
        }
    }
    
    /**
     * Test 14: Switch with Fall-through
     * Expected CFG: ENTRY -> SWITCH_HEAD -> [1: STATEMENT] -> [fall-through to case 2]
     *                                    -> [2: STATEMENT] -> [fall-through to default]
     *                                    -> [default: STATEMENT -> EXIT]
     * Variables: x (def), value (def), switch uses value
     */
    public static void switchFallthrough() {
        int value = 1;
        int x = 0;
        switch (value) {
            case 1:
                x = x + 10;  // Fall through to case 2
            case 2:
                x = x + 20;  // Fall through to default
            default:
                x = x + 1;
        }
    }
    
    /**
     * Test 15: Method Calls
     * Expected CFG: ENTRY -> STATEMENT -> STATEMENT -> EXIT
     * Variables: result (def), method calls tracked in metadata
     */
    public static void methodCalls() {
        int result = Math.max(5, 10);
        System.out.println(result);
    }
    
    /**
     * Test 16: Constructor (for constructor CFG testing)
     * Expected CFG: ENTRY(params: value) -> STATEMENT -> EXIT
     * Variables: value (param), this.field (def)
     */
    private int field;
    public BasicConstructs(int value) {
        this.field = value;
    }
}