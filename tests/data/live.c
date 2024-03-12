#include <stdio.h>

int main()
{
    int x;
    int y;
    
    y = 10;
    
    x = 10;
    printf("%d\\n", x); // used once
    printf("===");      // still live since it will be used
    a = 20;             // even though another variable is used
    printf("%d\\n", x); // used again

    x = 0;              // overwritten - dead
    x = 5;              // last write - live now
    printf("%d\\n", x);
    printf("===");      // x is dead now -- no more uses of it
}
