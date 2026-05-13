"""
ast_nodes.py
Definições dos nós da Árvore Sintática Abstracta (AST) para Fortran 77.
"""

class Node:
    """Nó base da AST."""
    def __repr__(self):
        return self._repr(0)

    def _repr(self, indent):
        name = self.__class__.__name__
        fields = vars(self)
        lines = [' ' * indent + name]
        for k, v in fields.items():
            if isinstance(v, list):
                lines.append(' ' * (indent+2) + f'{k}:')
                for item in v:
                    if isinstance(item, Node):
                        lines.append(item._repr(indent+4))
                    else:
                        lines.append(' ' * (indent+4) + repr(item))
            elif isinstance(v, Node):
                lines.append(' ' * (indent+2) + f'{k}:')
                lines.append(v._repr(indent+4))
            else:
                lines.append(' ' * (indent+2) + f'{k}: {repr(v)}')
        return '\n'.join(lines)


# ---- Programa / Estrutura ----

class Program(Node):
    def __init__(self, name, units):
        self.name  = name   # string ou None
        self.units = units  # lista de ProgramUnit

class ProgramUnit(Node):
    """PROGRAM, FUNCTION ou SUBROUTINE."""
    def __init__(self, kind, name, params, decls, stmts):
        self.kind   = kind    # 'PROGRAM' | 'FUNCTION' | 'SUBROUTINE'
        self.name   = name
        self.params = params  # lista de IDs (para FUNCTION/SUBROUTINE)
        self.decls  = decls   # lista de Declaration
        self.stmts  = stmts   # lista de Statement

# ---- Declarações ----

class Declaration(Node):
    def __init__(self, dtype, vars_):
        self.dtype = dtype   # 'INTEGER' | 'REAL' | 'LOGICAL' | 'CHARACTER' | etc.
        self.vars  = vars_   # lista de VarDecl

class VarDecl(Node):
    def __init__(self, name, dims=None, length=None):
        self.name   = name    # string
        self.dims   = dims    # lista de Expr (dimensões) ou None
        self.length = length  # para CHARACTER*n

class ImplicitNone(Node):
    pass

class ParameterStmt(Node):
    def __init__(self, assignments):
        self.assignments = assignments  # lista de (name, expr)

class CommonStmt(Node):
    def __init__(self, block, vars_):
        self.block = block
        self.vars  = vars_

class DimensionStmt(Node):
    def __init__(self, vars_):
        self.vars = vars_  # lista de VarDecl

# ---- Statements ----

class LabeledStmt(Node):
    def __init__(self, label, stmt):
        self.label = label
        self.stmt  = stmt

class AssignStmt(Node):
    def __init__(self, target, value):
        self.target = target  # Expr (lvalue)
        self.value  = value   # Expr

class PrintStmt(Node):
    def __init__(self, fmt, items):
        self.fmt   = fmt    # '*' ou label ou string
        self.items = items  # lista de Expr

class ReadStmt(Node):
    def __init__(self, fmt, items):
        self.fmt   = fmt
        self.items = items

class WriteStmt(Node):
    def __init__(self, unit, fmt, items):
        self.unit  = unit
        self.fmt   = fmt
        self.items = items

class IfThenStmt(Node):
    def __init__(self, cond, then_stmts, elseif_clauses, else_stmts):
        self.cond           = cond
        self.then_stmts     = then_stmts
        self.elseif_clauses = elseif_clauses  # lista de (cond, stmts)
        self.else_stmts     = else_stmts      # lista ou None

class ArithmeticIfStmt(Node):
    """IF (expr) label1, label2, label3"""
    def __init__(self, expr, neg_label, zero_label, pos_label):
        self.expr       = expr
        self.neg_label  = neg_label
        self.zero_label = zero_label
        self.pos_label  = pos_label

class LogicalIfStmt(Node):
    """IF (cond) statement"""
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

class DoStmt(Node):
    def __init__(self, label, var, start, stop, step, body):
        self.label = label  # int (rótulo do CONTINUE)
        self.var   = var    # string
        self.start = start  # Expr
        self.stop  = stop   # Expr
        self.step  = step   # Expr ou None
        self.body  = body   # lista de Statement

class ContinueStmt(Node):
    pass

class GotoStmt(Node):
    def __init__(self, label):
        self.label = label  # int

class StopStmt(Node):
    def __init__(self, msg=None):
        self.msg = msg

class ReturnStmt(Node):
    pass

class CallStmt(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # lista de Expr

class FormatStmt(Node):
    def __init__(self, spec):
        self.spec = spec  # string raw

# ---- Expressões ----

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op    = op
        self.left  = left
        self.right = right

class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand

class Var(Node):
    def __init__(self, name):
        self.name = name

class ArrayRef(Node):
    def __init__(self, name, indices):
        self.name    = name
        self.indices = indices  # lista de Expr

class FuncCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class IntLit(Node):
    def __init__(self, value):
        self.value = value

class RealLit(Node):
    def __init__(self, value):
        self.value = value

class LogicalLit(Node):
    def __init__(self, value):
        self.value = value  # True | False

class StringLit(Node):
    def __init__(self, value):
        self.value = value

class DoImplied(Node):
    """(lista, var = start, stop [, step])  — em DATA ou I/O"""
    def __init__(self, items, var, start, stop, step=None):
        self.items = items
        self.var   = var
        self.start = start
        self.stop  = stop
        self.step  = step
