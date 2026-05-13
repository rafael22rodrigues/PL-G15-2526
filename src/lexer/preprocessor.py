"""
preprocessor.py
Pré-processador de linhas para Fortran 77 (formato fixo e livre).

Formato fixo (ANSI X3.9-1978):
  Colunas 1-5  : label numérico (opcional)
  Coluna  6    : indicador de continuação (qualquer char != ' ' e != '0')
  Colunas 7-72 : código fonte
  Colunas 73+  : ignorado
"""

import re


def preprocess(source: str):
    """
    Pré-processa código Fortran 77 em formato fixo.
    Devolve lista de (label_str, code_str), com linhas de continuação já unidas.
    """
    lines = source.splitlines()
    statements = []
    current_label = ''
    current_code  = ''

    for raw in lines:
        line = raw.rstrip('\r\n')

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
        col1_5  = line[0:5]  if len(line) > 5  else line.ljust(5)[0:5]
        col6    = line[5]    if len(line) > 5  else ' '
        col7_72 = line[6:72] if len(line) > 6  else (line[5:] if len(line) > 5 else '')

        label_str       = col1_5.strip()
        is_continuation = (col6 not in (' ', '0', ''))
        code_part       = col6 if len(line) <= 5 else col7_72

        if is_continuation:
            current_code += ' ' + code_part.strip()
        else:
            if current_code.strip():
                statements.append((current_label, current_code.strip()))
            current_label = label_str
            current_code  = code_part

    if current_code.strip():
        statements.append((current_label, current_code.strip()))

    return statements


def preprocess_freeform(source: str):
    """
    Pré-processa código Fortran em formato livre.
    Linhas que terminam em & são continuação.
    """
    lines = source.splitlines()
    statements    = []
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

        # Label no início
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
    for l in lines[:20]:
        if l and l[0] in ('C', 'c', '*'):
            fixed_indicators += 1
        if len(l) > 72:
            fixed_indicators += 1
    if fixed_indicators > 0:
        return preprocess(source)
    else:
        return preprocess_freeform(source)
