import ply.lex as lex

# ANÁLISE LÉXICA - FORTRAN 77



# ------------- PALAVRAS RESERVADAS --------------------------

reserved = {
    'PROGRAM'   : 'PROGRAM',
    'END'       : 'END',
    'INTEGER'   : 'INTEGER',
    'REAL'      : 'REAL',
    'DOUBLE'    : 'DOUBLE',
    'PRECISION' : 'PRECISION',
    'COMPLEX'   : 'COMPLEX',
    'LOGICAL'   : 'LOGICAL',
    'CHARACTER' : 'CHARACTER',
    'PRINT'     : 'PRINT',
    'READ'      : 'READ',
    'WRITE'     : 'WRITE',
    'DO'        : 'DO',
    'CONTINUE'  : 'CONTINUE',
    'IF'        : 'IF',
    'THEN'      : 'THEN',
    'ELSE'      : 'ELSE',
    'ENDIF'     : 'ENDIF',
    'GOTO'      : 'GOTO',
    'STOP'      : 'STOP',
    'RETURN'    : 'RETURN',
    'CALL'      : 'CALL',
    'FUNCTION'  : 'FUNCTION',
    'SUBROUTINE': 'SUBROUTINE',
    'COMMON'    : 'COMMON',
    'DIMENSION' : 'DIMENSION',
    'DATA'      : 'DATA',
    'FORMAT'    : 'FORMAT',
    'PARAMETER' : 'PARAMETER',
    'IMPLICIT'  : 'IMPLICIT',
    'NONE'      : 'NONE',
}


# ---------LISTA DE TODOS OS TOKENS---------------------------

tokens = list(reserved.values()) + [
    # Literais
    'DOUBLE_PRECISION_LIT',   # 1.0D0
    'REAL_EXP_LIT',           # 1.0E10
    'REAL_LIT',               # 3.14
    'INTEGER_LIT',            # 42
    'LOGICAL_TRUE',           # .TRUE.
    'LOGICAL_FALSE',          # .FALSE.
    'STRING_LIT',             # 'HELLO'
    'HOLLERITH_LIT',          # 5HHELLO

    # Operadores aritméticos
    'POW',       # **
    'PLUS',      # +
    'MINUS',     # -
    'TIMES',     # *
    'DIVIDE',    # /
    'CONCAT',    # //

    # Operadores relacionais (simbólicos - extensão comum)
    'EQ_SYM',    # ==
    'NE_SYM',    # /=
    'LE_SYM',    # <=
    'GE_SYM',    # >=
    'LT_SYM',    # <
    'GT_SYM',    # >

    # Operadores relacionais (estilo Fortran)
    'OP_EQ',     # .EQ.
    'OP_NE',     # .NE.
    'OP_LT',     # .LT.
    'OP_GT',     # .GT.
    'OP_LE',     # .LE.
    'OP_GE',     # .GE.

    # Operadores lógicos
    'OP_AND',    # .AND.
    'OP_OR',     # .OR.
    'OP_NOT',    # .NOT.
    'OP_EQV',    # .EQV.
    'OP_NEQV',   # .NEQV.

    # Atribuição
    'ASSIGN',    # =

    # Pontuação
    'LPAREN',    # (
    'RPAREN',    # )
    'COMMA',     # ,
    'DOT',       # .
    'COLON',     # :
    'STAR',      # * (formato)

    # Identificadores
    'ID',

    # Rótulos (labels)
    'LABEL',
]

# ------------------------------------------------------------
# 3. REGRAS DE TOKENS (ordem: mais específico → mais geral)
# ------------------------------------------------------------

# --- Operadores multi-caractere (definidos como funções para ter prioridade) ---

def t_DOUBLE_PRECISION_LIT(t):
    r'[+-]?(\d+\.?\d*|\.\d+)[Dd][+-]?\d+'
    return t

def t_REAL_EXP_LIT(t):
    r'[+-]?(\d+\.?\d*|\.\d+)[Ee][+-]?\d+'
    return t

def t_REAL_LIT(t):
    r'[+-]?(\d+\.\d*|\.\d+)'
    return t

