/*
 * Java-Specific Language Features for CFG Testing
 * 
 * Purpose: This file contains modern Java language features and constructs
 * that are specific to Java (not found in C/C++). These tests validate CFG
 * generation for object-oriented and advanced Java features.
 * 
 * CFG Testing Strategy:
 * - Test object-oriented constructs (inheritance, polymorphism)
 * - Validate modern Java features (lambdas, streams, optional)
 * - Test exception handling unique to Java
 * - Ensure generic and annotation handling
 * - Test inner classes and anonymous classes
 * - Validate static vs instance method distinction
 * 
 * Java-Specific Features:
 * - Lambda expressions and method references
 * - Anonymous classes and inner classes
 * - Generic methods and type parameters
 * - Annotation processing
 * - Static initialization blocks
 * - Constructor chaining (this/super calls)
 * - Method overriding and polymorphism
 * - Interface default methods
 * - Exception handling (try-with-resources)
 * 
 * Expected Behavior:
 * - Lambda expressions should be modeled as separate control flow
 * - Anonymous classes should have separate CFG contexts
 * - Generic type information should not affect CFG structure
 * - Static vs instance distinction should be captured
 * - Exception hierarchies should be properly modeled
 * - Resource management (try-with-resources) should be handled
 * 
 * OOP Constructs:
 * - Method overriding and virtual dispatch
 * - Constructor and initializer blocks
 * - Static vs instance method calls
 * - Field access patterns
 * - Inheritance chains
 * 
 * Created: 2025-08-14
 * Test Category: Java-Specific Language Features
 */

import java.util.*;
import java.io.*;

public class JavaSpecific {
    
    private int instanceField = 0;
    private static int staticField = 100;
    
    // Static initialization block
    static {
        staticField = 200;
        System.out.println("Static initializer executed");
    }
    
    // Instance initialization block
    {
        instanceField = 42;
        System.out.println("Instance initializer executed");
    }
    
    /**
     * Test 1: Lambda Expressions
     * Expected CFG: Lambda expressions as separate control flow contexts
     * Java Feature: Lambda expressions with different syntaxes
     * Variables: numbers (def), lambda parameters and captures
     */
    public static void lambdaExpressions() {
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
        
        // Simple lambda expression
        numbers.forEach(n -> System.out.println(n));
        
        // Lambda with multiple statements
        numbers.stream()
               .filter(n -> {
                   System.out.println("Filtering: " + n);
                   return n % 2 == 0;
               })
               .forEach(System.out::println);
        
        // Lambda with capture
        int multiplier = 3;
        numbers.stream()
               .map(n -> n * multiplier)
               .forEach(System.out::println);
    }
    
    /**
     * Test 2: Method References
     * Expected CFG: Method references should be captured in call metadata
     * Java Feature: Different types of method references
     * Variables: strings (def), method reference usage
     */
    public static void methodReferences() {
        List<String> strings = Arrays.asList("apple", "banana", "cherry");
        
        // Static method reference
        strings.stream()
               .map(String::toUpperCase)
               .forEach(System.out::println);
        
        // Instance method reference
        strings.stream()
               .mapToInt(String::length)
               .forEach(System.out::println);
        
        // Constructor reference
        strings.stream()
               .map(StringBuilder::new)
               .forEach(sb -> sb.append(" modified"));
    }
    
