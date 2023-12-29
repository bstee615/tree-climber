int main() {
    x = 0;
    if (x > 0) {
        x += 15;
        return x;
    }
    else
        for (int i = 0; i < 10; i ++) {
            x += i;
            if (x)
                continue;
            x -= i;
        }
    return x + 10
}
