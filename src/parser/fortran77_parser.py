"""
fortran77_parser.py  (v2)
Analisador Sintático para Fortran 77 usando ply.yacc.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ply.yacc as yacc
import ply.lex  as plex
import importlib

_lex_mod = importlib.import_module('lexer.fortran77_lexer')
tokens   = _lex_mod.tokens

from parser.ast_nodes import *

# ============================================================
# PRECEDÊNCIAS
# ============================================================
precedence = (
    ('left',  'OP_EQV', 'OP_NEQV'),
    ('left',  'OP_OR'),
    ('left',  'OP_AND'),
    ('right', 'OP_NOT'),
    ('nonassoc', 'OP_EQ', 'OP_NE', 'OP_LT', 'OP_LE', 'OP_GT', 'OP_GE',
                 'EQ_SYM', 'NE_SYM', 'LT_SYM', 'LE_SYM', 'GT_SYM', 'GE_SYM'),
    ('left',  'CONCAT'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'TIMES', 'DIVIDE'),
    ('right', 'UMINUS', 'UPLUS'),
    ('right', 'POW'),
)

# ============================================================
# PROGRAMA
# ============================================================

def p_program(p):
    """program : program_unit_list"""
    p[0] = Program(None, p[1])

def p_program_unit_list_multi(p):
    """program_unit_list : program_unit_list program_unit"""
    p[0] = p[1] + [p[2]]

def p_program_unit_list_single(p):
    """program_unit_list : program_unit"""
    p[0] = [p[1]]

def p_program_unit_program(p):
    """program_unit : PROGRAM ID newlines decl_list stmt_list END newlines"""
    p[0] = ProgramUnit('PROGRAM', p[2], [], p[4], p[5])

def p_program_unit_noname(p):
    """program_unit : decl_list stmt_list END newlines"""
    p[0] = ProgramUnit('PROGRAM', 'MAIN', [], p[1], p[2])

def p_program_unit_function_typed(p):
    """program_unit : type_spec FUNCTION ID LPAREN param_list RPAREN newlines decl_list stmt_list END newlines"""
    unit = ProgramUnit('FUNCTION', p[3], p[5], p[8], p[9])
    unit.return_type = p[1]
    p[0] = unit

def p_program_unit_function_untyped(p):
    """program_unit : FUNCTION ID LPAREN param_list RPAREN newlines decl_list stmt_list END newlines"""
    unit = ProgramUnit('FUNCTION', p[2], p[4], p[7], p[8])
    unit.return_type = None
    p[0] = unit

def p_program_unit_subroutine_params(p):
    """program_unit : SUBROUTINE ID LPAREN param_list RPAREN newlines decl_list stmt_list END newlines"""
    p[0] = ProgramUnit('SUBROUTINE', p[2], p[4], p[7], p[8])

def p_program_unit_subroutine_noparams(p):
    """program_unit : SUBROUTINE ID newlines decl_list stmt_list END newlines"""
    p[0] = ProgramUnit('SUBROUTINE', p[2], [], p[4], p[5])

def p_param_list_multi(p):
    """param_list : param_list COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_param_list_single(p):
    """param_list : ID"""
    p[0] = [p[1]]

def p_param_list_empty(p):
    """param_list : empty"""
    p[0] = []

def p_newlines_multi(p):
    """newlines : newlines NEWLINE"""

def p_newlines_single(p):
    """newlines : NEWLINE"""

# ============================================================
# DECLARAÇÕES
# ============================================================

def p_decl_list_multi(p):
    """decl_list : decl_list decl_stmt"""
    p[0] = p[1] + [p[2]]

def p_decl_list_empty(p):
    """decl_list : empty"""
    p[0] = []

def p_decl_implicit_none(p):
    """decl_stmt : IMPLICIT NONE newlines"""
    p[0] = ImplicitNone()

def p_decl_type(p):
    """decl_stmt : type_spec var_decl_list newlines"""
    p[0] = Declaration(p[1], p[2])

def p_decl_dimension(p):
    """decl_stmt : DIMENSION var_decl_list newlines"""
    p[0] = DimensionStmt(p[2])

def p_decl_parameter(p):
    """decl_stmt : PARAMETER LPAREN param_assign_list RPAREN newlines"""
    p[0] = ParameterStmt(p[3])

def p_decl_common_unnamed(p):
    """decl_stmt : COMMON id_list newlines"""
    p[0] = CommonStmt(None, p[2])

