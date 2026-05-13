"""
codegen.py
Geração de código para a VM de pilha a partir da AST.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.ast_nodes import *
from vm.vm import Instr

# ============================================================
# GERADOR DE CÓDIGO
# ============================================================

class CodeGen:
    def __init__(self, sa=None):
        self.code      = []
        self.label_cnt = 0
        self.sa        = sa   # analisador semântico (para tabela de símbolos)
        self.current_unit = None
        self.param_map = {}   # nome -> índice, para subprogramas
        self.do_stack  = []   # stack de (end_label) para DO loops

    # -------- helpers --------

    def emit(self, op, *args):
        self.code.append(Instr(op, *args))

    def new_label(self, prefix='L'):
        self.label_cnt += 1
        return f"{prefix}_{self.label_cnt}"

    def emit_label(self, name):
        self.emit('LABEL', name)

    # -------- programa --------

    def generate(self, ast: Program):
        # Primeiro passa: gera funções/subroutines (para serem saltadas)
        main_unit = None
        sub_units = []
        for unit in ast.units:
            if unit.kind == 'PROGRAM':
                main_unit = unit
            else:
                sub_units.append(unit)

        # Gera subprogramas primeiro (ficam no início mas envoltos em FUNC/ENDFUNC)
        for unit in sub_units:
            self.gen_subprogram(unit)

        # Gera programa principal
        if main_unit:
            self.gen_unit(main_unit)
        elif sub_units:
            pass  # Apenas subprogramas

        self.emit('HALT')
        return self.code

    def gen_unit(self, unit: ProgramUnit):
        self.current_unit = unit
        self.param_map = {}

        # Inicializa arrays (reserva espaço simbólico)
        if self.sa:
            tbl = self.sa.current_table
            # Tenta encontrar o scope correcto
            for name, sym in self.sa.global_table.symbols.items():
                pass  # global symbols

        for decl in unit.decls:
            self.gen_decl(decl)

        for stmt in unit.stmts:
            self.gen_stmt(stmt)

    def gen_subprogram(self, unit: ProgramUnit):
        self.emit('FUNC', unit.name)
        old_unit = self.current_unit
        self.current_unit = unit

        # Mapeia parâmetros formais para índices
        self.param_map = {p: i for i, p in enumerate(unit.params)}

        # STORE dos argumentos nas variáveis locais
        for i, p in enumerate(unit.params):
            self.emit('LOADPARAM', i)
            self.emit('STORE', p)

        for decl in unit.decls:
            self.gen_decl(decl)

        for stmt in unit.stmts:
            self.gen_stmt(stmt)

        # Para FUNCTION, carrega o valor de retorno
        if unit.kind == 'FUNCTION':
            self.emit('LOAD', unit.name)

        self.emit('RET')
        self.emit('ENDFUNC')
        self.current_unit = old_unit
        self.param_map = {}

    def gen_decl(self, decl):
        if isinstance(decl, Declaration):
            for v in decl.vars:
                if v.dims:
                    # Inicializa array com zeros
                    # (a VM cria sob-demanda, mas inicializamos explicitamente)
                    pass
        elif isinstance(decl, ParameterStmt):
            for name, expr in decl.assignments:
                self.gen_expr(expr)
                self.emit('STORE', name)

    # -------- statements --------

    def gen_stmt(self, stmt):
        if isinstance(stmt, LabeledStmt):
            self.emit_label(f'LBL_{stmt.label}')
            self.gen_stmt(stmt.stmt)

        elif isinstance(stmt, AssignStmt):
            self.gen_assign(stmt)

        elif isinstance(stmt, PrintStmt):
            self.gen_print(stmt)

        elif isinstance(stmt, ReadStmt):
            self.gen_read(stmt)

        elif isinstance(stmt, WriteStmt):
            self.gen_write(stmt)

        elif isinstance(stmt, IfThenStmt):
            self.gen_if_then(stmt)

        elif isinstance(stmt, LogicalIfStmt):
            self.gen_logical_if(stmt)

        elif isinstance(stmt, DoStmt):
            self.gen_do(stmt)

        elif isinstance(stmt, ContinueStmt):
            self.emit('NOP')

        elif isinstance(stmt, GotoStmt):
            self.emit('JMP', f'LBL_{stmt.label}')

        elif isinstance(stmt, StopStmt):
            if stmt.msg:
                self.emit('PUSH', stmt.msg)
                self.emit('PRINT')
                self.emit('PRINTLN')
            self.emit('HALT')

        elif isinstance(stmt, ReturnStmt):
            if self.current_unit and self.current_unit.kind == 'FUNCTION':
                self.emit('LOAD', self.current_unit.name)
            self.emit('RET')

        elif isinstance(stmt, CallStmt):
            self.gen_call_stmt(stmt)

        elif isinstance(stmt, FormatStmt):
            self.emit('NOP')  # FORMAT é tratado estaticamente

    def gen_assign(self, stmt: AssignStmt):
        target = stmt.target
        if isinstance(target, Var):
            self.gen_expr(stmt.value)
            self.emit('STORE', target.name)
        elif isinstance(target, (ArrayRef, FuncCall)):
            # Arrays e chamadas de função têm sintaxe idêntica no parser
            name = target.name
            args = (target.indices if isinstance(target, ArrayRef) and hasattr(target,'indices')
                    else target.args)
            idx_expr = args[0] if args else IntLit(1)
            self.gen_expr(idx_expr)    # índice
            self.gen_expr(stmt.value)  # valor
            self.emit('STOREARR', name)

    def gen_array_index(self, ref):
        """Gera código para calcular índice linear de um array."""
        # Para arrays 1D simples:
        if isinstance(ref, (ArrayRef, FuncCall)):
            self.gen_expr(ref.indices[0] if hasattr(ref, 'indices') else ref.args[0])

    def gen_print(self, stmt: PrintStmt):
        for item in stmt.items:
            self.gen_expr(item)
            self.emit('PRINT')
            self.emit('PUSH', ' ')
            self.emit('PRINT')
        self.emit('PRINTLN')

    def gen_read(self, stmt: ReadStmt):
        for item in stmt.items:
            if isinstance(item, Var):
                self.emit('READ', item.name)
            elif isinstance(item, (ArrayRef, FuncCall)):
                name = item.name
                idx_expr = (item.indices[0] if hasattr(item, 'indices') and item.indices
                            else item.args[0] if hasattr(item, 'args') and item.args
                            else IntLit(1))
                self.gen_expr(idx_expr)
                self.emit('READARR', name)

    def gen_write(self, stmt: WriteStmt):
        for item in stmt.items:
            self.gen_expr(item)
            self.emit('PRINT')
        self.emit('PRINTLN')

    def gen_if_then(self, stmt: IfThenStmt):
        end_label    = self.new_label('ENDIF')
        next_label   = self.new_label('ELSE')

        # Condição principal
        self.gen_expr(stmt.cond)
        self.emit('JZ', next_label)

        for s in stmt.then_stmts:
            self.gen_stmt(s)
        self.emit('JMP', end_label)
        self.emit_label(next_label)

        # ELSEIF clauses
        for cond, body in stmt.elseif_clauses:
            next_elseif = self.new_label('ELSEIF')
            self.gen_expr(cond)
            self.emit('JZ', next_elseif)
            for s in body:
                self.gen_stmt(s)
            self.emit('JMP', end_label)
            self.emit_label(next_elseif)

        # ELSE
        if stmt.else_stmts:
            for s in stmt.else_stmts:
                self.gen_stmt(s)

        self.emit_label(end_label)

    def gen_logical_if(self, stmt: LogicalIfStmt):
        skip_label = self.new_label('IF_SKIP')
        self.gen_expr(stmt.cond)
        self.emit('JZ', skip_label)
        self.gen_stmt(stmt.stmt)
        self.emit_label(skip_label)

    def gen_do(self, stmt: DoStmt):
        """
        DO label var = start, stop [, step]
        Gera:
          STORE var (start)
          LOOP_label:
            LOAD var; PUSH stop; LE; JZ end
            body
            LOAD var; PUSH step; ADD; STORE var
            JMP LOOP_label
          LBL_label: (CONTINUE)
        """
        loop_label = self.new_label('DO_LOOP')
        end_label  = f'LBL_{stmt.label}'

        # var = start
        self.gen_expr(stmt.start)
        self.emit('STORE', stmt.var)

        self.emit_label(loop_label)

        # var <= stop ?
        self.emit('LOAD', stmt.var)
        self.gen_expr(stmt.stop)
        self.emit('LE')
        self.emit('JZ', end_label)

        # corpo
        self.do_stack.append(end_label)
        for s in stmt.body:
            self.gen_stmt(s)
        self.do_stack.pop()

        # var = var + step
        self.emit('LOAD', stmt.var)
        if stmt.step:
            self.gen_expr(stmt.step)
        else:
            self.emit('PUSH', 1)
        self.emit('ADD')
        self.emit('STORE', stmt.var)

        self.emit('JMP', loop_label)

        # label do CONTINUE
        self.emit_label(end_label)

    def gen_call_stmt(self, stmt: CallStmt):
        for arg in stmt.args:
            self.gen_expr(arg)
        self.emit('CALL', stmt.name, len(stmt.args))
        # Descarta valor de retorno (é statement, não expressão)
        if stmt.args:
            pass  # subroutines não empurram retorno

    # -------- expressões --------

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
            idx = expr.indices[0] if hasattr(expr,'indices') and expr.indices else expr.args[0]
            self.gen_expr(idx)
            self.emit('LOADARR', expr.name)

        elif isinstance(expr, FuncCall):
            name = expr.name
            args = expr.args if hasattr(expr, 'args') else []

            # Pode ser array ref ou função intrínseca ou função do utilizador
            # Intrínsecas especiais
            if name == 'MOD':
                self.gen_expr(args[0])
                self.gen_expr(args[1])
                self.emit('IMOD')
            elif name == 'ABS':
                self.gen_expr(args[0])
                self.emit('ABS_FUNC')
            elif name == 'SQRT':
                self.gen_expr(args[0])
                self.emit('SQRT_FUNC')
            elif name == 'INT':
                self.gen_expr(args[0])
                self.emit('INTCAST')
            elif name in ('FLOAT', 'REAL', 'DBLE'):
                self.gen_expr(args[0])
                self.emit('FLOATCAST')
            elif name == 'MAX':
                self.gen_expr(args[0])
                for a in args[1:]:
                    self.gen_expr(a)
                    self.emit('CALL', 'MAX', 2)
            elif name == 'MIN':
                self.gen_expr(args[0])
                for a in args[1:]:
                    self.gen_expr(a)
                    self.emit('CALL', 'MIN', 2)
            else:
                # Pode ser array ref — tenta como array, senão chama função
                for a in args:
                    self.gen_expr(a)
                if len(args) == 1:
                    # Ambíguo: pode ser array ou função
                    # Emite LOADARR tentativo; a VM resolve
                    # Para simplificar: emite como CALL e a VM trata
                    pass
                self.emit('CALL', name, len(args))

        elif isinstance(expr, BinOp):
            self.gen_binop(expr)

        elif isinstance(expr, UnaryOp):
            self.gen_expr(expr.operand)
            if expr.op == '-':
                self.emit('UMINUS')
            elif expr.op == '.NOT.':
                self.emit('NOT')

    def gen_binop(self, expr: BinOp):
        op = expr.op

        # Curto-circuito para AND/OR
        if op == '.AND.':
            self.gen_expr(expr.left)
            self.gen_expr(expr.right)
            self.emit('AND')
            return
        if op == '.OR.':
            self.gen_expr(expr.left)
            self.gen_expr(expr.right)
            self.emit('OR')
            return

        self.gen_expr(expr.left)
        self.gen_expr(expr.right)

        op_map = {
            '+'     : 'ADD',
            '-'     : 'SUB',
            '*'     : 'MUL',
            '/'     : 'DIV',
            '**'    : 'POW',
            '//'    : 'CONCAT',
            '.EQ.'  : 'EQ',  '.NE.': 'NE',
            '.LT.'  : 'LT',  '.LE.': 'LE',
            '.GT.'  : 'GT',  '.GE.': 'GE',
            '=='    : 'EQ',  '/='  : 'NE',
            '<'     : 'LT',  '<='  : 'LE',
            '>'     : 'GT',  '>='  : 'GE',
            '.EQV.' : 'EQ',
            '.NEQV.': 'NE',
        }
        vm_op = op_map.get(op)
        if vm_op:
            self.emit(vm_op)
        else:
            print(f"[CODEGEN] Operador desconhecido: {op}")


# ============================================================
# PRETTY PRINT DO CÓDIGO GERADO
# ============================================================

def print_code(code):
    print(f"\n{'='*50}")
    print(f"{'#':<5} {'Instrução'}")
    print(f"{'='*50}")
    for i, instr in enumerate(code):
        print(f"{i:<5} {instr}")
    print(f"{'='*50}\n")


# ============================================================
# SERIALIZAR / DESERIALIZAR CÓDIGO VM
# ============================================================

def code_to_text(code):
    """Serializa lista de Instr para texto."""
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
            # Tenta avaliar os argumentos
            raw_args = parts[1]
            args = []
            for tok in raw_args.split():
                try:
                    args.append(pyast.literal_eval(tok))
                except Exception:
                    args.append(tok)
            instrs.append(Instr(op, *args))
    return instrs


def generate(ast, sa=None):
    cg = CodeGen(sa=sa)
    code = cg.generate(ast)
    return code
