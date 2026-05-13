"""
run_tests.py
Runner de testes automáticos para o compilador Fortran 77.
"""

import sys
import os
import io
import traceback

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lexer.fortran77_lexer import analisar, preprocess
from src.parser.fortran77_parser import parse
from src.semantic.semantic import SemanticAnalyzer
from src.codegen.codegen import CodeGen, print_code
from vm.vm import VM

# ============================================================
# DEFINIÇÃO DOS TESTES
# ============================================================

TESTS = [
    {
        'name'    : 'Hello World',
        'file'    : 'tests/programs/hello.f77',
        'input'   : [],
        'expected': 'Ola, Mundo!',
    },
    {
        'name'    : 'Fatorial de 5',
        'file'    : 'tests/programs/fatorial.f77',
        'input'   : ['5'],
        'expected': '120',
    },
    {
        'name'    : 'Fatorial de 1',
        'file'    : 'tests/programs/fatorial.f77',
        'input'   : ['1'],
        'expected': '1',
    },
    {
        'name'    : 'Numero primo (17)',
        'file'    : 'tests/programs/primo.f77',
        'input'   : ['17'],
        'expected': 'primo',
    },
    {
        'name'    : 'Numero nao primo (4)',
        'file'    : 'tests/programs/primo.f77',
        'input'   : ['4'],
        'expected': 'nao',
    },
    {
        'name'    : 'Soma de array [10,20,30,40,50]',
        'file'    : 'tests/programs/somaarr.f77',
        'input'   : ['10', '20', '30', '40', '50'],
        'expected': '150',
    },
    {
        'name'    : 'Conversor base (10)',
        'file'    : 'tests/programs/conversor.f77',
        'input'   : ['10'],
        'expected': '1010',  # 10 em base 2
    },
]


# ============================================================
# EXECUTOR
# ============================================================

def run_program(source, input_data):
    """
    Compila e executa um programa Fortran 77.
    Devolve (output_str, errors).
    """
    output_lines = []

    def capture_output(text, end='\n'):
        output_lines.append(str(text))

    try:
        ast = parse(source, use_fixed=True)
        if ast is None:
            return '', ['Parse falhou']

        sa = SemanticAnalyzer()
        sa.analyze(ast)

        cg = CodeGen(sa=sa)
        code = cg.generate(ast)

        vm = VM(code, input_data=input_data, output_fn=capture_output)
        vm.run()

        return ''.join(output_lines), []
    except Exception as e:
        return '', [f"Excepção: {e}\n{traceback.format_exc()}"]


# ============================================================
# RUNNER
# ============================================================

def run_tests():
    base_dir = os.path.dirname(__file__)
    passed = 0
    failed = 0
    errors = 0

    print(f"\n{'='*65}")
    print(f"  TESTES DO COMPILADOR FORTRAN 77")
    print(f"{'='*65}")

    for t in TESTS:
        name     = t['name']
        filepath = os.path.join(base_dir, t['file'])
        inp      = t['input']
        expected = t['expected']

        if not os.path.exists(filepath):
            print(f"  [ SKIP ] {name} — ficheiro não encontrado: {filepath}")
            continue

        with open(filepath, 'r') as f:
            source = f.read()

        output, errs = run_program(source, inp)

        if errs:
            print(f"  [ ERR  ] {name}")
            for e in errs[:2]:
                print(f"           {e[:100]}")
            errors += 1
        elif expected.lower() in output.lower():
            print(f"  [ OK   ] {name}")
            passed += 1
        else:
            print(f"  [ FAIL ] {name}")
            print(f"           Esperado: '{expected}'")
            print(f"           Obtido:   '{output.strip()[:80]}'")
            failed += 1

    total = passed + failed + errors
    print(f"\n{'='*65}")
    print(f"  Resultado: {passed}/{total} passaram  |  {failed} falharam  |  {errors} erros")
    print(f"{'='*65}\n")
    return passed, failed, errors


if __name__ == '__main__':
    run_tests()
