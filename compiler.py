"""
compiler.py
Ponto de entrada do compilador Fortran 77.
Orquestra: Lexer -> Parser -> Semântica -> CodeGen -> VM
"""

import sys
import os
import argparse

# Adiciona o src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.lexer.fortran77_lexer import analisar, preprocess, preprocess_freeform
from src.parser.fortran77_parser import parse
from src.semantic.semantic import SemanticAnalyzer
from src.codegen.codegen import CodeGen, print_code, code_to_text
from vm.vm import VM


def compile_source(source: str, use_fixed=True, verbose=False, run=False,
                   input_data=None, output_vm_file=None):
    """
    Pipeline completo de compilação.
    Devolve (code, errors) onde code é lista de Instr e errors é lista de strings.
    """
    errors = []

    #  1. PRÉ-PROCESSAMENTO + ANÁLISE LÉXICA
    if verbose:
        print("\n" + "="*60)
        print("FASE 1: ANÁLISE LÉXICA")
        print("="*60)
        analisar(source, use_fixed=use_fixed)

    #  2. ANÁLISE SINTÁTICA
    if verbose:
        print("\n" + "="*60)
        print("FASE 2: ANÁLISE SINTÁTICA")
        print("="*60)

    ast = parse(source, use_fixed=use_fixed)
    if ast is None:
        errors.append("[COMPILADOR] Falha na análise sintática.")
        return None, errors

    if verbose:
        print(ast)

    #  3. ANÁLISE SEMÂNTICA
    if verbose:
        print("\n" + "="*60)
        print("FASE 3: ANÁLISE SEMÂNTICA")
        print("="*60)

    sa = SemanticAnalyzer()
    ok = sa.analyze(ast)
    sem_errors, sem_warnings = sa.report()
    errors.extend(sem_errors)

    if not ok and not verbose:
        for e in sem_errors:
            print(e)

    # 4. GERAÇÃO DE CÓDIGO
    if verbose:
        print("\n" + "="*60)
        print("FASE 4: GERAÇÃO DE CÓDIGO VM")
        print("="*60)

    cg = CodeGen(sa=sa)
    code = cg.generate(ast)

    if verbose:
        print_code(code)

    # 5. GUARDAR CÓDIGO VM
    if output_vm_file:
        vm_text = code_to_text(code)
        with open(output_vm_file, 'w') as f:
            f.write(vm_text)
        print(f"[COMPILADOR] Código VM escrito em: {output_vm_file}")

    # 6. EXECUÇÃO NA VM
    if run:
        if verbose:
            print("\n" + "="*60)
            print("FASE 5: EXECUÇÃO NA VM")
            print("="*60)
        vm = VM(code, input_data=input_data)
        vm.run()
        return code, errors

    return code, errors


def main():
    parser = argparse.ArgumentParser(
        description='Compilador Fortran 77 → VM de Pilha',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Exemplos:
  python compiler.py programa.f77            # compila e corre
  python compiler.py programa.f77 -v         # verbose (mostra todas as fases)
  python compiler.py programa.f77 -o out.vm  # guarda código VM
  python compiler.py programa.f77 --lex-only # apenas análise léxica
  python compiler.py programa.f77 --parse-only # apenas parsing
  python compiler.py programa.f77 --free-form  # formato livre (& continuação)
"""
    )
    parser.add_argument('file',          help='Ficheiro Fortran 77 (.f77 ou .f)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verbose')
    parser.add_argument('-o', '--output',  default=None,        help='Ficheiro de saída VM')
    parser.add_argument('--lex-only',    action='store_true', help='Apenas análise léxica')
    parser.add_argument('--parse-only',  action='store_true', help='Apenas parsing')
    parser.add_argument('--free-form',   action='store_true', help='Formato livre')
    parser.add_argument('--no-run',      action='store_true', help='Não executar na VM')
    parser.add_argument('--input',       default=None, help='Ficheiro de input para a VM')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERRO] Ficheiro não encontrado: {args.file}")
        sys.exit(1)

    with open(args.file, 'r') as f:
        source = f.read()

    use_fixed = not args.free_form

    # Modo léxico apenas
    if args.lex_only:
        analisar(source, use_fixed=use_fixed)
        sys.exit(0)

    # Modo parser apenas
    if args.parse_only:
        ast = parse(source, use_fixed=use_fixed)
        if ast:
            print(ast)
        sys.exit(0)

    # Input para VM
    input_data = None
    if args.input:
        with open(args.input, 'r') as f:
            input_data = [line.strip() for line in f if line.strip()]

    # Compilação completa
    code, errors = compile_source(
        source,
        use_fixed=use_fixed,
        verbose=args.verbose,
        run=not args.no_run,
        input_data=input_data,
        output_vm_file=args.output
    )

    if errors:
        print("\n[COMPILADOR] Erros encontrados:")
        for e in errors:
            print(" ", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
