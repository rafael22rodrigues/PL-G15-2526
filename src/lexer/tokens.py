"""
tokens.py
Palavras reservadas e lista de tokens do Fortran 77.
"""

# ============================================================
# PALAVRAS RESERVADAS
# ============================================================

reserved = {
    'PROGRAM'    : 'PROGRAM',
    'END'        : 'END',
    'INTEGER'    : 'INTEGER',
    'REAL'       : 'REAL',
    'DOUBLE'     : 'DOUBLE',
    'PRECISION'  : 'PRECISION',
    'COMPLEX'    : 'COMPLEX',
    'LOGICAL'    : 'LOGICAL',
    'CHARACTER'  : 'CHARACTER',
    'PRINT'      : 'PRINT',
    'READ'       : 'READ',
    'WRITE'      : 'WRITE',
    'DO'         : 'DO',
    'CONTINUE'   : 'CONTINUE',
    'IF'         : 'IF',
    'THEN'       : 'THEN',
    'ELSE'       : 'ELSE',
    'ELSEIF'     : 'ELSEIF',
    'ENDIF'      : 'ENDIF',
    'GOTO'       : 'GOTO',
    'STOP'       : 'STOP',
    'RETURN'     : 'RETURN',
    'CALL'       : 'CALL',
    'FUNCTION'   : 'FUNCTION',
    'SUBROUTINE' : 'SUBROUTINE',
    'COMMON'     : 'COMMON',
    'DIMENSION'  : 'DIMENSION',
    'FORMAT'     : 'FORMAT',
    'PARAMETER'  : 'PARAMETER',
    'IMPLICIT'   : 'IMPLICIT',
    'NONE'       : 'NONE',
    'DATA'       : 'DATA',
    'SQRT'       : 'SQRT',
    'FLOAT'      : 'FLOAT',
}

# ============================================================
# LISTA DE TOKENS
# ============================================================

tokens = list(reserved.values()) + [
    # Literais
    'DOUBLE_PRECISION_LIT',
    'REAL_EXP_LIT',
    'REAL_LIT',
    'INTEGER_LIT',
    'LOGICAL_TRUE',
    'LOGICAL_FALSE',
    'STRING_LIT',
    'STAR_FMT',

    # Operadores aritméticos
    'POW',       # **
    'PLUS',      # +
    'MINUS',     # -
    'TIMES',     # *
    'DIVIDE',    # /

    # Concatenação
    'CONCAT',    # //

    # Operadores relacionais simbólicos
    'EQ_SYM',    # ==
    'NE_SYM',    # /=
    'LE_SYM',    # <=
    'GE_SYM',    # >=
    'LT_SYM',    # <
    'GT_SYM',    # >

    # Operadores relacionais estilo Fortran
    'OP_EQ',     # .EQ.
    'OP_NE',     # .NE.
    'OP_LT',     # .LT.
    'OP_GT',     # .GT.
    'OP_LE',     # .LE.
    'OP_GE',     # .GE.

    # Operadores lógicos
    'OP_AND',
    'OP_OR',
    'OP_NOT',
    'OP_EQV',
    'OP_NEQV',

    # Atribuição
    'ASSIGN',    # =

    # Pontuação
    'LPAREN',
    'RPAREN',
    'COMMA',
    'COLON',
    'LABEL',
    'NEWLINE',

    # Identificadores
    'ID',
]