    /**
     * Test 3: Anonymous Classes
     * Expected CFG: Anonymous class methods as separate CFG contexts
     * Java Feature: Anonymous class with method overrides
     * Variables: runnable (def), anonymous class implementation
     */
    public static void anonymousClasses() {
        // Anonymous class implementing Runnable
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                for (int i = 0; i < 3; i++) {
                    System.out.println("Anonymous class execution: " + i);
                    if (i == 1) {
                        break;
                    }
                }
            }
        };
        
        // Anonymous class with multiple methods
        Comparator<String> comparator = new Comparator<String>() {
            @Override
            public int compare(String s1, String s2) {
                if (s1 == null && s2 == null) {
                    return 0;
                } else if (s1 == null) {
                    return -1;
                } else if (s2 == null) {
                    return 1;
                } else {
                    return s1.compareTo(s2);
                }
            }
        };
        
        runnable.run();
    }
    
    /**
     * Test 4: Generic Methods
     * Expected CFG: Generic type parameters should not affect control flow
     * Java Feature: Generic methods with type bounds
     * Variables: list (param), generic type handling
     */
    public static <T extends Comparable<T>> T findMax(List<T> list) {
        if (list == null || list.isEmpty()) {
            return null;
        }
        
        T max = list.get(0);
        for (T item : list) {
            if (item.compareTo(max) > 0) {
                max = item;
            }
        }
        return max;
    }
    
    /**
     * Test 5: Try-with-Resources
     * Expected CFG: Resource management with automatic cleanup
     * Java Feature: Try-with-resources for automatic resource management
     * Variables: br (resource), automatic resource cleanup
     */
    public static void tryWithResources() {
        // Single resource
        try (BufferedReader br = new BufferedReader(new StringReader("test content"))) {
            String line;
            while ((line = br.readLine()) != null) {
                System.out.println("Read line: " + line);
                if (line.contains("test")) {
                    break;
                }
            }
        } catch (IOException e) {
            System.err.println("I/O error: " + e.getMessage());
        }
        
        // Multiple resources
        try (FileInputStream fis = new FileInputStream("dummy.txt");
             BufferedInputStream bis = new BufferedInputStream(fis)) {
            
            int data = bis.read();
            while (data != -1) {
                System.out.print((char) data);
                data = bis.read();
            }
        } catch (IOException e) {
            System.err.println("File error: " + e.getMessage());
        }
    }
    
    /**
     * Test 6: Constructor Chaining
     * Expected CFG: Constructor calls should be modeled properly
     * Java Feature: this() and super() constructor calls
     * Variables: Constructor parameters and field initialization
     */
    public JavaSpecific() {
        this(0);  // Call to other constructor
        System.out.println("Default constructor");
    }
    
    public JavaSpecific(int value) {
        super();  // Explicit super constructor call
        this.instanceField = value;
        System.out.println("Parameterized constructor: " + value);
    }
    
    /**
     * Test 7: Method Overriding and Polymorphism
     * Expected CFG: Method calls should capture potential polymorphism
     * Java Feature: Virtual method dispatch and overriding
     * Variables: obj (def), polymorphic method calls
     */
    public static void methodOverridingAndPolymorphism() {
        Object obj = new JavaSpecific(42);
        
        // Virtual method call (toString is overridden in many classes)
        String str = obj.toString();
        System.out.println("toString result: " + str);
        
        // Polymorphic behavior with lists
        List<String> list = new ArrayList<>();
        list.add("item1");
        list.add("item2");
        
        // Method call that could be ArrayList or LinkedList implementation
        for (String item : list) {
            System.out.println("Item: " + item);
        }
    }
    
    /**
     * Test 8: Static vs Instance Method Calls
     * Expected CFG: Static and instance calls should be distinguished
     * Java Feature: Static method calls vs instance method calls
     * Variables: obj (def), static vs instance call distinction
     */
    public static void staticVsInstanceMethods() {
        JavaSpecific obj = new JavaSpecific();
        
        // Static method call
        staticMethod();
        JavaSpecific.staticMethod();  // Explicit static call
        
        // Instance method call
        obj.instanceMethod();
        
        // Mixed calls in expressions
        int result = Math.max(obj.getInstanceField(), getStaticField());
        System.out.println("Result: " + result);
    }
    
    public static void staticMethod() {
        System.out.println("Static method called");
    }
    
    public void instanceMethod() {
        System.out.println("Instance method called: " + this.instanceField);
    }
    
    public int getInstanceField() {
        return instanceField;
    }
    
    public static int getStaticField() {
        return staticField;
    }
    
    /**
     * Test 9: Exception Handling with Custom Exceptions
     * Expected CFG: Exception hierarchy and multiple catch blocks
     * Java Feature: Custom exception classes and exception hierarchies
     * Variables: value (param), exception flow with different types
     */
    public static void customExceptionHandling(int value) throws CustomException {
        try {
            if (value < 0) {
                throw new CustomException("Negative value not allowed: " + value);
            } else if (value == 0) {
                throw new IllegalArgumentException("Zero value not allowed");
            } else if (value > 100) {
                throw new RuntimeException("Value too large: " + value);
            }
            
            System.out.println("Valid value: " + value);
            
        } catch (CustomException e) {
            System.err.println("Custom exception: " + e.getMessage());
            throw e;  // Re-throw
        } catch (IllegalArgumentException e) {
            System.err.println("Illegal argument: " + e.getMessage());
        } catch (RuntimeException e) {
            System.err.println("Runtime exception: " + e.getMessage());
        } finally {
            System.out.println("Cleanup in finally block");
        }
    }
    
    // Custom exception class
    static class CustomException extends Exception {
        public CustomException(String message) {
            super(message);
        }
    }
    
    /**
     * Test 10: Annotation Processing and Reflection
     * Expected CFG: Annotations should not affect control flow
     * Java Feature: Annotations and basic reflection
     * Variables: clazz (def), reflection-based control flow
     */
    @SuppressWarnings("unchecked")
    public static void annotationsAndReflection() {
        Class<?> clazz = JavaSpecific.class;
        
        try {
            // Reflection-based method call
            java.lang.reflect.Method method = clazz.getMethod("staticMethod");
            method.invoke(null);
            
            // Conditional logic based on reflection
            if (clazz.isAnnotationPresent(Deprecated.class)) {
                System.out.println("Class is deprecated");
            } else {
                System.out.println("Class is current");
            }
            
        } catch (Exception e) {
            System.err.println("Reflection error: " + e.getMessage());
        }
    }
    
    /**
     * Test 11: Inner Classes and Nested Classes
     * Expected CFG: Inner class methods as separate contexts
     * Java Feature: Inner classes with access to outer class members
     * Variables: Outer class fields accessed from inner class
     */
    public void innerClassExample() {
        int localVar = 10;
        
        // Local inner class
        class LocalInner {
            public void doSomething() {
                System.out.println("Accessing outer field: " + instanceField);
                System.out.println("Accessing local var: " + localVar);
                
                // Control flow within inner class
                for (int i = 0; i < 3; i++) {
                    if (i == 1) {
                        continue;
                    }
                    System.out.println("Inner class loop: " + i);
                }
            }
        }
        
        LocalInner inner = new LocalInner();
        inner.doSomething();
    }
    
    /**
     * Test 12: Switch Expressions (Java 14+)
     * Expected CFG: Switch expressions return values
     * Java Feature: Modern switch expressions with yield
     * Variables: value (param), switch expression result
     */
    public static String switchExpression(int value) {
        // Switch expression (Java 14+)
        String result = switch (value) {
            case 1, 2 -> {
                System.out.println("Small number");
                yield "small";
            }
            case 3, 4, 5 -> {
                System.out.println("Medium number");
                yield "medium";
            }
            default -> {
                if (value > 10) {
                    System.out.println("Large number");
                    yield "large";
                } else {
                    System.out.println("Other number");
                    yield "other";
                }
            }
        };
        
        return result;
    }
    
    /**
     * Test 13: Record Classes (Java 14+)
     * Expected CFG: Record methods and constructors
     * Java Feature: Record classes with compact constructors
     * Variables: Record components and validation
     */
    public record Point(int x, int y) {
        // Compact constructor with validation
        public Point {
            if (x < 0 || y < 0) {
                throw new IllegalArgumentException("Coordinates must be non-negative");
            }
        }
        
        // Additional methods in record
        public double distanceFromOrigin() {
            return Math.sqrt(x * x + y * y);
        }
        
        public Point translate(int dx, int dy) {
            return new Point(x + dx, y + dy);
        }
    }
    
    /**
     * Test 14: Pattern Matching (Java 17+)
     * Expected CFG: Pattern matching in instanceof
     * Java Feature: Pattern matching with instanceof
     * Variables: obj (param), pattern matching variables
     */
    public static void patternMatching(Object obj) {
        // Pattern matching with instanceof (Java 17+)
        if (obj instanceof String str && str.length() > 5) {
            System.out.println("Long string: " + str.toUpperCase());
        } else if (obj instanceof Integer num && num > 0) {
            System.out.println("Positive integer: " + (num * 2));
        } else if (obj instanceof List<?> list && !list.isEmpty()) {
            System.out.println("Non-empty list with " + list.size() + " elements");
        } else {
            System.out.println("Other type: " + obj.getClass().getSimpleName());
        }
    }
}