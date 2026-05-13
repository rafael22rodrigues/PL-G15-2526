"""
semantic.py
Análise Semântica para Fortran 77.
- Tabela de símbolos por scope
- Verificação de tipos
- Resolução ArrayRef vs FuncCall
- Validação de labels DO/CONTINUE
- Regra de tipagem implícita (I-N = INTEGER, restante = REAL)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.ast_nodes import *


# ============================================================
# TABELA DE SÍMBOLOS
# ============================================================

class Symbol:
    def __init__(self, name, stype, dims=None, is_param=False, is_func=False):
        self.name     = name
        self.stype    = stype    # 'INTEGER'|'REAL'|'LOGICAL'|'CHARACTER'|'DOUBLE PRECISION'
        self.dims     = dims     # lista de tamanhos (inteiros) para arrays, ou None
        self.is_param = is_param
        self.is_func  = is_func

    def __repr__(self):
        return f"Symbol({self.name}, {self.stype}, dims={self.dims})"


class SymbolTable:
    def __init__(self, parent=None, scope_name='global'):
        self.parent     = parent
        self.scope_name = scope_name
        self.symbols    = {}

    def declare(self, sym: Symbol):
        if sym.name in self.symbols:
            return False  # redeclaração
        self.symbols[sym.name] = sym
        return True

    def lookup(self, name: str):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str):
        return self.symbols.get(name)


# ============================================================
# FUNÇÕES INTRÍNSECAS
# ============================================================
INTRINSICS = {
    'MOD'  : 'INTEGER',
    'ABS'  : 'REAL',
    'SQRT' : 'REAL',
    'INT'  : 'INTEGER',
    'FLOAT': 'REAL',
    'MAX'  : 'REAL',
    'MIN'  : 'REAL',
    'REAL' : 'REAL',
    'IABS' : 'INTEGER',
    'LEN'  : 'INTEGER',
    'INDEX': 'INTEGER',
    'CHAR' : 'CHARACTER',
    'ICHAR': 'INTEGER',
    'DBLE' : 'DOUBLE PRECISION',
    'CMPLX': 'COMPLEX',
    'AIMAG': 'REAL',
    'CONJG': 'COMPLEX',
    'AINT' : 'REAL',
    'ANINT': 'REAL',
    'NINT' : 'INTEGER',
    'IDINT': 'INTEGER',
    'SNGL' : 'REAL',
    'EXP'  : 'REAL',
    'LOG'  : 'REAL',
    'LOG10': 'REAL',
    'SIN'  : 'REAL',
    'COS'  : 'REAL',
    'TAN'  : 'REAL',
    'ASIN' : 'REAL',
    'ACOS' : 'REAL',
    'ATAN' : 'REAL',
    'ATAN2': 'REAL',
    'SINH' : 'REAL',
    'COSH' : 'REAL',
    'TANH' : 'REAL',
    'SIGN' : 'REAL',
    'DIM'  : 'REAL',
    'DPROD': 'DOUBLE PRECISION',
}


def implicit_type(name: str) -> str:
    """Regra de tipagem implícita: I, J, K, L, M, N → INTEGER, resto → REAL."""
    if name and name[0].upper() in 'IJKLMN':
        return 'INTEGER'
    return 'REAL'


# ============================================================
# ANALISADOR SEMÂNTICO
# ============================================================

class SemanticAnalyzer:
    def __init__(self):
        self.errors   = []
        self.warnings = []
        self.global_table = SymbolTable(scope_name='global')
        self.current_table = self.global_table
        self.current_unit  = None
        self.implicit_none = False
        # Labels de DO conhecidos neste scope: label -> DoStmt
        self.do_labels = {}
        # Todos os labels definidos neste unit
        self.defined_labels = set()
        # Todas as referências a labels (GOTO, DO)
        self.referenced_labels = set()

    def error(self, msg):
        self.errors.append(f"[SEMÂNTICO] {msg}")

    def warning(self, msg):
        self.warnings.append(f"[AVISO] {msg}")

    def analyze(self, ast: Program):
        for unit in ast.units:
            self.analyze_unit(unit)
        return len(self.errors) == 0

    def analyze_unit(self, unit: ProgramUnit):
        self.current_unit  = unit
        self.implicit_none = False
        self.do_labels     = {}
        self.defined_labels= set()
        self.referenced_labels = set()

        # Novo scope
        self.current_table = SymbolTable(
            parent=self.global_table,
            scope_name=unit.name
        )

        # Registar parâmetros formais
        for p in unit.params:
            sym = Symbol(p, implicit_type(p), is_param=True)
            self.current_table.declare(sym)

        # Para FUNCTION, registar o próprio nome como variável de retorno
        if unit.kind == 'FUNCTION':
            ret_type = getattr(unit, 'return_type', None) or implicit_type(unit.name)
            self.current_table.declare(Symbol(unit.name, ret_type, is_func=True))
            # Registar também na tabela global para chamadas
            self.global_table.declare(Symbol(unit.name, ret_type, is_func=True))

        if unit.kind == 'SUBROUTINE':
            self.global_table.declare(Symbol(unit.name, 'VOID', is_func=True))

        # Processar declarações
        for d in unit.decls:
            self.analyze_decl(d)

        # Recolher todos os labels definidos
        self._collect_labels(unit.stmts)

        # Processar statements
        for s in unit.stmts:
            self.analyze_stmt(s)

        # Verificar referências a labels
        for lbl in self.referenced_labels:
            if lbl not in self.defined_labels:
                self.error(f"Label {lbl} referenciado mas não definido em {unit.name}")

    def _collect_labels(self, stmts):
        for s in stmts:
            if isinstance(s, LabeledStmt):
                self.defined_labels.add(s.label)
                self._collect_labels([s.stmt])
            elif isinstance(s, DoStmt):
                self.defined_labels.add(s.label)
                self._collect_labels(s.body)
            elif isinstance(s, IfThenStmt):
                self._collect_labels(s.then_stmts)
                for _, body in s.elseif_clauses:
                    self._collect_labels(body)
                if s.else_stmts:
                    self._collect_labels(s.else_stmts)

    def analyze_decl(self, d):
        if isinstance(d, ImplicitNone):
            self.implicit_none = True
            return

        if isinstance(d, Declaration):
            for v in d.vars:
                existing = self.current_table.lookup_local(v.name)
                if existing:
                    self.error(f"Variável '{v.name}' redeclarada em {self.current_unit.name}")
                else:
                    sym = Symbol(v.name, d.dtype, dims=self._eval_dims(v.dims))
                    self.current_table.declare(sym)

        elif isinstance(d, DimensionStmt):
            for v in d.vars:
                sym = self.current_table.lookup_local(v.name)
                if sym:
                    sym.dims = self._eval_dims(v.dims)
                else:
                    # cria com tipo implícito
                    sym = Symbol(v.name, implicit_type(v.name), dims=self._eval_dims(v.dims))
                    self.current_table.declare(sym)

        elif isinstance(d, ParameterStmt):
            for name, expr in d.assignments:
                sym = self.current_table.lookup_local(name)
                if not sym:
                    sym = Symbol(name, implicit_type(name))
                    self.current_table.declare(sym)

    def _eval_dims(self, dims):
        if not dims:
            return None
        result = []
        for d in dims:
            if isinstance(d, tuple):
                # range: (low, high)
                result.append(d)
            elif isinstance(d, IntLit):
                result.append(d.value)
            else:
                result.append('?')
        return result

    def analyze_stmt(self, s):
        if isinstance(s, LabeledStmt):
            self.analyze_stmt(s.stmt)

        elif isinstance(s, AssignStmt):
            t_val = self.type_of(s.value)
            # Resolve lvalue
            if isinstance(s.target, Var):
                sym = self._get_or_implicit(s.target.name)
                t_lv = sym.stype
            elif isinstance(s.target, ArrayRef):
                sym = self.current_table.lookup(s.target.name)
                if not sym:
                    self.error(f"Array '{s.target.name}' não declarado")
                    return
                if not sym.dims:
                    self.error(f"'{s.target.name}' usado como array mas não tem dimensões")
                t_lv = sym.stype
            else:
                t_lv = 'REAL'

            # Aviso de coerção
            if t_val and t_lv and t_val != t_lv:
                if not ({t_val, t_lv} <= {'INTEGER', 'REAL', 'DOUBLE PRECISION'}):
                    self.warning(f"Atribuição de {t_val} a {t_lv} pode perder informação")

        elif isinstance(s, DoStmt):
            self.referenced_labels.add(s.label)
            # Verifica variável de controlo
            self._get_or_implicit(s.var)
            t_start = self.type_of(s.start)
            t_stop  = self.type_of(s.stop)
            if t_start not in ('INTEGER', 'REAL', None) or t_stop not in ('INTEGER', 'REAL', None):
                self.error(f"Variáveis do DO devem ser numéricas")
            for stmt in s.body:
                self.analyze_stmt(stmt)

        elif isinstance(s, IfThenStmt):
            self.type_of(s.cond)
            for stmt in s.then_stmts:
                self.analyze_stmt(stmt)
            for cond, body in s.elseif_clauses:
                self.type_of(cond)
                for stmt in body:
                    self.analyze_stmt(stmt)
            if s.else_stmts:
                for stmt in s.else_stmts:
                    self.analyze_stmt(stmt)

        elif isinstance(s, LogicalIfStmt):
            self.type_of(s.cond)
            self.analyze_stmt(s.stmt)

        elif isinstance(s, GotoStmt):
            self.referenced_labels.add(s.label)

        elif isinstance(s, CallStmt):
            sym = self.global_table.lookup(s.name)
            if not sym:
                self.warning(f"Subprograma '{s.name}' não declarado (pode ser externo)")

        elif isinstance(s, PrintStmt):
            for item in s.items:
                self.type_of(item)

        elif isinstance(s, ReadStmt):
            for item in s.items:
                if isinstance(item, Var):
                    self._get_or_implicit(item.name)
                elif isinstance(item, ArrayRef):
                    sym = self.current_table.lookup(item.name)
                    if not sym:
                        self.error(f"Array '{item.name}' não declarado em READ")

    def _get_or_implicit(self, name: str) -> Symbol:
        sym = self.current_table.lookup(name)
        if not sym:
            if self.implicit_none:
                self.error(f"Variável '{name}' não declarada (IMPLICIT NONE activo)")
                sym = Symbol(name, 'INTEGER')
            else:
                sym = Symbol(name, implicit_type(name))
                self.current_table.declare(sym)
                self.warning(f"Variável '{name}' declarada implicitamente como {sym.stype}")
        return sym

    def type_of(self, expr) -> str:
        if expr is None:
            return None
        if isinstance(expr, IntLit):
            return 'INTEGER'
        if isinstance(expr, RealLit):
            return 'REAL'
        if isinstance(expr, LogicalLit):
            return 'LOGICAL'
        if isinstance(expr, StringLit):
            return 'CHARACTER'
        if isinstance(expr, Var):
            sym = self._get_or_implicit(expr.name)
            return sym.stype
        if isinstance(expr, ArrayRef):
            sym = self.current_table.lookup(expr.name)
            if sym:
                return sym.stype
            return implicit_type(expr.name)
        if isinstance(expr, FuncCall):
            # Pode ser ArrayRef — resolve
            sym = self.current_table.lookup(expr.name)
            if sym and sym.dims:
                # É um array ref
                node = expr
                node.__class__ = ArrayRef
                return sym.stype
            # Intrínseca
            if expr.name in INTRINSICS:
                return INTRINSICS[expr.name]
            # Função declarada
            gsym = self.global_table.lookup(expr.name)
            if gsym and gsym.is_func:
                return gsym.stype
            self.warning(f"Função '{expr.name}' desconhecida, assume-se REAL")
            return 'REAL'
        if isinstance(expr, BinOp):
            lt = self.type_of(expr.left)
            rt = self.type_of(expr.right)
            op = expr.op
            # Operadores relacionais e lógicos devolvem LOGICAL
            if op in ('.EQ.', '.NE.', '.LT.', '.LE.', '.GT.', '.GE.',
                      '==', '/=', '<', '<=', '>', '>=',
                      '.AND.', '.OR.', '.EQV.', '.NEQV.'):
                return 'LOGICAL'
            # Promoção numérica
            if 'DOUBLE PRECISION' in (lt, rt):
                return 'DOUBLE PRECISION'
            if 'REAL' in (lt, rt):
                return 'REAL'
            return lt or rt or 'INTEGER'
        if isinstance(expr, UnaryOp):
            return self.type_of(expr.operand)
        return None

    def report(self):
        for w in self.warnings:
            print(w)
        for e in self.errors:
            print(e)
        if not self.errors:
            print("[SEMÂNTICO] Análise sem erros.")
        return self.errors, self.warnings


def analyze(ast):
    sa = SemanticAnalyzer()
    ok = sa.analyze(ast)
    sa.report()
    return sa, ok
