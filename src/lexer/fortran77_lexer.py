"""
fortran77_lexer.py
Analisador Léxico para Fortran 77 (ANSI X3.9-1978)
Usa ply.lex. Suporta formato de colunas fixas e free-form.
"""

import ply.lex as lex
import re

# ============================================================
# 1. PRÉ-PROCESSADOR DE LINHAS (formato fixo Fortran 77)
# ============================================================
# Colunas fixas:
#   1-5  : label numérico (opcional)
#   6    : indicador de continuação (qualquer char != ' ' e != '0')
#   7-72 : código fonte
#   73+  : ignorado (cartão perfurado histórico)

def preprocess(source: str):
    """
    Pré-processa código Fortran 77 em formato fixo.
    Devolve lista de (label, code_line) e já junta linhas de continuação.
    Retorna string limpa para o lexer, com tokens de NEWLINE inseridos.
    """
    lines = source.splitlines()
    statements = []   # lista de (label_str, code_str)
    current_label = ''
    current_code  = ''

    for raw in lines:
        # Normaliza para 72 colunas (padding com espaços se necessário)
        line = raw.rstrip('\r\n')

        # Linha em branco
        if len(line.strip()) == 0:
            continue

        # Comentário: coluna 1 é C, c ou *
        if line and line[0] in ('C', 'c', '*', '!'):
            continue
        # Comentário inline com ! (ignorar dentro de strings)
        if '!' in line:
            in_str = False
            for ci, ch in enumerate(line):
                if ch == "'":
                    in_str = not in_str
                elif ch == '!' and not in_str:
                    line = line[:ci]
                    break

        # Extrai campos fixos
        col1_5 = line[0:5]  if len(line) > 5  else line.ljust(5)[0:5]
        col6   = line[5]    if len(line) > 5  else ' '
        col7_72= line[6:72] if len(line) > 6  else (line[5:] if len(line) > 5 else '')

        label_str = col1_5.strip()
        is_continuation = (col6 not in (' ', '0', ''))
        code_part = col6 if len(line) <= 5 else col7_72  # fallback free-form

        # Se é linha de continuação, acrescenta ao statement corrente
        if is_continuation:
            current_code += ' ' + code_part.strip()
        else:
            # Guarda statement anterior (se existir)
            if current_code.strip():
                statements.append((current_label, current_code.strip()))
            current_label = label_str
            current_code  = code_part

    # Último statement
    if current_code.strip():
        statements.append((current_label, current_code.strip()))

    return statements


def preprocess_freeform(source: str):
    """
    Pré-processa código Fortran em formato livre (free-form).
    Linhas que terminam em & são continuação.
    """
    lines = source.splitlines()
    statements = []
    current_label = ''
    current_code  = ''

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # Comentários
        if line.startswith(('C ', 'c ', '* ', '!')):
            continue
        if line.startswith(('C\n', 'c\n', '*\n')):
            continue
        if '!' in line:
            line = line[:line.index('!')].strip()
        if not line:
            continue

        # Label no início (número seguido de espaço)
        m = re.match(r'^(\d{1,5})\s+(.*)', line)
        if m:
            if current_code.strip():
                statements.append((current_label, current_code.strip()))
            current_label = m.group(1)
            line = m.group(2)
        else:
            if current_code.strip() and not current_code.rstrip().endswith('&'):
                statements.append((current_label, current_code.strip()))
                current_label = ''
                current_code  = ''

        if line.endswith('&'):
            current_code += ' ' + line[:-1]
        else:
            current_code += ' ' + line
            statements.append((current_label, current_code.strip()))
            current_label = ''
            current_code  = ''

    if current_code.strip():
        statements.append((current_label, current_code.strip()))

    return statements


def preprocess_auto(source: str):
    """
    Detecta automaticamente se é formato fixo ou livre e pré-processa.
    Heurística: se existem linhas com C ou * na coluna 1, é fixo.
    """
    lines = source.splitlines()
    fixed_indicators = 0
    for l in lines[:20]:  # analisa as primeiras 20 linhas
        if l and l[0] in ('C', 'c', '*'):
            fixed_indicators += 1
        if len(l) > 72:
            fixed_indicators += 1
    if fixed_indicators > 0:
        return preprocess(source)
    else:
        return preprocess_freeform(source)


