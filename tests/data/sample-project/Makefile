all: main
clean:
	rm -f *.o main
a.o: a.c
	gcc -c -o a.o a.c
b.o: b.c
	gcc -c -o b.o b.c
main.o: main.c
	gcc -c -o main.o main.c
main: a.o b.o main.o
	gcc -o main main.o a.o b.o
