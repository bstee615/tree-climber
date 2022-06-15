/**
 * @file test.c
 * @author Ben Steenhoek
 * @brief 
 * @version 0.1
 * @date 2022-06-15
 * 
 * @copyright Copyright (c) 2022
 * 
 * Wasn't sure if continue inside a do/while loop will go to the first statement, or to the conditional.
 * Made this program to test if it goes to the conditional.
 * Output:
loop header
loop 0
loop end
loop cond
loop header
loop 1
loop end
loop cond
loop header
loop 2
loop end
loop cond
loop header
loop 3
loop end
loop cond
loop header
loop 4
loop end
loop cond
loop header
loop 5
loop cond
loop header
loop 6
loop cond
loop header
loop 7
loop cond
loop header
loop 8
loop cond
loop header
loop 9
loop cond
after loop 10
done
    Looks like it does go to the conditional.
 */
#include <stdio.h>

int main(){
    int i = 0;
    do
    {
        printf("loop header\n");
        printf("loop %d\n", i);
        i ++;
        if (i > 5) continue;
        printf("loop end\n");
    }
    while (printf("loop cond\n") && i < 10);
    printf("after loop %d\n", i);
    printf("done\n");
}