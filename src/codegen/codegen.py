"""
codegen.py  [REFACTORED]
Geração de código para a VM de pilha a partir da AST.
Os detalhes de geração estão nos submódulos:
  - emitter.py   : helpers emit / new_label / emit_label
  - expr_gen.py  : gen_expr, gen_binop
  - stmt_gen.py  : gen_stmt, gen_assign, gen_print, gen_read, gen_do, gen_subprogram, ...
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.ast_nodes import Program, ProgramUnit, Declaration, ParameterStmt
from codegen.emitter  import Emitter
from codegen.expr_gen import ExprGen
from codegen.stmt_gen import StmtGen
from vm.vm import Instr


# ============================================================
# GERADOR DE CÓDIGO  (herda dos três mixins)
# ============================================================

class CodeGen(Emitter, ExprGen, StmtGen):
    def __init__(self, sa=None):
        Emitter.__init__(self)
        self.sa           = sa    # analisador semântico (tabela de símbolos)
        self.current_unit = None
        self.param_map    = {}    # nome → índice, para subprogramas
        self.do_stack     = []    # stack de end_labels para DO loops aninhados

    # --------------------------------------------------------
    # Entrada principal
    # --------------------------------------------------------

    def generate(self, ast: Program):
        """
        Gera código para todas as unidades do programa.
        Subprogramas são emitidos antes do programa principal
        (ficam envolvidos em FUNC / ENDFUNC e não são executados na inicialização).
        """
        main_unit = None
        sub_units = []
        for unit in ast.units:
            if unit.kind == 'PROGRAM':
                main_unit = unit
            else:
                sub_units.append(unit)

        for unit in sub_units:
            self.gen_subprogram(unit)

        if main_unit:
            self.gen_unit(main_unit)

        self.emit('HALT')
        return self.code

    def gen_unit(self, unit: ProgramUnit):
        self.current_unit = unit
        self.param_map    = {}
        for decl in unit.decls:
            self.gen_decl(decl)
        for stmt in unit.stmts:
            self.gen_stmt(stmt)

    def gen_decl(self, decl):
        if isinstance(decl, Declaration):
            pass  # arrays inicializados sob demanda pela VM
        elif isinstance(decl, ParameterStmt):
            for name, expr in decl.assignments:
                self.gen_expr(expr)
                self.emit('STORE', name)


# ============================================================
# UTILITÁRIOS
# ============================================================

def print_code(code):
    print(f"\n{'='*50}")
    print(f"{'#':<5} {'Instrução'}")
    print(f"{'='*50}")
    for i, instr in enumerate(code):
        print(f"{i:<5} {instr}")
    print(f"{'='*50}\n")


def code_to_text(code) -> str:
    """Serializa lista de Instr para texto legível."""
    lines = []
    for instr in code:
        if instr.args:
            parts = [instr.op] + [repr(a) for a in instr.args]
        else:
            parts = [instr.op]
        lines.append(' '.join(parts))
    return '\n'.join(lines)


def text_to_code(text):
    """Deserializa texto para lista de Instr."""
    import ast as pyast
    instrs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        parts = line.split(None, 1)
        op = parts[0]
        if len(parts) == 1:
            instrs.append(Instr(op))
        else:
            args = []
            for tok in parts[1].split():
                try:
                    args.append(pyast.literal_eval(tok))
                except Exception:
                    args.append(tok)
            instrs.append(Instr(op, *args))
    return instrs


def generate(ast, sa=None):
    cg = CodeGen(sa=sa)
    return cg.generate(ast)
