# Compilador Fortran 77 — Relatório Técnico

**Unidade Curricular:** Processamento de Linguagens 2026  
**Data de entrega:** 17/05/2026  
**Linguagem alvo:** Fortran 77 (ANSI X3.9-1978)  
**Implementação:** Python 3 com `ply` (Python Lex-Yacc)

---

## 1. Arquitetura Geral

O compilador está organizado em cinco fases sequenciais:

```
Código Fortran 77
       │
       ▼
┌─────────────────┐
│ Pré-processador │  (format fixo/livre, labels, continuações)
└────────┬────────┘
         │ lista de (label, statement)
         ▼
┌─────────────────┐
│  Análise Léxica │  src/lexer/fortran77_lexer.py   (ply.lex)
└────────┬────────┘
         │ stream de tokens com LABEL injectado
         ▼
┌──────────────────┐
│ Análise Sintática│  src/parser/fortran77_parser.py  (ply.yacc)
└────────┬─────────┘
         │ AST
         ▼
┌──────────────────┐
│ Análise Semântica│  src/semantic/semantic.py
└────────┬─────────┘
         │ AST anotada + tabela de símbolos
         ▼
┌─────────────────┐
│ Geração de Código│  src/codegen/codegen.py
└────────┬────────┘
         │ lista de instruções VM
         ▼
┌─────────────────┐
│  Máquina Virtual│  vm/vm.py
└─────────────────┘
```

---

## 2. Formato de Colunas

### Decisão: Formato Fixo (Fortran 77 Standard)

Optámos por suportar o **formato de colunas fixas** (ANSI X3.9-1978), que é o formato canónico do Fortran 77:

| Colunas | Significado                     |
|---------|---------------------------------|
| 1       | `C`, `c` ou `*` → linha de comentário |
| 1–5     | Label numérico (opcional)       |
| 6       | Indicador de continuação (qualquer char ≠ `' '` e ≠ `'0'`) |
| 7–72    | Código fonte                    |
| 73+     | Ignorado (histórico de cartões) |

O compilador também aceita comentários inline com `!` (fora de strings) e suporta formato livre via flag `--free-form`.

O pré-processamento é feito antes do lexer, resolvendo:
- Labels -> injetados como tokens `LABEL` artificiais
- Linhas de continuação -> concatenadas ao statement anterior
- Comentários -> removidos antes da tokenização

---

## 3. Análise Léxica

**Ficheiro:** `src/lexer/fortran77_lexer.py`  
**Ferramenta:** `ply.lex`

### Tokens reconhecidos

| Categoria | Exemplos |
|-----------|---------|
| Palavras reservadas | `PROGRAM`, `IF`, `DO`, `GOTO`, `INTEGER`, `REAL`, `LOGICAL`, ... |
| Literais | `INTEGER_LIT`, `REAL_LIT`, `REAL_EXP_LIT`, `DOUBLE_PRECISION_LIT`, `LOGICAL_TRUE/FALSE`, `STRING_LIT` |
| Operadores aritméticos | `+` `-` `*` `/` `**` |
| Operadores relacionais (Fortran) | `.EQ.` `.NE.` `.LT.` `.LE.` `.GT.` `.GE.` |
| Operadores relacionais (simbólicos) | `==` `/=` `<` `<=` `>` `>=` |
| Operadores lógicos | `.AND.` `.OR.` `.NOT.` `.EQV.` `.NEQV.` |
| Concatenação | `//` |
| Pontuação | `(` `)` `,` `:` |
| Especiais | `LABEL` (injectado), `NEWLINE` (separador de statements) |

### Decisões relevantes

- **Funções intrínsecas** (`MOD`, `ABS`, `SQRT`, etc.) são tratadas como identificadores comuns (`ID`) e resolvidas na geração de código, evitando conflitos com a gramática.
- **Fortran ignora espaços** fora de strings — implementado via `t_ignore`.
- **Strings** usam apóstrofos com duplicação interna (`''` → `'`).
- A **ambiguidade** entre `*` como operador de multiplicação e `*` no `PRINT *` é resolvida pelo contexto no parser.

---

## 4. Análise Sintática

**Ficheiro:** `src/parser/fortran77_parser.py`  
**Ferramenta:** `ply.yacc` (LALR(1))

### Gramática (resumo)

```
program          → program_unit+
program_unit     → PROGRAM ID newlines decl_list stmt_list END
                 | type_spec FUNCTION ID(params) newlines decl_list stmt_list END
                 | SUBROUTINE ID(params) newlines decl_list stmt_list END

decl_stmt        → type_spec var_decl_list
                 | IMPLICIT NONE
                 | DIMENSION var_decl_list
                 | PARAMETER (assign_list)

stmt             → [LABEL] stmt_body NEWLINE
stmt_body        → assign | print | read | write
                 | if_then | logical_if | do | continue
                 | goto | stop | return | call | format

expr             → expr OP expr | -expr | .NOT. expr
                 | ID | ID(expr_list) | literals | (expr)
```

### Construções suportadas

- Declarações de tipos com arrays: `INTEGER NUMS(5)`
- `IF-THEN-ELSE-ENDIF` com múltiplos `ELSEIF`
- IF lógico de uma linha: `IF (cond) stmt`
- Ciclo `DO` com label e `CONTINUE` (com e sem step)
- `GOTO` com label numérico
- `PRINT *` e `READ *` com listas de I/O
- `CALL` e `RETURN` para subprogramas
- Funções tipadas: `INTEGER FUNCTION CONVRT(N, B)`

