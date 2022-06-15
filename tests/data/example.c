int main()
{
    int x = 0;
    x = x + 1;
    if (x > 1) {
        x += 5;
    }
    else {
        x += 50;
    }
    x = x + 2;
    for (int i = 0; i < 10; i ++) {
        x --;
    }
    x = x + 3;
    while (x < 0) {
        x ++;
        x = x + 1;
    }
    x = x + 4;
    return x;
}
