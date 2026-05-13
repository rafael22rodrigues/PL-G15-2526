"""
emitter.py
Helpers de baixo nível para emissão de instruções VM.
O CodeGen herda desta classe para ter acesso a emit / new_label / emit_label.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vm.vm import Instr


class Emitter:
    """Mixin com helpers de emissão de código VM."""

    def __init__(self):
        self.code      = []
        self.label_cnt = 0

    def emit(self, op, *args):
        """Acrescenta uma instrução à lista de código."""
        self.code.append(Instr(op, *args))

    def new_label(self, prefix='L') -> str:
        """Gera um novo label único com o prefixo indicado."""
        self.label_cnt += 1
        return f"{prefix}_{self.label_cnt}"

    def emit_label(self, name: str):
        """Emite uma pseudo-instrução LABEL (resolve saltos)."""
        self.emit('LABEL', name)
