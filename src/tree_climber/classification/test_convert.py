from tree_climber.classification.helper_parser import analyze_source_code
from tree_climber.cli.cpg import CPG
import json
import re
def convert_destructor_to_function(code: str) -> str:
    """
    Convert C++ destructor definition from format:
    'VAR1 :: ~ FUN1 ( ) { ... }'
    to simplified format:
    'void FUN1 ( ) { ... }' (for valid C syntax)
    or just 'FUN1 ( ) { ... }' if add_return_type=False
    
    Also handles cases where a function definition is missing a return type.
    Also adds common type definitions to make normalized code parseable.
    Removes preprocessor directives that can break parsing.
    
    Args:
        code: The C++ function definition string
        
    Returns:
        The converted function definition string with necessary type definitions
    """
    # Strip leading/trailing whitespace
    code = code.strip()
    
    # Remove all preprocessor directives that break parsing
    # These need to be removed as they create malformed syntax when not properly closed
    code = re.sub(r'#if\s+\d+\s*', '', code)     # Remove #if 0 or #if 1
    code = re.sub(r'#ifdef\s+\w+\s*', '', code)  # Remove #ifdef MACRO
    code = re.sub(r'#ifndef\s+\w+\s*', '', code) # Remove #ifndef MACRO
    code = re.sub(r'#else\s*', '', code)         # Remove #else
    code = re.sub(r'#endif\s*', '', code)        # Remove #endif
    code = re.sub(r'#define\s+[^\n]*\n?', '', code)  # Remove #define statements
    
    # Fix malformed function calls with stray identifiers
    # Pattern: FUN() VAR, -> FUN(), (VAR is likely a macro that should be removed)
    code = re.sub(r'\)\s+(VAR\d+)\s*,', '), ', code)
    # Pattern: &VAR VAR27) -> &VAR) (removes trailing macro identifiers in argument lists)
    code = re.sub(r'(\w+)\s+(VAR\d+)\s*\)', r'\1)', code)
    
    # Remove standalone macro/variable identifiers that appear as statements
    # These are likely RETURN_FALSE, RETURN_MM_ERROR macros without proper syntax
    code = re.sub(r';\s*(VAR\d+)\s*;', '; ;', code)  # ; VAR31; -> ; ;
    code = re.sub(r'\{\s*(VAR\d+)\s*;', '{ ;', code)  # { VAR33; -> { ;
    code = re.sub(r'}\s*(VAR\d+)\s*;', '} ;', code)  # } VAR31; -> } ;
    
    # Remove double semicolons
    code = re.sub(r';\s*;', ';', code)
    
    # Declare variables that are used but not declared (from removed #if 0 blocks)
    # Insert declarations at the beginning of the function body
    # This is a simplified approach - just add common undeclared variables
    code = re.sub(r'(\{[^{]*?)(\s+if\s*\()', r'\1 int VAR35 = 0; void *VAR36 = NULL; void *VAR37 = NULL;\2', code, count=1)
    
    # Convert macro-based loop constructs to proper for loops
    # Pattern: FUN5(VAR13, ..., VAR16) { ... } -> for(int VAR16 = 0; VAR16 < 10; VAR16++) { ... }
    # This handles nla_for_each_nested and similar macros
    code = re.sub(r'(\w+)\s*\(\s*(\w+)\s*,\s*[^,)]+\s*,\s*(\w+)\s*\)\s*({[^}]*}|\S+;?)',
                  r'for(int \3 = 0; \3 < 10; \3++) \4', code)
    
    
    # Fix standalone macro identifiers that are likely macro calls  
    # Pattern: { VAR33; -> { ; (macro call after opening brace)
    code = re.sub(r'\{\s*(VAR\d+)\s*;', '{ ;', code)
    # Pattern: ; VAR31; -> ; ; (standalone macro calls between semicolons)
    code = re.sub(r';\s+(VAR\d+)\s*;', '; ;', code)
    # Pattern: } VAR31; -> } ; (standalone macro before closing brace)  
    code = re.sub(r'}\s+(VAR\d+)\s*;', '} ;', code)
    
    # Pattern 1: Match destructor - CLASS_NAME :: ~ FUNCTION_NAME ( ) { ... }
    pattern_destructor = r'^(\w+)\s*::\s*~\s*(\w+)\s*(.*)$'
    match_destructor = re.match(pattern_destructor, code, re.DOTALL)
    
    if match_destructor:
        # Extract function name and the rest (parameters and body)
        function_name = match_destructor.group(2)
        rest = match_destructor.group(3)
        # Add void return type for valid C syntax
        code = f"void {function_name} {rest}"
    else:
        # Pattern 2: Match member function - [return_type] CLASS_NAME :: FUNCTION_NAME ( ... ) [const] { ... }
        # This pattern captures: return type (one or more words), class name, function name, and rest
        pattern_member = r'^([\w\s]+?)\s+(\w+)\s*::\s*(\w+)\s*(.*)$'
        match_member = re.match(pattern_member, code, re.DOTALL)
        
        if match_member:
            return_type = match_member.group(1).strip()
            function_name = match_member.group(3)
            rest = match_member.group(4)
            # Remove 'const' qualifier if present after parameters
            rest = re.sub(r'\)\s+const\s+{', ') {', rest)
            # Reconstruct as a regular function
            code = f"{return_type} {function_name} {rest}"
    
    # Check if the code starts with a function name without return type
    # Pattern: FUNCTION_NAME ( ... ) { ... }
    pattern_no_return = r'^([A-Z_][A-Z0-9_]*)\s*\('
    match_no_return = re.match(pattern_no_return, code)
    
    if match_no_return:
        # Add void return type for valid C syntax
        code = f"void {code}"
    
    # Fix K&R-style or malformed function parameters (must be done AFTER adding return type)
    # Pattern: type FUN(VAR) -> type FUN(void *VAR)
    # This handles cases where parameter has no type specifier
    code = re.sub(r'(\w+)\s+(\w+)\s*\(\s*(\w+)\s*\)', r'\1 \2(void *\3)', code)
    
    # Add common type definitions for normalized code
    # These are placeholder types that appear in vulnerability datasets
    type_defs = """
        typedef void* STREAM;
        typedef unsigned int uint32;
        typedef unsigned short uint16;
        typedef unsigned char uint8;
    """
    return type_defs + code
