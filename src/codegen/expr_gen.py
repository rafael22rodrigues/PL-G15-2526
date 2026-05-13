"""
expr_gen.py
Geração de código VM para expressões (gen_expr, gen_binop).
Mixin utilizado pelo CodeGen principal.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.ast_nodes import (
    IntLit, RealLit, LogicalLit, StringLit,
    Var, ArrayRef, FuncCall, BinOp, UnaryOp,
)


class ExprGen:
    """Mixin com métodos de geração de código para expressões."""

    # --------------------------------------------------------
    # Ponto de entrada principal
    # --------------------------------------------------------

    def gen_expr(self, expr):
        if isinstance(expr, IntLit):
            self.emit('PUSH', expr.value)

        elif isinstance(expr, RealLit):
            self.emit('PUSH', expr.value)

        elif isinstance(expr, LogicalLit):
            self.emit('PUSH', expr.value)

        elif isinstance(expr, StringLit):
            self.emit('PUSH', expr.value)

        elif isinstance(expr, Var):
            self.emit('LOAD', expr.name)

        elif isinstance(expr, ArrayRef):
            indices = getattr(expr, 'indices', None) or getattr(expr, 'args', None) or []
            idx = indices[0] if indices else None
            if idx:
                self.gen_expr(idx)
            self.emit('LOADARR', expr.name)

        elif isinstance(expr, FuncCall):
            self._gen_func_call_expr(expr)

        elif isinstance(expr, BinOp):
            self.gen_binop(expr)

        elif isinstance(expr, UnaryOp):
            self.gen_expr(expr.operand)
            if expr.op == '-':
                self.emit('UMINUS')
            elif expr.op == '.NOT.':
                self.emit('NOT')

    # --------------------------------------------------------
    # Chamadas de função em expressões
    # --------------------------------------------------------

    def _gen_func_call_expr(self, expr: FuncCall):
        name = expr.name
        args = expr.args if hasattr(expr, 'args') else []

        intrinsics_map = {
            'MOD'  : ('IMOD',      2),
            'ABS'  : ('ABS_FUNC',  1),
            'SQRT' : ('SQRT_FUNC', 1),
            'INT'  : ('INTCAST',   1),
            'FLOAT': ('FLOATCAST', 1),
            'REAL' : ('FLOATCAST', 1),
            'DBLE' : ('FLOATCAST', 1),
        }

        if name in intrinsics_map:
            vm_op, nargs = intrinsics_map[name]
            for a in args[:nargs]:
                self.gen_expr(a)
            self.emit(vm_op)

        elif name in ('MAX', 'MIN'):
            # Reduz sobre os argumentos usando CALL MAX/MIN 2
            self.gen_expr(args[0])
            for a in args[1:]:
                self.gen_expr(a)
                self.emit('CALL', name, 2)

        else:
            # Pode ser array ou função de utilizador — emite CALL
            for a in args:
                self.gen_expr(a)
            self.emit('CALL', name, len(args))

    # --------------------------------------------------------
    # Operações binárias
    # --------------------------------------------------------

    def gen_binop(self, expr: BinOp):
        op = expr.op

        # AND / OR sem curto-circuito (avalia ambos os lados)
        if op in ('.AND.', '.OR.'):
            self.gen_expr(expr.left)
            self.gen_expr(expr.right)
            self.emit('AND' if op == '.AND.' else 'OR')
            return

        self.gen_expr(expr.left)
        self.gen_expr(expr.right)

        op_map = {
            '+'      : 'ADD',
            '-'      : 'SUB',
            '*'      : 'MUL',
            '/'      : 'DIV',
            '**'     : 'POW',
            '//'     : 'CONCAT',
            '.EQ.'   : 'EQ',  '.NE.' : 'NE',
            '.LT.'   : 'LT',  '.LE.' : 'LE',
            '.GT.'   : 'GT',  '.GE.' : 'GE',
            '=='     : 'EQ',  '/='   : 'NE',
            '<'      : 'LT',  '<='   : 'LE',
            '>'      : 'GT',  '>='   : 'GE',
            '.EQV.'  : 'EQ',
            '.NEQV.' : 'NE',
        }
        vm_op = op_map.get(op)
        if vm_op:
            self.emit(vm_op)
        else:
            print(f"[CODEGEN] Operador desconhecido: {op}")