def t_HOLLERITH_LIT(t):
    r'\d+[Hh](.+)'
    # Valida se o número de caracteres bate com o prefixo
    raw = t.value
    n   = int(raw.split('H')[0].split('h')[0])
    sep = 'H' if 'H' in raw else 'h'
    content = raw.split(sep, 1)[1]
    t.value = (n, content[:n])
    return t

def t_INTEGER_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

# --- Literais lógicos e operadores com pontos ---
def t_LOGICAL_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_LOGICAL_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

def t_OP_EQ(t):   r'\.EQ\.';   return t
def t_OP_NE(t):   r'\.NE\.';   return t
def t_OP_LE(t):   r'\.LE\.';   return t
def t_OP_GE(t):   r'\.GE\.';   return t
def t_OP_LT(t):   r'\.LT\.';   return t
def t_OP_GT(t):   r'\.GT\.';   return t
def t_OP_AND(t):  r'\.AND\.';  return t
def t_OP_OR(t):   r'\.OR\.';   return t
def t_OP_NOT(t):  r'\.NOT\.';  return t
def t_OP_EQV(t):  r'\.EQV\.';  return t
def t_OP_NEQV(t): r'\.NEQV\.'; return t

# --- String entre apóstrofos ---
def t_STRING_LIT(t):
    r"'([^']|'')*'"
    # Remove os apóstrofos externos e substitui '' por '
    t.value = t.value[1:-1].replace("''", "'")
    return t

# --- Operadores simbólicos multi-caractere ---
t_POW     = r'\*\*'
t_CONCAT  = r'//'
t_EQ_SYM  = r'=='
t_NE_SYM  = r'/='
t_LE_SYM  = r'<='
t_GE_SYM  = r'>='
t_LT_SYM  = r'<'
t_GT_SYM  = r'>'

# --- Operadores simples ---
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_ASSIGN  = r'='

# --- Pontuação ---
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COMMA   = r','
t_DOT     = r'\.'
t_COLON   = r':'
t_STAR    = r'\*'

# --- Identificadores e palavras reservadas ---
def t_ID(t):
    r'[A-Za-z][A-Za-z0-9]*'
    t.type = reserved.get(t.value.upper(), 'ID')
    return t

# --- Comentários (linha começa com C ou *) ---
def t_COMMENT(t):
    r'(^[Cc\*].*)|(![^\n]*)'
    pass  # ignorar comentários

# --- Rótulos numéricos no início da linha ---
def t_LABEL(t):
    r"[0-9]{1,5}"
    t.value = int(t.value)
    return t

# --- Ignorar espaços e tabs (Fortran 77 ignora espaços fora de strings) ---
t_ignore = ' \t'

# --- Nova linha ---
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# --- Erros ---
def t_error(t):
    print(f"  [ERRO LÉXICO] Caractere inválido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)


# ============================================================
# 4. CONSTRUÇÃO DO LEXER
# ============================================================
lexer = lex.lex()


# ============================================================
# 5. FUNÇÃO DE TESTE
# ============================================================
def analisar(codigo: str):
    lexer.input(codigo)
    lexer.lineno = 1
    print(f"\n{'='*60}")
    print(f"{'TOKEN':<22} {'TIPO':<22} {'LINHA'}")
    print(f"{'='*60}")
    for tok in lexer:
        print(f"{str(tok.value):<22} {tok.type:<22} {tok.lineno}")
    print(f"{'='*60}\n")


# ============================================================
# 6. PROGRAMA DE TESTE - FATORIAL
# ============================================================
if __name__ == '__main__':
    programa_fatorial = """\
PROGRAM SOMAARR
INTEGER NUMS(5)
INTEGER I, SOMA
SOMA = 0
PRINT *, 'Introduza 5 numeros inteiros:'
DO 30 I = 1, 5
READ *, NUMS(I)
SOMA = SOMA + NUMS(I)
30 CONTINUE
PRINT *, 'A soma dos numeros e: ', SOMA
END
"""
    print("Código Fortran 77 a analisar:")
    print(programa_fatorial)
    analisar(programa_fatorial)
