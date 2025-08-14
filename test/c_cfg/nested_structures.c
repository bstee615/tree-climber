/**
 * Nested C control structures for CFG testing
 * 
 * This file contains complex nested combinations of control flow constructs:
 * - If statements inside loops
 * - Loops inside if statements
 * - Nested loops (2-level and 3-level)
 * - Switch statements inside loops
 * - Nested switch statements
 * - Mixed break/continue with multiple nesting levels
 * - Complex nested conditions
 * - Deep nesting with all construct types
 * 
 * Use for: Advanced CFG generation testing, edge connectivity validation
 * 
 * These functions test the CFG implementation's ability to properly compose
 * subgraphs when control structures are nested, ensuring correct edge
 * connections across multiple nesting levels and proper break/continue
 * targeting in complex scenarios.
 */

// If statement inside while loop
int if_in_while(int n) {
    int sum = 0;
    while (n > 0) {
        if (n % 2 == 0) {
            sum = sum + n;
        } else {
            sum = sum - n;
        }
        n = n - 1;
    }
    return sum;
}

// While loop inside if statement
int while_in_if(int x) {
    if (x > 0) {
        while (x > 0) {
            x = x - 1;
        }
    } else {
        x = -x;
    }
    return x;
}

// Nested for loops
int nested_for_loops(int rows, int cols) {
    int sum = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            sum = sum + i * j;
        }
    }
    return sum;
}

// For loop inside switch case
int for_in_switch(int mode, int limit) {
    int result = 0;
    switch (mode) {
        case 1:
            for (int i = 0; i < limit; i++) {
                result = result + i;
            }
            break;
        case 2:
            for (int i = limit; i > 0; i--) {
                result = result + i;
            }
            break;
        default:
            result = -1;
    }
    return result;
}

// Switch inside while loop
int switch_in_while(int n) {
    int result = 0;
    while (n > 0) {
        switch (n % 3) {
            case 0:
                result = result + 1;
                break;
            case 1:
                result = result + 2;
                break;
            case 2:
                result = result + 3;
                break;
        }
        n = n - 1;
    }
    return result;
}

// Nested switch statements
int nested_switches(int x, int y) {
    int result = 0;
    switch (x) {
        case 1:
            switch (y) {
                case 1:
                    result = 11;
                    break;
                case 2:
                    result = 12;
                    break;
                default:
                    result = 10;
            }
            break;
        case 2:
            switch (y) {
                case 1:
                    result = 21;
                    break;
                case 2:
                    result = 22;
                    break;
                default:
                    result = 20;
            }
            break;
        default:
            result = 0;
    }
    return result;
}

// Triple nested loops
int triple_nested_loops(int x, int y, int z) {
    int sum = 0;
    for (int i = 0; i < x; i++) {
        for (int j = 0; j < y; j++) {
            for (int k = 0; k < z; k++) {
                if (i == j && j == k) {
                    sum = sum + i + j + k;
                }
            }
        }
    }
    return sum;
}

// Mixed break and continue with nesting
int mixed_break_continue(int limit) {
    int sum = 0;
    for (int i = 0; i < limit; i++) {
        if (i % 5 == 0) {
            continue;  // Skip multiples of 5
        }
        
        for (int j = 0; j < 10; j++) {
            if (j == 5) {
                break;  // Break inner loop at j=5
            }
            
            if (i + j > limit) {
                goto finish;  // Jump out of both loops
            }
            
            sum = sum + i + j;
        }
    }
    
finish:
    return sum;
}

// Complex condition with nested control flow
int complex_nested_conditions(int x) {
    if (x > 0) {
        if (x > 10) {
            while (x > 10) {
                x = x - 1;
                if (x == 15) {
                    break;
                }
            }
        } else {
            for (int i = 0; i < x; i++) {
                if (i == 5) {
                    continue;
                }
                x = x + 1;
                if (x > 20) {
                    return x;
                }
            }
        }
    } else {
        do {
            x = x + 1;
            if (x == 0) {
                break;
            }
        } while (x < 0);
    }
    return x;
}

// Deeply nested with all constructs
int deeply_nested_all_constructs(int n) {
    int result = 0;
    
    if (n > 0) {
        while (n > 0) {
            for (int i = 0; i < n; i++) {
                switch (i % 3) {
                    case 0:
                        if (i > 5) {
                            do {
                                result = result + 1;
                                i = i - 1;
                            } while (i > 3);
                        }
                        break;
                    case 1:
                        if (result > 100) {
                            goto cleanup;
                        }
                        result = result + i;
                        break;
                    case 2:
                        continue;
                    default:
                        break;
                }
            }
            n = n - 1;
        }
    }
    
cleanup:
    return result;
}