### Ambiguidade ArrayRef vs FuncCall

Em Fortran, `X(I)` tanto pode ser um acesso a array como uma chamada de função. O parser gera sempre um nó `FuncCall` e a resolução é feita na análise semântica e na geração de código, consultando a tabela de símbolos.

---

## 5. Análise Semântica

**Ficheiro:** `src/semantic/semantic.py`

### Tabela de Símbolos

Hierarquia de scopes: `global → program_unit`. Cada símbolo regista:
- Nome, tipo (`INTEGER`, `REAL`, `LOGICAL`, `CHARACTER`, `DOUBLE PRECISION`)
- Dimensões (para arrays)
- Flags: `is_param`, `is_func`

### Verificações implementadas

1. **Tipagem implícita** — variáveis começadas por I–N são `INTEGER`, restantes `REAL` (regra standard do Fortran 77)
2. **IMPLICIT NONE** — desactiva tipagem implícita; variáveis não declaradas geram erro
3. **Redeclaração de variáveis** — detectada e reportada
4. **Validação de labels** — todos os labels referenciados por `GOTO` e `DO` são verificados contra os labels definidos no mesmo `ProgramUnit`
5. **Validação de arrays** — uso como array sem declaração de dimensões gera erro
6. **Coerção de tipos** — avisos para atribuições entre tipos incompatíveis
7. **Funções intrínsecas** — tabela de 30+ funções com tipo de retorno conhecido (`MOD`, `ABS`, `SQRT`, `SIN`, `COS`, etc.)
8. **Subprogramas externos** — avisos para chamadas a subprogramas não declarados

---

## 6. Geração de Código

**Ficheiro:** `src/codegen/codegen.py`

Geração directa de código para a VM de pilha (sem representação intermédia separada).

### Estratégia por construção

| Construção Fortran | Código VM gerado |
|-------------------|-----------------|
| `x = expr` | `gen_expr(expr); STORE x` |
| `arr(i) = expr` | `gen_expr(i); gen_expr(expr); STOREARR arr` |
| `PRINT *, a, b` | `PUSH a; PRINT; PUSH b; PRINT; PRINTLN` |
| `READ *, x` | `READ x` |
| `IF (c) THEN ... ELSE ... ENDIF` | `gen_expr(c); JZ else_lbl; ...; JMP end_lbl; LABEL else_lbl; ...; LABEL end_lbl` |
| `DO lbl var=s,e[,step]` | `STORE var; LABEL loop; LOAD var; PUSH e; LE; JZ end; ...; ADD step; STORE var; JMP loop; LABEL end` |
| `GOTO lbl` | `JMP LBL_lbl` |
| `CALL sub(args)` | `gen_expr(args); CALL sub N` |
| `FUNCTION f(params)` | `FUNC f; LOADPARAM i; STORE p_i; ...; LOAD f; RET; ENDFUNC` |

---

## 7. Máquina Virtual

**Ficheiro:** `vm/vm.py`

VM de pilha com as seguintes instruções:

**Pilha:** `PUSH val`, `LOAD name`, `STORE name`, `LOADARR name`, `STOREARR name`  
**Aritmética:** `ADD`, `SUB`, `MUL`, `DIV`, `POW`, `IMOD`, `UMINUS`  
**Comparação:** `EQ`, `NE`, `LT`, `LE`, `GT`, `GE`  
**Lógica:** `AND`, `OR`, `NOT`  
**Saltos:** `JMP label`, `JZ label`, `JNZ label`  
**I/O:** `PRINT`, `PRINTLN`, `READ name`, `READARR name`  
**Subprogramas:** `FUNC name`, `ENDFUNC`, `CALL name nargs`, `RET`, `LOADPARAM i`  
**Especiais:** `LABEL name`, `NOP`, `HALT`, `INTCAST`, `FLOATCAST`, `CONCAT`

A VM inclui uma tabela de **funções built-in** (`MOD`, `ABS`, `SQRT`, `SIN`, `COS`, `EXP`, `LOG`, etc.) resolvidas em tempo de execução via `CALL`.

---

## 8. Como Executar

### Instalação

```bash
pip install ply
```

### Uso

```bash
# Compilar e executar
python compiler.py tests/programs/programa.f77

# Modo verbose (mostra todas as fases)
python compiler.py tests/programs/programa.f77 -v

# Guardar código VM em ficheiro
python compiler.py tests/programs/programa.f77 -o programa.vm

# Só análise léxica
python compiler.py tests/programs/programa.f77 --lex-only

# Só parsing (mostra AST)
python compiler.py tests/programs/programa.f77 --parse-only

# Com input de ficheiro
python compiler.py tests/programs/programa.f77 --input programa.input

# Formato livre (free-form)
python compiler.py tests/programs/programa.f77 --free-form
```

### Testes automáticos

```bash
python run_tests.py
```

---

## 9. Testes

Foram implementados testes para todos os exemplos do enunciado:

| Programa | Input | Output esperado |
|----------|-------|-----------------|
| `hello.f77` | — | `Ola, Mundo!` |
| `fatorial.f77` | `5` | `120` |
| `fatorial.f77` | `0` | `1` |
| `primo.f77` | `17` | `e um numero primo` |
| `primo.f77` | `4` | `nao e um numero primo` |
| `somaarr.f77` | `10 20 30 40 50` | `150` |
| `conversor.f77` | `10` | `BASE 2: 1010` |

---

## 10. Dificuldades Encontradas

---
