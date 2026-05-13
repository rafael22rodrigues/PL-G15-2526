"""
intrinsics.py
Tabela de funções intrínsecas do Fortran 77 e regra de tipagem implícita.
"""

# ============================================================
# FUNÇÕES INTRÍNSECAS  (nome → tipo de retorno)
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
    """
    Regra de tipagem implícita do Fortran 77:
    variáveis cujo nome começa por I, J, K, L, M ou N → INTEGER; resto → REAL.
    """
    if name and name[0].upper() in 'IJKLMN':
        return 'INTEGER'
    return 'REAL'