# ============================================================
# 2. PALAVRAS RESERVADAS
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
# 3. LISTA DE TOKENS
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
    'STAR_FMT',   # * em PRINT/READ

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

# ============================================================
# 4. REGRAS DE TOKENS
# ============================================================

# --- Literais numéricos (funções = maior prioridade) ---

def t_DOUBLE_PRECISION_LIT(t):
    r'(\d+\.?\d*|\.\d+)[Dd][+-]?\d+'
    t.value = float(t.value.replace('D','E').replace('d','e'))
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

# --- Literais lógicos ---
def t_LOGICAL_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_LOGICAL_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

# --- Operadores com pontos (ordem importa: mais longo primeiro) ---
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

# --- String literal ---
def t_STRING_LIT(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t

# --- Operadores multi-char (strings têm prioridade por comprimento) ---
t_POW    = r'\*\*'
t_CONCAT = r'//'
t_EQ_SYM = r'=='
t_NE_SYM = r'/='
t_LE_SYM = r'<='
t_GE_SYM = r'>='
t_LT_SYM = r'<'
t_GT_SYM = r'>'

# --- Operadores simples ---
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='

# --- Pontuação ---
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_COMMA    = r','
t_COLON    = r':'

# (resolvido no parser pelo contexto; no lexer tratamos * como TIMES
#  e o parser resolve a ambiguidade)

# --- Identificadores e palavras reservadas ---
def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'ID')
    if t.type == 'ID':
        t.value = t.value.upper()
    else:
        t.value = t.value.upper()
    return t

# --- LABEL: sequência de dígitos usada como rótulo (tratada no preprocessador,
#     mas também aqui para o modo free-form) ---
# Removido do lexer principal — labels são injetados pelo preprocessador.

# --- NEWLINE token (separador de statements) ---
def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# --- Ignorar espaços e tabs ---
t_ignore = ' \t\r'

# --- Erros ---
def t_error(t):
    print(f"  [ERRO LÉXICO] Caractere inválido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# ============================================================
# 5. CONSTRUÇÃO DO LEXER
# ============================================================
lexer = lex.lex()


# ============================================================
# 6. TOKENIZAR COM PRÉ-PROCESSAMENTO
# ============================================================

def tokenize_source(source: str, use_fixed=True):
    """
    Tokeniza código Fortran 77.
    Devolve lista de tokens enriquecida com labels.
    """
    if use_fixed:
        statements = preprocess(source)
    else:
        statements = preprocess_freeform(source)

    all_tokens = []
    for label, code in statements:
        if label:
            # injeta token LABEL artificial
            all_tokens.append(('LABEL', int(label), 0))
        lx = lex.lex()
        lx.input(code)
        for tok in lx:
            if tok.type == 'NEWLINE':
                continue
            all_tokens.append((tok.type, tok.value, tok.lineno))
        all_tokens.append(('NEWLINE', '\n', 0))

    return all_tokens


# ============================================================
# 7. FUNÇÃO DE TESTE / DEBUG
# ============================================================
def analisar(codigo: str, use_fixed=True):
    if use_fixed:
        stmts = preprocess(codigo)
    else:
        stmts = preprocess_freeform(codigo)

    print(f"\n{'='*65}")
    print(f"{'TOKEN':<25} {'TIPO':<22} {'LINHA'}")
    print(f"{'='*65}")

    for label, code in stmts:
        if label:
            print(f"{'[LABEL] '+label:<25} {'LABEL':<22}")
        lx = lex.lex()
        lx.input(code)
        for tok in lx:
            if tok.type != 'NEWLINE':
                print(f"{str(tok.value):<25} {tok.type:<22} {tok.lineno}")
        print(f"{'---NEWLINE---':<25}")
    print(f"{'='*65}\n")


# ============================================================
# 8. TESTE STANDALONE
# ============================================================
if __name__ == '__main__':
    programa = """\
      PROGRAM SOMAARR
      INTEGER NUMS(5)
      INTEGER I, SOMA
      SOMA = 0
      PRINT *, 'Introduza 5 numeros inteiros:'
      DO 30 I = 1, 5
      READ *, NUMS(I)
      SOMA = SOMA + NUMS(I)
 30   CONTINUE
      PRINT *, 'A soma dos numeros e: ', SOMA
      END
"""
    print("Código Fortran 77 a analisar:")
    print(programa)
    analisar(programa)
