"""
vm.py
Máquina Virtual de Pilha para execução de código gerado pelo compilador Fortran 77.

Instrucões:
  PUSH val        — empurra valor literal
  LOAD name       — carrega variável
  STORE name      — guarda em variável
  LOADARR name    — carrega elemento de array (índice no topo da pilha)
  STOREARR name   — guarda elemento de array (índice abaixo do topo)
  ADD / SUB / MUL / DIV / POW
  UMINUS          — negação unária
  EQ / NE / LT / LE / GT / GE
  AND / OR / NOT
  JMP label       — salto incondicional
  JZ  label       — salta se topo == False/0
  JNZ label       — salta se topo != 0
  PRINT           — imprime topo da pilha
  PRINTLN         — imprime topo + newline
  READ  name      — lê valor e guarda em variável
  READARR name    — lê valor e guarda em array[idx]
  CALL  name nargs— chama sub/função
  RET             — retorna de função
  HALT            — termina execução
  LABEL name      — marca posição (pseudo-instrução, removida antes da execução)
  NOP             — não faz nada
  CONCAT          — concatenação de strings
  IMOD            — inteiro módulo
  INTCAST         — converte para inteiro
  FLOATCAST       — converte para float
"""

import math
import sys


# ============================================================
# INSTRUÇÃO
# ============================================================

class Instr:
    def __init__(self, op, *args):
        self.op   = op
        self.args = args

    def __repr__(self):
        if self.args:
            return f"{self.op} {' '.join(str(a) for a in self.args)}"
        return self.op


# ============================================================
# MÁQUINA VIRTUAL
# ============================================================

