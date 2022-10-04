#include "main.h"
#include <stdio.h>

int main() {
    int a = foo(1);
    int b = bar(a);
    printf("%d\n", a + b);
}
