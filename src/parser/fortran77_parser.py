"""
fortran77_parser.py  [REFACTORED]
Ponto de entrada do analisador sintático.
Define precedências, constrói o parser PLY e expõe parse().
As regras gramaticais estão em grammar_rules.py.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ply.yacc as yacc
import ply.lex  as plex
import importlib

_lex_mod  = importlib.import_module('lexer.fortran77_lexer')
_rules_mod = importlib.import_module('parser.grammar_rules')

# ply.yacc precisa de encontrar 'tokens' neste módulo
from lexer.tokens import tokens  # noqa: F401

# ============================================================
# CONSTRUÇÃO DO PARSER
# (ply.yacc recolhe as funções p_* do módulo grammar_rules)
# ============================================================

parser = yacc.yacc(
    module=_rules_mod,
    debug=False,
    write_tables=False,
)

# ============================================================
# LEXER COM INJECÇÃO DE LABELS
# ============================================================

class FortranLexer:
    """
    Wraps o lexer base e injeta tokens LABEL antes de cada statement.
    """
    def __init__(self, use_fixed=True):
        self.use_fixed   = use_fixed
        self.token_queue = []
        self._pos        = 0
        self.lineno      = 1
        self.lexpos      = 0

    def input(self, source):
        import ply.lex as inner_lex
        import lexer.rules as _rules
        if self.use_fixed:
            stmts = _lex_mod.preprocess(source)
        else:
            stmts = _lex_mod.preprocess_freeform(source)

        self.token_queue = []
        lno = 1

        for label, code in stmts:
            if label:
                tok = plex.LexToken()
                tok.type   = 'LABEL'
                tok.value  = int(label)
                tok.lineno = lno
                tok.lexpos = 0
                self.token_queue.append(tok)

            inner = inner_lex.lex(module=_rules)
            inner.input(code)
            for t in inner:
                if t.type != 'NEWLINE':
                    t.lineno = lno
                    self.token_queue.append(t)
            lno += 1

            nl = plex.LexToken()
            nl.type   = 'NEWLINE'
            nl.value  = '\n'
            nl.lineno = lno
            nl.lexpos = 0
            self.token_queue.append(nl)

        self._pos = 0

    def token(self):
        if self._pos < len(self.token_queue):
            t = self.token_queue[self._pos]
            self._pos += 1
            return t
        return None

    def clone(self):
        return FortranLexer(self.use_fixed)


# ============================================================
# API PÚBLICA
# ============================================================

def parse(source: str, use_fixed=True, debug=False):
    fl = FortranLexer(use_fixed=use_fixed)
    fl.input(source)
    return parser.parse(None, lexer=fl, debug=debug, tracking=True)


if __name__ == '__main__':
    src = open(
        os.path.join(os.path.dirname(__file__), '../../tests/programs/fatorial.f77')
    ).read()
    ast = parse(src)
    if ast:
        print(ast)
