"""
stmt_gen.py
Geração de código VM para statements e subprogramas.
Mixin utilizado pelo CodeGen principal.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.ast_nodes import (
    LabeledStmt, AssignStmt, PrintStmt, ReadStmt, WriteStmt,
    IfThenStmt, LogicalIfStmt, DoStmt, ContinueStmt,
    GotoStmt, StopStmt, ReturnStmt, CallStmt, FormatStmt,
    Var, ArrayRef, FuncCall, IntLit,
    ProgramUnit,
)


class StmtGen:
    """Mixin com métodos de geração de código para statements e subprogramas."""

    # --------------------------------------------------------
    # Despacho de statements
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Atribuição
    # --------------------------------------------------------

    def gen_assign(self, stmt: AssignStmt):
        target = stmt.target
        if isinstance(target, Var):
            self.gen_expr(stmt.value)
            self.emit('STORE', target.name)
        elif isinstance(target, (ArrayRef, FuncCall)):
            name = target.name
            args = (target.indices if isinstance(target, ArrayRef) and hasattr(target, 'indices')
                    else target.args)
            idx_expr = args[0] if args else IntLit(1)
            self.gen_expr(idx_expr)
            self.gen_expr(stmt.value)
            self.emit('STOREARR', name)

    # --------------------------------------------------------
    # I/O
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Estruturas de controlo
    # --------------------------------------------------------

    def gen_if_then(self, stmt: IfThenStmt):
        end_label  = self.new_label('ENDIF')
        next_label = self.new_label('ELSE')

        self.gen_expr(stmt.cond)
        self.emit('JZ', next_label)

        for s in stmt.then_stmts:
            self.gen_stmt(s)
        self.emit('JMP', end_label)
        self.emit_label(next_label)

        for cond, body in stmt.elseif_clauses:
            next_elseif = self.new_label('ELSEIF')
            self.gen_expr(cond)
            self.emit('JZ', next_elseif)
            for s in body:
                self.gen_stmt(s)
            self.emit('JMP', end_label)
            self.emit_label(next_elseif)

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
          var = start
          LOOP: if var > stop → JMP end
          body
          var = var + step
          JMP LOOP
          LBL_label:
        """
        loop_label = self.new_label('DO_LOOP')
        end_label  = f'LBL_{stmt.label}'

        self.gen_expr(stmt.start)
        self.emit('STORE', stmt.var)

        self.emit_label(loop_label)

        self.emit('LOAD', stmt.var)
        self.gen_expr(stmt.stop)
        self.emit('LE')
        self.emit('JZ', end_label)

        self.do_stack.append(end_label)
        for s in stmt.body:
            self.gen_stmt(s)
        self.do_stack.pop()

        self.emit('LOAD', stmt.var)
        if stmt.step:
            self.gen_expr(stmt.step)
        else:
            self.emit('PUSH', 1)
        self.emit('ADD')
        self.emit('STORE', stmt.var)

        self.emit('JMP', loop_label)
        self.emit_label(end_label)

    # --------------------------------------------------------
    # Subprogramas
    # --------------------------------------------------------

    def gen_subprogram(self, unit: ProgramUnit):
        self.emit('FUNC', unit.name)
        old_unit = self.current_unit
        self.current_unit = unit

        self.param_map = {p: i for i, p in enumerate(unit.params)}

        for i, p in enumerate(unit.params):
            self.emit('LOADPARAM', i)
            self.emit('STORE', p)

        for decl in unit.decls:
            self.gen_decl(decl)

        for stmt in unit.stmts:
            self.gen_stmt(stmt)

        if unit.kind == 'FUNCTION':
            self.emit('LOAD', unit.name)

        self.emit('RET')
        self.emit('ENDFUNC')
        self.current_unit = old_unit
        self.param_map = {}

    def gen_call_stmt(self, stmt: CallStmt):
        for arg in stmt.args:
            self.gen_expr(arg)
        self.emit('CALL', stmt.name, len(stmt.args))
