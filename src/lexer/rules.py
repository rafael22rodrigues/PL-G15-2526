"""
rules.py
Regras de tokenização PLY para Fortran 77.
Importa reserved e tokens de tokens.py para que ply.lex os encontre
no módulo correcto quando chamado com module=rules.
"""

from lexer.tokens import reserved, tokens  # noqa: F401  (ply.lex precisa de tokens aqui)

# ============================================================
# LITERAIS NUMÉRICOS  (funções = maior prioridade que strings)
# ============================================================

def t_DOUBLE_PRECISION_LIT(t):
    r'(\d+\.?\d*|\.\d+)[Dd][+-]?\d+'
    t.value = float(t.value.replace('D', 'E').replace('d', 'e'))
    return t

def t_REAL_EXP_LIT(t):
    r'(\d+\.?\d*|\.\d+)[Ee][+-]?\d+'
    t.value = float(t.value)
    return t

def t_REAL_LIT(t):
    r'\d+\.\d*|\.\d+'
    t.value = float(t.value)
    return t

def t_INTEGER_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

# ============================================================
# LITERAIS LÓGICOS
# ============================================================

def t_LOGICAL_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_LOGICAL_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

# ============================================================
# OPERADORES COM PONTOS  (mais longo primeiro)
# ============================================================

def t_OP_NEQV(t): r'\.NEQV\.'; return t
def t_OP_EQV(t):  r'\.EQV\.';  return t
def t_OP_AND(t):  r'\.AND\.';  return t
def t_OP_OR(t):   r'\.OR\.';   return t
def t_OP_NOT(t):  r'\.NOT\.';  return t
def t_OP_EQ(t):   r'\.EQ\.';   return t
def t_OP_NE(t):   r'\.NE\.';   return t
def t_OP_LE(t):   r'\.LE\.';   return t
def t_OP_GE(t):   r'\.GE\.';   return t
def t_OP_LT(t):   r'\.LT\.';   return t
def t_OP_GT(t):   r'\.GT\.';   return t

# ============================================================
# STRING LITERAL
# ============================================================

def t_STRING_LIT(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t

# ============================================================
# OPERADORES MULTI-CHAR  (strings têm prioridade por comprimento)
# ============================================================

t_POW    = r'\*\*'
t_CONCAT = r'//'
t_EQ_SYM = r'=='
t_NE_SYM = r'/='
t_LE_SYM = r'<='
t_GE_SYM = r'>='
t_LT_SYM = r'<'
t_GT_SYM = r'>'

# ============================================================
# OPERADORES SIMPLES
# ============================================================

t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='

# ============================================================
# PONTUAÇÃO
# ============================================================

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA  = r','
t_COLON  = r':'

# ============================================================
# IDENTIFICADORES E PALAVRAS RESERVADAS
# ============================================================

def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.type  = reserved.get(t.value.upper(), 'ID')
    t.value = t.value.upper()
    return t

# ============================================================
# NEWLINE  (separador de statements)
# ============================================================

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# ============================================================
# IGNORAR ESPAÇOS E TABS
# ============================================================

t_ignore = ' \t\r'

# ============================================================
# ERROS
# ============================================================

def t_error(t):
    print(f"  [ERRO LÉXICO] Caractere inválido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)
