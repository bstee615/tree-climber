/*
 * Java DFG Stress Test - Comprehensive scenarios for dataflow analysis
 * This file contains complex Java constructs to thoroughly test DFG analysis.
 */

public class DFGStressTest {
    
    // Basic static methods with multiple parameters
    public static int add(int a, int b) {
        int result = a + b;
        return result;
    }
    
    public static int multiply(int x, int y) {
        return x * y;
    }
    
    // Method with parameter modification
    public static int increment(int x) {
        x = x + 1;
        int doubled = x * 2;
        return doubled;
    }
    
    // Recursive method
    public static int factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
    
    // Method with complex control flow
    public static int complexFlow(int input) {
        int result = 0;
        
        if (input > 0) {
            result = input * 2;
            if (result > 10) {
                result = result - 5;
            }
        } else {
            result = input * -1;
            while (result < 10) {
                result = result + 1;
            }
        }
        
        return result;
    }
    
    // Method with loops and method calls
    public static int sumProcessed(int count) {
        int total = 0;
        for (int i = 0; i < count; i++) {
            total = total + increment(i);
        }
        return total;
    }
    
    // Method with multiple local variables
    public static int multiVars(int a, int b, int c) {
        int x = a + b;
        int y = b + c;
        int z = x + y;
        
        // Redefine some variables
        x = z - a;
        y = x + c;
        
        return x + y + z;
    }
    
    // Method with nested method calls
    public static int nestedCalls(int val) {
        int processed = increment(val);
        int doubled = add(processed, processed);
        return complexFlow(doubled);
    }
    
    // Method with enhanced for loop
    public static int arraySum(int[] numbers) {
        int sum = 0;
        for (int num : numbers) {
            sum = sum + increment(num);
        }
        return sum;
    }
    
    // Method with try-catch (exception handling)
    public static int safeDivide(int numerator, int denominator) {
        int result = 0;
        try {
            result = numerator / denominator;
            result = increment(result);
        } catch (ArithmeticException e) {
            result = add(numerator, 1);
        }
        return result;
    }
    
    // Main method with comprehensive testing
    public static void main(String[] args) {
        // Basic assignments
        int x = 5;
        int y = 3;
        
        // Method calls with argument aliasing
        int sum = add(x, y);
        int incX = increment(x);
        
        // Complex expressions
        int complexResult = nestedCalls(x + y);
        
        // Variable reuse
        x = complexResult;
        y = sumProcessed(x);
        
        // Conditional with method calls
        int finalResult;
        if (x > y) {
            finalResult = factorial(5);
        } else {
            finalResult = multiVars(x, y, sum);
        }
        
        // Loop with method calls
        for (int i = 0; i < 3; i++) {
            finalResult = finalResult + add(i, finalResult);
            if (finalResult > 100) {
                break;
            }
        }
        
        // Array processing
        int[] testArray = {1, 2, 3, 4, 5};
        int arrayResult = arraySum(testArray);
        
        // Exception handling
        int safeResult = safeDivide(finalResult, arrayResult);
        
        System.out.println("Final result: " + safeResult);
    }
    
    // Additional test methods
    public static void testSwitchStatement(int value) {
        int result = 0;
        
        switch (value) {
            case 1:
                result = increment(value);
                break;
            case 2:
                result = add(value, 10);
                // Fallthrough
            case 3:
                result = result + complexFlow(value);
                break;
            default:
                result = factorial(value % 5);
        }
    }
    
    // Test method with multiple returns
    public static int multipleReturns(int condition) {
        int x = increment(condition);
        
        if (x < 0) {
            return add(x, -1);
        }
        
        if (x > 100) {
            return complexFlow(x);
        }
        
        return factorial(x % 10);
    }
    
    // Test deeply nested calls
    public static int deeplyNested(int depth) {
        if (depth <= 0) {
            return 1;
        }
        
        int a = increment(depth);
        int b = add(a, depth);
        int c = complexFlow(b);
        
        return deeplyNested(depth - 1) + c;
    }
    
    // Test method overloading (different parameter types)
    public static double add(double a, double b) {
        double result = a + b;
        return result;
    }
    
    // Test static vs instance method patterns
    public static int staticMethod(int param) {
        return increment(param);
    }
    
    // Test lambda expressions (Java 8+)
    public static void testLambdas() {
        int[] numbers = {1, 2, 3, 4, 5};
        int multiplier = 2;
        
        // Simple lambda with closure
        for (int i = 0; i < numbers.length; i++) {
            int processed = increment(numbers[i]);
            int result = multiply(processed, multiplier);
            System.out.println(result);
        }
    }
    
    // Test method with complex parameter patterns
    public static int complexParameters(int first, int second, int third) {
        // Use parameters in different orders
        int a = add(second, third);
        int b = multiply(first, a);
        int c = increment(b);
        
        // Redefine parameters
        first = c;
        second = add(first, third);
        
        return multiVars(first, second, third);
    }
}