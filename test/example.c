// 
// int add(int a, int b) {
//     a = a + 1;
// 	b = a + 2;
// 	return a + b;
// }

// CWE121_Stack_Based_Buffer_Overflow__CWE129_connect_socket_83_goodB2G :: ~ CWE121_Stack_Based_Buffer_Overflow__CWE129_connect_socket_83_goodB2G ( ) { { int i ; int buffer [ 10 ] = { 0 } ; if ( data >= 0 && data < ( 10 ) ) { buffer [ data ] = 1 ; for ( i = 0 ; i < 10 ; i ++ ) { printIntLine ( buffer [ i ] ) ; } } else { printLine ( "ERROR: Array index is out-of-bounds" ) ; } } }

void FUN1 ( ) { char * VAR1 ; VAR1 = ( char * ) malloc ( 100 * sizeof ( char ) ) ; if ( VAR1 == NULL ) { FUN2 ( - 1 ) ; } VAR1 [ 0 ] = '' ; strcpy ( VAR1 , VAR2 ) ; if ( VAR3 ) { for ( ; * VAR1 != '' ; VAR1 ++ ) { if ( * VAR1 == VAR4 ) { FUN3 ( "" ) ; break ; } } free ( VAR1 ) ; } }