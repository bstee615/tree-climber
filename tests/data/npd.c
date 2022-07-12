#include <stdio.h>

int main(int argc, char **argv)
{
    char *x;
    x = NULL;
    char *y = NULL;
    if (argc > 10) {
        y = "bar";
    }
    printf("%s %s\n", x, y);
    return 0;
}