def p_decl_data(p):
    """decl_stmt : DATA data_list newlines"""
    p[0] = Declaration('DATA', p[2])

def p_data_list_multi(p):
    """data_list : data_list COMMA data_item"""
    p[0] = p[1] + [p[3]]

def p_data_list_single(p):
    """data_list : data_item"""
    p[0] = [p[1]]

def p_data_item(p):
    """data_item : id_list DIVIDE expr_list DIVIDE"""
    p[0] = (p[1], p[3])

def p_decl_common_named(p):
    """decl_stmt : COMMON DIVIDE ID DIVIDE id_list newlines"""
    p[0] = CommonStmt(p[3], p[5])

def p_param_assign_list_multi(p):
    """param_assign_list : param_assign_list COMMA param_assign"""
    p[0] = p[1] + [p[3]]

def p_param_assign_list_single(p):
    """param_assign_list : param_assign"""
    p[0] = [p[1]]

def p_param_assign(p):
    """param_assign : ID ASSIGN expr"""
    p[0] = (p[1], p[3])

def p_type_spec_single(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL
                 | COMPLEX
                 | CHARACTER"""
    p[0] = p[1]

def p_type_spec_double(p):
    """type_spec : DOUBLE PRECISION"""
    p[0] = 'DOUBLE PRECISION'

def p_var_decl_list_multi(p):
    """var_decl_list : var_decl_list COMMA var_decl"""
    p[0] = p[1] + [p[3]]

def p_var_decl_list_single(p):
    """var_decl_list : var_decl"""
    p[0] = [p[1]]

def p_var_decl_array(p):
    """var_decl : ID LPAREN dim_list RPAREN"""
    p[0] = VarDecl(p[1], dims=p[3])

def p_var_decl_char_len(p):
    """var_decl : ID TIMES INTEGER_LIT"""
    p[0] = VarDecl(p[1], length=p[3])

def p_var_decl_simple(p):
    """var_decl : ID"""
    p[0] = VarDecl(p[1])

def p_dim_list_multi(p):
    """dim_list : dim_list COMMA dim_spec"""
    p[0] = p[1] + [p[3]]

def p_dim_list_single(p):
    """dim_list : dim_spec"""
    p[0] = [p[1]]

def p_dim_spec_range(p):
    """dim_spec : expr COLON expr"""
    p[0] = (p[1], p[3])

def p_dim_spec_size(p):
    """dim_spec : expr"""
    p[0] = p[1]

def p_id_list_multi(p):
    """id_list : id_list COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_id_list_single(p):
    """id_list : ID"""
    p[0] = [p[1]]

# ============================================================
# STATEMENTS
# ============================================================

def p_stmt_list_multi(p):
    """stmt_list : stmt_list stmt"""
    p[0] = p[1] + [p[2]]

def p_stmt_list_empty(p):
    """stmt_list : empty"""
    p[0] = []

def p_stmt_labeled(p):
    """stmt : LABEL stmt_body newlines"""
    p[0] = LabeledStmt(p[1], p[2])

def p_stmt_unlabeled(p):
    """stmt : stmt_body newlines"""
    p[0] = p[1]

def p_stmt_body(p):
    """stmt_body : assign_stmt
                 | print_stmt
                 | read_stmt
                 | write_stmt
                 | if_then_stmt
                 | logical_if_stmt
                 | do_stmt
                 | continue_stmt
                 | goto_stmt
                 | stop_stmt
                 | return_stmt
                 | call_stmt
                 | format_stmt"""
    p[0] = p[1]

# --- Atribuição ---
def p_assign_stmt(p):
    """assign_stmt : lvalue ASSIGN expr"""
    p[0] = AssignStmt(p[1], p[3])

def p_lvalue_array(p):
    """lvalue : ID LPAREN expr_list RPAREN"""
    p[0] = ArrayRef(p[1], p[3])

def p_lvalue_var(p):
    """lvalue : ID"""
    p[0] = Var(p[1])

# --- PRINT ---
def p_print_star_items(p):
    """print_stmt : PRINT TIMES COMMA io_list
                  | PRINT STAR_FMT COMMA io_list"""
    p[0] = PrintStmt('*', p[4])

def p_print_star_empty(p):
    """print_stmt : PRINT TIMES
                  | PRINT STAR_FMT"""
    p[0] = PrintStmt('*', [])

def p_print_fmt_int(p):
    """print_stmt : PRINT INTEGER_LIT COMMA io_list"""
    p[0] = PrintStmt(p[2], p[4])

def p_print_fmt_str(p):
    """print_stmt : PRINT STRING_LIT COMMA io_list"""
    p[0] = PrintStmt(p[2], p[4])

# --- READ ---
def p_read_star_items(p):
    """read_stmt : READ TIMES COMMA io_list
                 | READ STAR_FMT COMMA io_list"""
    p[0] = ReadStmt('*', p[4])

def p_read_star_empty(p):
    """read_stmt : READ TIMES
                 | READ STAR_FMT"""
    p[0] = ReadStmt('*', [])

def p_read_fmt(p):
    """read_stmt : READ INTEGER_LIT COMMA io_list"""
    p[0] = ReadStmt(p[2], p[4])

# --- WRITE ---
def p_write_star(p):
    """write_stmt : WRITE LPAREN expr COMMA TIMES RPAREN io_list"""
    p[0] = WriteStmt(p[3], '*', p[7])

def p_write_fmt(p):
    """write_stmt : WRITE LPAREN expr COMMA expr RPAREN io_list"""
    p[0] = WriteStmt(p[3], p[5], p[7])

def p_io_list_multi(p):
    """io_list : io_list COMMA io_item"""
    p[0] = p[1] + [p[3]]

def p_io_list_single(p):
    """io_list : io_item"""
    p[0] = [p[1]]

def p_io_item(p):
    """io_item : expr"""
    p[0] = p[1]

# --- IF-THEN-ELSE ---
def p_if_then_stmt(p):
    """if_then_stmt : IF LPAREN expr RPAREN THEN newlines stmt_list elseif_list else_part ENDIF"""
    p[0] = IfThenStmt(p[3], p[7], p[8], p[9])

def p_elseif_list_multi(p):
    """elseif_list : elseif_list elseif_clause"""
    p[0] = p[1] + [p[2]]

def p_elseif_list_empty(p):
    """elseif_list : empty"""
    p[0] = []

def p_elseif_clause_keyword(p):
    """elseif_clause : ELSEIF LPAREN expr RPAREN THEN newlines stmt_list"""
    p[0] = (p[3], p[7])

def p_elseif_clause_two_words(p):
    """elseif_clause : ELSE IF LPAREN expr RPAREN THEN newlines stmt_list"""
    p[0] = (p[4], p[8])

def p_else_part_with(p):
    """else_part : ELSE newlines stmt_list"""
    p[0] = p[3]

def p_else_part_empty(p):
    """else_part : empty"""
    p[0] = None

# --- IF lógico (uma linha) ---
def p_logical_if_stmt(p):
    """logical_if_stmt : IF LPAREN expr RPAREN stmt_body"""
    p[0] = LogicalIfStmt(p[3], p[5])

# --- DO com e sem step ---
def p_do_stmt_step(p):
    """do_stmt : DO INTEGER_LIT ID ASSIGN expr COMMA expr COMMA expr newlines stmt_list LABEL CONTINUE"""
    p[0] = DoStmt(p[2], p[3], p[5], p[7], p[9], p[11])

def p_do_stmt_no_step(p):
    """do_stmt : DO INTEGER_LIT ID ASSIGN expr COMMA expr newlines stmt_list LABEL CONTINUE"""
    p[0] = DoStmt(p[2], p[3], p[5], p[7], None, p[9])

# --- CONTINUE ---
def p_continue_stmt(p):
    """continue_stmt : CONTINUE"""
    p[0] = ContinueStmt()

# --- GOTO ---
def p_goto_stmt(p):
    """goto_stmt : GOTO INTEGER_LIT"""
    p[0] = GotoStmt(p[2])

# --- STOP ---
def p_stop_plain(p):
    """stop_stmt : STOP"""
    p[0] = StopStmt()

def p_stop_msg(p):
    """stop_stmt : STOP STRING_LIT
                 | STOP INTEGER_LIT"""
    p[0] = StopStmt(p[2])

# --- RETURN ---
def p_return_stmt(p):
    """return_stmt : RETURN"""
    p[0] = ReturnStmt()

# --- CALL ---
def p_call_args(p):
    """call_stmt : CALL ID LPAREN expr_list RPAREN"""
    p[0] = CallStmt(p[2], p[4])

def p_call_noargs(p):
    """call_stmt : CALL ID"""
    p[0] = CallStmt(p[2], [])

# --- FORMAT ---
def p_format_stmt(p):
    """format_stmt : FORMAT LPAREN format_spec RPAREN"""
    p[0] = FormatStmt(p[3])

def p_format_spec_list(p):
    """format_spec : format_item_list"""
    p[0] = p[1]

def p_format_spec_empty(p):
    """format_spec : empty"""
    p[0] = ''

def p_format_item_list_multi(p):
    """format_item_list : format_item_list COMMA format_item"""
    p[0] = p[1] + ',' + p[3]

def p_format_item_list_single(p):
    """format_item_list : format_item"""
    p[0] = p[1]

def p_format_item_id(p):
    """format_item : ID"""
    p[0] = str(p[1])

def p_format_item_int_id(p):
    """format_item : INTEGER_LIT ID"""
    p[0] = str(p[1]) + str(p[2])

def p_format_item_star(p):
    """format_item : TIMES"""
    p[0] = '*'

# ============================================================
# EXPRESSÕES
# ============================================================

def p_expr_binop(p):
    """expr : expr PLUS    expr
            | expr MINUS   expr
            | expr TIMES   expr
            | expr DIVIDE  expr
            | expr POW     expr
            | expr CONCAT  expr
            | expr OP_EQ   expr
            | expr OP_NE   expr
            | expr OP_LT   expr
            | expr OP_LE   expr
            | expr OP_GT   expr
            | expr OP_GE   expr
            | expr EQ_SYM  expr
            | expr NE_SYM  expr
            | expr LT_SYM  expr
            | expr LE_SYM  expr
            | expr GT_SYM  expr
            | expr GE_SYM  expr
            | expr OP_AND  expr
            | expr OP_OR   expr
            | expr OP_EQV  expr
            | expr OP_NEQV expr"""
    p[0] = BinOp(p[2], p[1], p[3])

def p_expr_uminus(p):
    """expr : MINUS expr %prec UMINUS"""
    p[0] = UnaryOp('-', p[2])

def p_expr_uplus(p):
    """expr : PLUS expr %prec UPLUS"""
    p[0] = p[2]

def p_expr_not(p):
    """expr : OP_NOT expr"""
    p[0] = UnaryOp('.NOT.', p[2])

def p_expr_paren(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

def p_expr_call_or_array(p):
    """expr : ID LPAREN expr_list RPAREN"""
    p[0] = FuncCall(p[1], p[3])

def p_expr_sqrt(p):
    """expr : SQRT LPAREN expr_list RPAREN"""
    p[0] = FuncCall('SQRT', p[3])

def p_expr_float(p):
    """expr : FLOAT LPAREN expr_list RPAREN"""
    p[0] = FuncCall('FLOAT', p[3])

def p_expr_var(p):
    """expr : ID"""
    p[0] = Var(p[1])

def p_expr_int(p):
    """expr : INTEGER_LIT"""
    p[0] = IntLit(p[1])

def p_expr_real(p):
    """expr : REAL_LIT"""
    p[0] = RealLit(p[1])

def p_expr_real_exp(p):
    """expr : REAL_EXP_LIT"""
    p[0] = RealLit(p[1])

def p_expr_double(p):
    """expr : DOUBLE_PRECISION_LIT"""
    p[0] = RealLit(p[1])

def p_expr_true(p):
    """expr : LOGICAL_TRUE"""
    p[0] = LogicalLit(True)

def p_expr_false(p):
    """expr : LOGICAL_FALSE"""
    p[0] = LogicalLit(False)

def p_expr_str(p):
    """expr : STRING_LIT"""
    p[0] = StringLit(p[1])

def p_expr_list_multi(p):
    """expr_list : expr_list COMMA expr"""
    p[0] = p[1] + [p[3]]

def p_expr_list_single(p):
    """expr_list : expr"""
    p[0] = [p[1]]

def p_empty(p):
    """empty :"""
    p[0] = []

# ============================================================
# ERROS
# ============================================================
def p_error(p):
    if p:
        print(f"  [ERRO SINTÁTICO] Token inesperado '{p.value}' ({p.type}) linha {p.lineno}")
    else:
        print("  [ERRO SINTÁTICO] Fim de ficheiro inesperado")

# ============================================================
# PARSER
# ============================================================
parser = yacc.yacc(debug=False, write_tables=False)

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

            inner = inner_lex.lex(module=_lex_mod)
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
