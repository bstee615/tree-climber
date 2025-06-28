# Code
```c
int factorial() { //@entry
    int a = 1; //@stmt1
    int b = 10; //@stmt2
    for (int i = 2; /*@stmt3 @next:[]*/ i <= b /*@stmt4 @next:[stmt7]*/; i ++ /*@stmt5 @next:[stmt4]*/) {
        a *= i; //@stmt6 @next:[stmt5]
    }
    return a; //@stmt7
}
```