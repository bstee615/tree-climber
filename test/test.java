public class Test {
    public int testMethod(int input) {
        // Basic variable declarations and statements
        int x = input;
        System.out.println("Input: " + x);
        
        // If-else statement
        if (x > 0) {
            x = x + 1;
            System.out.println("positive");
        } else {
            x = x - 1;
            System.out.println("negative");
        }
        
        // While loop with break
        while (x < 10) {
            if (x == 5) {
                break;
            }
            x++;
        }
        
        // Do-while loop with continue
        do {
            x--;
            if (x % 2 == 0) {
                continue;
            }
            System.out.println(x);
        } while (x > 0);
        
        // For loop
        for (int i = 0; i < 3; i++) {
            x += i;
        }
        
        // Enhanced for loop (for-each)
        int[] numbers = {1, 2, 3};
        for (int num : numbers) {
            x += num;
        }
        
        // Switch statement
        switch (x % 3) {
            case 0:
                x *= 2;
                break;
            case 1:
                x += 1;
                // Fall through
            case 2:
                x -= 1;
                break;
            default:
                x = 0;
        }
        
        return x;
    }

    public static void main(String[] args) {
        Test t = new Test();
        int result = t.testMethod(5);
        System.out.println("Result: " + result);
    }
}
