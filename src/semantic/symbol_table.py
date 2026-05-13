"""
symbol_table.py
Tabela de símbolos com suporte a scopes hierárquicos.
"""


class Symbol:
    """Representa um símbolo (variável, array, função, parâmetro) na tabela."""

    def __init__(self, name, stype, dims=None, is_param=False, is_func=False):
        self.name     = name
        self.stype    = stype      # 'INTEGER'|'REAL'|'LOGICAL'|'CHARACTER'|'DOUBLE PRECISION'
        self.dims     = dims       # lista de tamanhos para arrays, ou None
        self.is_param = is_param
        self.is_func  = is_func

    def __repr__(self):
        return f"Symbol({self.name}, {self.stype}, dims={self.dims})"


class SymbolTable:
    """Tabela de símbolos para um scope. Suporta lookup hierárquico via parent."""

    def __init__(self, parent=None, scope_name='global'):
        self.parent     = parent
        self.scope_name = scope_name
        self.symbols    = {}

    def declare(self, sym: Symbol) -> bool:
        """
        Declara um símbolo. Devolve False se já existir neste scope
        (exceto parâmetros formais, que podem ser redeclarados com tipo explícito).
        """
        existing = self.symbols.get(sym.name)
        if existing:
            # Parâmetro formal a ser tipado explicitamente — actualiza o tipo
            if existing.is_param:
                existing.stype = sym.stype
                if sym.dims:
                    existing.dims = sym.dims
                return True
            return False
        self.symbols[sym.name] = sym
        return True

    def lookup(self, name: str):
        """Procura um símbolo neste scope e nos scopes pai."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str):
        """Procura apenas neste scope (sem subir para o pai)."""
        return self.symbols.get(name)
