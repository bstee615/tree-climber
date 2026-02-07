// int fibonacci(int n) {
//     if (n <= 1) {
//         return n;
//     }
//     return fibonacci(n - 1) + fibonacci(n - 2);
// }
void FUN1(void *VAR1) { VAR2 *VAR3, **VAR4, *VAR5, *VAR6; VAR7 *VAR8; HashPosition VAR9; VAR10 **VAR11; long * VAR12;       int VAR13, VAR14, VAR15, *VAR16, VAR17; unsigned char *VAR18 = NULL, **VAR19; char * VAR20; int VAR21; char *VAR22 =NULL; int VAR23 = 0; const VAR24 *VAR25; EVP_CIPHER_CTX VAR26; int VAR35 = 0; void *VAR36 = NULL; void *VAR37 = NULL;  if (FUN2(FUN3(),  "VAR28", &VAR20, &VAR21, &VAR5, &VAR6, &VAR3, &VAR22, &VAR23) == VAR29) { return; }  VAR8 = FUN4(VAR3); VAR17 = VAR8 ? FUN5(VAR8) : 0; if (!VAR17) { FUN6(NULL VAR27, VAR30, "VAR28"); }  if (VAR22) { VAR25 = FUN7(VAR22); if (!VAR25) { FUN6(NULL VAR27, VAR30, "VAR28"); } if (FUN8(VAR25) > 0) { FUN6(NULL VAR27, VAR30, "VAR28"); } } else { VAR25 = FUN9(); }  VAR11 = FUN10(VAR17, sizeof(*VAR11), 0); VAR16 = FUN10(VAR17, sizeof(*VAR16), 0); VAR19 = FUN10(VAR17, sizeof(*VAR19), 0); memset(VAR19, 0, sizeof(*VAR19) * VAR17); VAR12 = FUN10(VAR17, sizeof(long), 0); memset(VAR12, 0, sizeof(*VAR12) * VAR17);   FUN11(VAR8, &VAR9); VAR13 = 0; while (FUN12(VAR8, (void **) &VAR4, &VAR9) == VAR32) { VAR11[VAR13] = FUN13(VAR4, 1, NULL, 0, &VAR12[VAR13] VAR27); if (VAR11[VAR13] == NULL) { FUN6(NULL VAR27, VAR30, "VAR28", VAR13+1); goto VAR34; } VAR19[VAR13] = FUN14(FUN15(VAR11[VAR13]) + 1); FUN16(VAR8, &VAR9); VAR13++; }  if (!FUN17(&VAR26,VAR25,NULL,NULL)) { ; FUN18(&VAR26); goto VAR34; }  VAR35 = FUN19(&VAR26); VAR36 = VAR35 ? FUN14(VAR35 + 1) : NULL; VAR18 = FUN14(VAR21 + FUN20(&VAR26)); FUN18(&VAR26);  if (!FUN21(&VAR26, VAR25, VAR19, VAR16, NULL, VAR11, VAR17) || !FUN22(&VAR26, VAR18, &VAR14, (unsigned char *)VAR20, VAR21)) { ; FUN23(VAR18); FUN18(&VAR26); goto VAR34; }  FUN24(&VAR26, VAR18 + VAR14, &VAR15); if (VAR14 + VAR15 > 0) { FUN25(VAR5); VAR18[VAR14 + VAR15] = 'VAR28'; VAR18 = FUN26(VAR18, VAR14 + VAR15 + 1); FUN27(VAR5, (char *)VAR18, VAR14 + VAR15, 0);  FUN25(VAR6); FUN28(VAR6); for (VAR13=0; VAR13<VAR17; VAR13++) { VAR19[VAR13][VAR16[VAR13]] = 'VAR28'; FUN29(VAR6, FUN26(VAR19[VAR13], VAR16[VAR13] + 1), VAR16[VAR13], 0); VAR19[VAR13] = NULL; } FUN25(*VAR37); if (VAR35) { VAR36[VAR35] = 'VAR28'; FUN27(*VAR37, FUN26(VAR36, VAR35 + 1), VAR35, 0); } else { FUN30(*VAR37); } } else { FUN23(VAR18); } FUN31(VAR14 + VAR15); FUN18(&VAR26);  VAR34: for (VAR13=0; VAR13<VAR17; VAR13++) { if (VAR12[VAR13] == -1) { FUN32(VAR11[VAR13]); } if (VAR19[VAR13]) { FUN23(VAR19[VAR13]); } } FUN23(VAR19); FUN23(VAR16); FUN23(VAR11); FUN23(VAR12); }
// void greet(const char* name) {
//     if (name != nullptr) {
//         printf("Hello, %s!\n", name);
//     } else {
//         printf("Hello, World!\n");
//     }
// }

// int main() {
//     int result = fibonacci(5);
//     greet("User");
//     return 0;
// }