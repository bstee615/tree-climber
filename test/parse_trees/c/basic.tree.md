# Code
```c
int factorial() {
    int a = 1;
    int b = 10;
    for (int i = 2; i <= b; i ++) {
        a *= i;
    }
    return a;
}
```

# Expect
```xml
<test_spec>
<counts
    nodes="9"
    ENTRY="1"
    EXIT="1"
    STATEMENT="6"
    LOOP_HEADER="1"
/>
</test_spec>
```
