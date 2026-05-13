"""
fortran77_lexer.py  [REFACTORED]
Ponto de entrada do analisador léxico.
Constrói o lexer PLY a partir de rules.py e expõe tokenize_source / analisar.
Os detalhes estão nos submódulos:
  - preprocessor.py  : pré-processamento de linhas (formato fixo/livre)
  - tokens.py        : palavras reservadas e lista de tokens
  - rules.py         : regras t_* do PLY
"""

import ply.lex as lex

# Reexporta para compatibilidade com o parser (que importa deste módulo)
from lexer.preprocessor import preprocess, preprocess_freeform, preprocess_auto  # noqa: F401
from lexer.tokens import reserved, tokens  # noqa: F401
import lexer.rules as _rules

# ============================================================
# CONSTRUÇÃO DO LEXER
# ============================================================

lexer = lex.lex(module=_rules)


# ============================================================
# TOKENIZAR COM PRÉ-PROCESSAMENTO
# ============================================================

def tokenize_source(source: str, use_fixed=True):
    """
    Tokeniza código Fortran 77.
    Devolve lista de tuplos (tipo, valor, linha), com tokens LABEL injectados.
    """
    if use_fixed:
        statements = preprocess(source)
    else:
        statements = preprocess_freeform(source)

    all_tokens = []
    for label, code in statements:
        if label:
            all_tokens.append(('LABEL', int(label), 0))
        lx = lex.lex(module=_rules)
        lx.input(code)
        for tok in lx:
            if tok.type == 'NEWLINE':
                continue
            all_tokens.append((tok.type, tok.value, tok.lineno))
        all_tokens.append(('NEWLINE', '\n', 0))

    return all_tokens


# ============================================================
# FUNÇÃO DE DEBUG / TESTE
# ============================================================

def analisar(codigo: str, use_fixed=True):
    """Imprime a sequência de tokens para debug."""
    if use_fixed:
        stmts = preprocess(codigo)
    else:
        stmts = preprocess_freeform(codigo)

    print(f"\n{'='*65}")
    print(f"{'TOKEN':<25} {'TIPO':<22} {'LINHA'}")
    print(f"{'='*65}")

    for label, code in stmts:
        if label:
            print(f"{'[LABEL] '+label:<25} {'LABEL':<22}")
        lx = lex.lex(module=_rules)
        lx.input(code)
        for tok in lx:
            if tok.type != 'NEWLINE':
                print(f"{str(tok.value):<25} {tok.type:<22} {tok.lineno}")
        print(f"{'---NEWLINE---':<25}")
    print(f"{'='*65}\n")


# ============================================================
# TESTE STANDALONE
# ============================================================

if __name__ == '__main__':
    programa = """\
      PROGRAM SOMAARR
      INTEGER NUMS(5)
      INTEGER I, SOMA
      SOMA = 0
      PRINT *, 'Introduza 5 numeros inteiros:'
      DO 30 I = 1, 5
      READ *, NUMS(I)
      SOMA = SOMA + NUMS(I)
 30   CONTINUE
      PRINT *, 'A soma dos numeros e: ', SOMA
      END
"""
    print("Código Fortran 77 a analisar:")
    print(programa)
    analisar(programa)