source_code = """
const VAR1::VAR2& FUN1() { static VAR3::VAR4<VAR1::VAR2> VAR5 { VAR1::FUN2() .FUN3("VAR6", VAR1::VAR2::VAR7< VAR8::VAR9::VAR10>()) .FUN3("VAR6", VAR1::VAR2::VAR7< VAR11::VAR9::VAR12, VAR11::VAR9::VAR13, VAR11::VAR9::VAR14, VAR15::VAR9::VAR16, VAR8::VAR9::VAR10, #if FUN4(VAR17) VAR9::VAR18, #endif VAR19::VAR9::VAR20, VAR21::VAR9::VAR22>()) .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") .FUN5("VAR6", "VAR6") #if FUN4(VAR23) .FUN5("VAR6", "VAR6") #endif .FUN6( "VAR6", "VAR6", VAR1::VAR2::VAR7< VAR24::VAR9::VAR25, VAR24::VAR9::VAR26, VAR11::VAR9::VAR27, #if FUN4(VAR23) VAR28::VAR9::VAR29, VAR30::VAR31::VAR9::VAR32, VAR30::VAR33::VAR9::VAR34, VAR30::VAR35::VAR9::VAR34, VAR30::VAR36::VAR9::VAR37, VAR30::VAR38::VAR9::VAR39, VAR30::VAR40::VAR9::VAR41, VAR30::VAR42::VAR9::VAR43, VAR30::VAR42::VAR9::VAR44, VAR30::VAR45::VAR9::VAR46, VAR47::VAR9::VAR48, #endif VAR49::VAR9::VAR50, #if FUN7(VAR51) VAR52::VAR53, #endif VAR54::VAR9::VAR55, VAR56::VAR9::VAR57, VAR58::VAR9::VAR59, VAR60::VAR9::VAR61,  VAR62::VAR9::VAR34, VAR63::VAR9::VAR39, VAR64::VAR9::VAR34, #if FUN4(VAR65) VAR66::VAR9::VAR39, #else VAR67::VAR9::VAR34, #endif #if FUN4(VAR17) || FUN4(VAR68) || FUN4(VAR69) || \ FUN4(VAR23) VAR70::VAR9::VAR71, VAR70::VAR9::VAR72, #endif #if FUN4(VAR23) VAR73::VAR9::VAR74, #endif VAR9::VAR75, VAR9::VAR76, VAR9::VAR77, VAR9::VAR78, VAR9::VAR79, VAR9::VAR80, VAR81::VAR9::VAR34>()) .FUN8(VAR82::FUN9()) #if FUN4(VAR23) .FUN8(VAR30::VAR42::FUN9()) #endif   .FUN10() }; return *VAR5; }  
"""

# source_code = """
# VAR1 :: ~ FUN1 ( ) { { int VAR2 ; int VAR3 [ 10 ] = { 0 } ; if ( VAR4 >= 0 && VAR4 < ( 10 ) ) { VAR3 [ VAR4 ] = 1 ; for ( VAR2 = 0 ; VAR2 < 10 ; VAR2 ++ ) { FUN2 ( VAR3 [ VAR2 ] ) ; } } else { FUN3 ( "" ) ; } } } 
# """

def main():
    new_source = convert_destructor_to_function(source_code)
    print(new_source)
    cpg = analyze_source_code(new_source, language="cpp")
    data = cpg.save_json()
    new_cpg = CPG.load_json(data)
    with open("./output_cpg_new_c.json", "w", encoding="utf-8") as f:
        json.dump(new_cpg.to_dict(), f, indent=2)

if __name__ == "__main__":
    main()