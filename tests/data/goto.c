int a = 3;
    
int main()
{
    int i = 0;
    int x = 0;
    end:
    x -= a;
    for (; true; ) {
        x += 5;
        if (x < 0) {
            goto end;
        }
    }
    printf("%d %d\\n", x, i);
    x = 10;
    return x;
}