class VM:
    def __init__(self, instructions, input_data=None, output_fn=None):
        self.instructions = instructions   # lista de Instr
        self.stack        = []
        self.memory       = {}             # variáveis globais
        self.arrays       = {}             # arrays: name -> dict{idx: val}
        self.call_stack   = []             # [(return_addr, local_memory)]
        self.ip           = 0
        self.label_map    = {}
        self.input_buf    = list(input_data) if input_data else []
        self.output_buf   = []
        self.output_fn    = output_fn or print
        self.functions    = {}             # name -> start_addr

        self._build_label_map()

    def _build_label_map(self):
        for i, instr in enumerate(self.instructions):
            if instr.op == 'LABEL':
                self.label_map[instr.args[0]] = i + 1
            elif instr.op == 'FUNC':
                self.functions[instr.args[0]] = i + 1

    def run(self):
        while self.ip < len(self.instructions):
            instr = self.instructions[self.ip]
            self.ip += 1
            self._exec(instr)

    def _exec(self, instr):
        op = instr.op
        args = instr.args

        if op == 'LABEL' or op == 'NOP':
            pass

        elif op == 'FUNC':
            # Pular corpo da função (só entra via CALL)
            # Procura o RET correspondente
            depth = 1
            while depth > 0:
                instr2 = self.instructions[self.ip]
                self.ip += 1
                if instr2.op == 'FUNC':
                    depth += 1
                elif instr2.op == 'ENDFUNC':
                    depth -= 1

        elif op == 'ENDFUNC':
            pass

        elif op == 'PUSH':
            self.stack.append(args[0])

        elif op == 'LOAD':
            val = self.memory.get(args[0])
            if val is None:
                # tenta na frame activa
                if self.call_stack:
                    val = self.call_stack[-1][1].get(args[0], 0)
                else:
                    val = 0
            self.stack.append(val)

        elif op == 'STORE':
            val = self.stack.pop()
            if self.call_stack:
                self.call_stack[-1][1][args[0]] = val
            else:
                self.memory[args[0]] = val

        elif op == 'LOADARR':
            idx = self.stack.pop()
            arr = self.arrays.get(args[0], {})
            self.stack.append(arr.get(idx, 0))

        elif op == 'STOREARR':
            val = self.stack.pop()
            idx = self.stack.pop()
            if args[0] not in self.arrays:
                self.arrays[args[0]] = {}
            self.arrays[args[0]][idx] = val

        elif op == 'ADD':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a + b)

        elif op == 'SUB':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a - b)

        elif op == 'MUL':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a * b)

        elif op == 'DIV':
            b = self.stack.pop(); a = self.stack.pop()
            if isinstance(a, int) and isinstance(b, int):
                self.stack.append(a // b)
            else:
                self.stack.append(a / b)

        elif op == 'POW':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a ** b)

        elif op == 'IMOD':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(int(a) % int(b))

        elif op == 'UMINUS':
            self.stack.append(-self.stack.pop())

        elif op == 'CONCAT':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(str(a) + str(b))

        elif op == 'INTCAST':
            self.stack.append(int(self.stack.pop()))

        elif op == 'FLOATCAST':
            self.stack.append(float(self.stack.pop()))

        # Comparações — devolvem True/False
        elif op == 'EQ':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a == b)
        elif op == 'NE':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a != b)
        elif op == 'LT':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a < b)
        elif op == 'LE':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a <= b)
        elif op == 'GT':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a > b)
        elif op == 'GE':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a >= b)

        elif op == 'AND':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(bool(a) and bool(b))
        elif op == 'OR':
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(bool(a) or bool(b))
        elif op == 'NOT':
            self.stack.append(not bool(self.stack.pop()))

        elif op == 'JMP':
            self.ip = self.label_map[args[0]]

        elif op == 'JZ':
            val = self.stack.pop()
            if not val:
                self.ip = self.label_map[args[0]]

        elif op == 'JNZ':
            val = self.stack.pop()
            if val:
                self.ip = self.label_map[args[0]]

        elif op == 'PRINT':
            val = self.stack.pop()
            self.output_fn(self._fmt(val), end='')
            self.output_buf.append(self._fmt(val))

        elif op == 'PRINTLN':
            self.output_fn('')
            self.output_buf.append('\n')

        elif op == 'READ':
            if self.input_buf:
                raw = self.input_buf.pop(0)
            else:
                raw = input()
            val = self._parse_input(raw)
            if self.call_stack:
                self.call_stack[-1][1][args[0]] = val
            else:
                self.memory[args[0]] = val

        elif op == 'READARR':
            idx = self.stack.pop()
            if self.input_buf:
                raw = self.input_buf.pop(0)
            else:
                raw = input()
            val = self._parse_input(raw)
            if args[0] not in self.arrays:
                self.arrays[args[0]] = {}
            self.arrays[args[0]][idx] = val

        elif op == 'CALL':
            fname = args[0]
            nargs = int(args[1]) if len(args) > 1 else 0
            call_args = list(reversed([self.stack.pop() for _ in range(nargs)]))

            if fname in self.functions:
                local_mem = {}
                # Os argumentos são passados como __arg0, __arg1, ...
                for i, v in enumerate(call_args):
                    local_mem[f'__arg{i}'] = v
                self.call_stack.append((self.ip, local_mem))
                self.ip = self.functions[fname]
            elif fname in BUILTIN_FUNCS:
                result = BUILTIN_FUNCS[fname](*call_args)
                self.stack.append(result)
            else:
                print(f"[VM] Função desconhecida: {fname}")
                self.stack.append(0)

        elif op == 'RET':
            if not self.call_stack:
                return
            ret_addr, local_mem = self.call_stack.pop()
            # valor de retorno fica no topo da pilha (se for function)
            self.ip = ret_addr

        elif op == 'LOADPARAM':
            # Carrega argumento formal pelo índice
            idx = int(args[0])
            if self.call_stack:
                val = self.call_stack[-1][1].get(f'__arg{idx}', 0)
            else:
                val = 0
            self.stack.append(val)

        elif op == 'HALT':
            self.ip = len(self.instructions)

        elif op == 'SQRT_FUNC':
            self.stack.append(math.sqrt(self.stack.pop()))

        elif op == 'ABS_FUNC':
            self.stack.append(abs(self.stack.pop()))

        else:
            print(f"[VM] Instrução desconhecida: {op}")

    def _fmt(self, val):
        if isinstance(val, bool):
            return '.TRUE.' if val else '.FALSE.'
        if isinstance(val, float):
            if val == int(val):
                return str(int(val))
            return str(val)
        return str(val)

    def _parse_input(self, raw):
        raw = str(raw).strip()
        try:
            if '.' in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw


# ============================================================
# FUNÇÕES BUILT-IN
# ============================================================
BUILTIN_FUNCS = {
    'MOD'  : lambda a, b: int(a) % int(b),
    'ABS'  : abs,
    'SQRT' : math.sqrt,
    'INT'  : int,
    'FLOAT': float,
    'MAX'  : max,
    'MIN'  : min,
    'EXP'  : math.exp,
    'LOG'  : math.log,
    'LOG10': math.log10,
    'SIN'  : math.sin,
    'COS'  : math.cos,
    'TAN'  : math.tan,
    'ASIN' : math.asin,
    'ACOS' : math.acos,
    'ATAN' : math.atan,
    'ATAN2': math.atan2,
    'SIGN' : lambda a, b: abs(a) if b >= 0 else -abs(a),
    'DBLE' : float,
    'REAL' : float,
    'NINT' : round,
    'IABS' : lambda x: abs(int(x)),
}
