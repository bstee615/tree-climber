/**
 * Basic C constructs for CFG testing
 * 
 * This file contains simple, isolated examples of each major C control flow construct:
 * - Sequential statements
 * - If statements (with and without else)
 * - While loops
 * - For loops  
 * - Do-while loops
 * - Switch statements (with breaks and fall-through)
 * - Break and continue statements
 * - Multiple return statements
 * - Goto statements and labels
 * 
 * Use for: Basic functionality testing, individual construct validation
 * 
 * Each function demonstrates a single control flow pattern in isolation,
 * making it easy to validate that individual constructs generate correct
 * CFG structures with proper node types, edge connections, and labels.
 */

// Simple sequence test
int simple_sequence() {
    int x = 5;
    x = x + 1;
    x = x * 2;
    return x;
}

// If statement without else
int if_only(int x) {
    if (x > 0) {
        x = x + 10;
    }
    return x;
}

// If-else statement
int if_else(int x) {
    if (x > 0) {
        x = x + 10;
    } else {
        x = x - 10;
    }
    return x;
}

// While loop
int while_loop(int n) {
    int sum = 0;
    while (n > 0) {
        sum = sum + n;
        n = n - 1;
    }
    return sum;
}

// For loop
int for_loop(int n) {
    int sum = 0;
    for (int i = 1; i <= n; i++) {
        sum = sum + i;
    }
    return sum;
}

// Do-while loop
int do_while_loop(int n) {
    int result = 1;
    do {
        result = result * 2;
        n = n - 1;
    } while (n > 0);
    return result;
}

// Switch statement with breaks
int switch_with_breaks(int x) {
    int result = 0;
    switch (x) {
        case 1:
            result = 10;
            break;
        case 2:
            result = 20;
            break;
        case 3:
            result = 30;
            break;
        default:
            result = -1;
    }
    return result;
}

// Switch statement with fall-through
int switch_fallthrough(int x) {
    int result = 0;
    switch (x) {
        case 1:
            result = result + 1;
            // fall through
        case 2:
            result = result + 2;
            break;
        case 3:
            result = result + 3;
            break;
        default:
            result = -1;
    }
    return result;
}

// Break statement in loop
int break_in_loop(int limit) {
    int sum = 0;
    for (int i = 0; i < 100; i++) {
        sum = sum + i;
        if (sum > limit) {
            break;
        }
    }
    return sum;
}

// Continue statement in loop
int continue_in_loop(int limit) {
    int sum = 0;
    for (int i = 0; i < limit; i++) {
        if (i % 2 == 0) {
            continue;
        }
        sum = sum + i;
    }
    return sum;
}

// Multiple return statements
int multiple_returns(int x) {
    if (x < 0) {
        return -1;
    }
    if (x == 0) {
        return 0;
    }
    if (x > 100) {
        return 100;
    }
    return x;
}

// Goto and labels
int goto_example(int x) {
    if (x < 0) {
        goto negative;
    }
    
    x = x * 2;
    goto end;
    
negative:
    x = -x;
    
end:
    return x;
}