import sys
import itertools
from enum import Enum, auto
from dataclasses import dataclass

class TokenKind(Enum):
    WHEN = auto()
    EVERY = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    DO = auto()
    END = auto()

    AND = auto()
    OR = auto()
    NOT = auto()
    
    TRUE = auto()
    FALSE = auto()
    ON = auto()
    OFF = auto()

    MODO = auto() 
    COLOR = auto()
    
    SENSOR = auto()       # sensor_temp, sensor_luz, etc.
    ACTUATOR = auto()     # foco_entrada, aire_acondicionado, etc.
    ATTRIBUTE = auto()    # .estado, .brillo, etc. (incluye el punto)
    
    NUMBER = auto()       # 25, 80, 100, etc.
    TEMP = auto()         # 25°C
    PERCENT = auto()      # 80%
    LUX = auto()          # 600lux
    TIME_DURATION = auto()# 30m, 10s, 1h
    HORA = auto()         # 22:00
    FECHA = auto()        # 21/04/2026
    STRING = auto()       # "texto"
    EMAIL = auto()        # alguien@dominio.com
    
    EQUAL    = auto()           # ==
    NEGATE = auto()          # !=
    GREATER = auto()     # >
    LESSER = auto()        # < 
    GREAT_EQUAL = auto()   # >=
    LESS_EQUAL = auto()       # <=
    ASSIGN = auto()          # =
    
    LPAREN = auto() #(
    RPAREN = auto() #)
    
    EOF = auto()
    ERROR = auto()
    

@dataclass(frozen=True)
class Token:
    kind: TokenKind
    src: str
    row: int
    col: int
    
    def __repr__(self):
        return f"Token({self.kind.name}, '{self.src}', línea={self.row}, col={self.col})"

PALABRAS_RESERVADAS = {
    "when": TokenKind.WHEN,
    "every": TokenKind.EVERY,
    "if": TokenKind.IF,
    "then": TokenKind.THEN,
    "else": TokenKind.ELSE,
    "do": TokenKind.DO,
    "end": TokenKind.END,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "on": TokenKind.ON,
    "off": TokenKind.OFF,
}

PREFIJOS_SENSOR = ("sensor_temp", "sensor_luz", "sensor_movimiento",
                "sensor_humo", "sensor_humedad")

PREFIJOS_ACTUADOR = ("foco_", "aire_", "persiana_", "cerradura_",
                    "reloj_", "altavoz_", "alarma_")

ATRIBUTOS_VALIDOS = {".estado", ".brillo", ".color", ".modo", ".temp_obj",
                    ".temp_act", ".posicion", ".hora", ".fecha", ".volumen",
                    ".mute", ".mensaje", ".email_notif", ".activada"}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.row = 1
        self.col = 1
        self.tokens = []
        self.errors = []


    def peek(self, offset=0):
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return ''
    
    
    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.row += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    
    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.peek()
            
            if ch in ' \t\r\n':
                self.advance()
                continue
            
            if ch == '/' and self.peek(1) == '/':
                self.consumir_comentario()
                continue
            
            if ch.isalpha() or ch == '_':
                self.consumir_identificador()
                continue
            
            if ch == '.':
                self.consumir_atributo()
                continue
            
            if ch == '"':
                self.consumir_string()
                continue
            
            if ch in '=!<>()':
                self.consumir_operador()
                continue

            if ch.isdigit():
                self.consumir_numero()
                continue
            
            self.errors.append(f"Carácter no reconocido: '{ch}'")
            self.advance()
        
        self.tokens.append(Token(TokenKind.EOF, "", self.row, self.col))
        return self.tokens


    def consumir_numero(self):
        start_row = self.row
        start_col = self.col
        lexema = ""

        while self.pos < len(self.source) and self.peek().isdigit():
            lexema += self.advance()

        if self.peek() == '.' and self.peek(1).isdigit():
            lexema += self.advance()
            while self.pos < len(self.source) and self.peek().isdigit():
                lexema += self.advance()

        sig = self.peek()

        if sig == '%':
            lexema += self.advance()
            self.tokens.append(Token(TokenKind.PERCENT, lexema, start_row, start_col))

        elif sig == '°' or (sig == 'C' and lexema):
            if sig == '°':
                lexema += self.advance()
            if self.peek() == 'C':
                lexema += self.advance()
                self.tokens.append(Token(TokenKind.TEMP, lexema, start_row, start_col))
            else:
                self.errors.append(f"Unidad de temperatura incompleta: '{lexema}'")

        elif sig in ('l', 's', 'm', 'h'):
            if sig == 'l' and self.source[self.pos:self.pos+3] == 'lux':
                lexema += self.advance()
                lexema += self.advance()
                lexema += self.advance()
                self.tokens.append(Token(TokenKind.LUX, lexema, start_row, start_col))
            elif sig in ('s', 'm', 'h'):
                lexema += self.advance()
                self.tokens.append(Token(TokenKind.TIME_DURATION, lexema, start_row, start_col))
            else:
                self.tokens.append(Token(TokenKind.NUMBER, lexema, start_row, start_col))

        else:
            self.tokens.append(Token(TokenKind.NUMBER, lexema, start_row, start_col))


    def consumir_comentario(self):
        self.advance()  
        self.advance()
        while self.pos < len(self.source) and self.peek() != '\n':
            self.advance()


    def consumir_identificador(self):
        start_row = self.row
        start_col = self.col
        lexema = ""
        
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            lexema += self.advance()
        
        lexema_lower = lexema.lower()
        
        if lexema_lower in PALABRAS_RESERVADAS:
            self.tokens.append(Token(
                PALABRAS_RESERVADAS[lexema_lower],
                lexema, start_row, start_col
            ))
            return
        
        if lexema_lower in ("blanco", "rojo", "azul"):
            self.tokens.append(Token(TokenKind.COLOR, lexema, start_row, start_col))
            return
        
        if lexema_lower in ("frio", "calor", "vent"):
            self.tokens.append(Token(TokenKind.MODO, lexema, start_row, start_col))
            return
        
        for prefijo in PREFIJOS_SENSOR:
            if lexema_lower == prefijo or lexema_lower.startswith(prefijo + "_"):
                self.tokens.append(Token(TokenKind.SENSOR, lexema, start_row, start_col))
                return
        
        for prefijo in PREFIJOS_ACTUADOR:
            if lexema_lower.startswith(prefijo):
                self.tokens.append(Token(TokenKind.ACTUATOR, lexema, start_row, start_col))
                return
        
        self.errors.append(f"Identificador no reconocido: '{lexema}' ")


    def consumir_atributo(self):
        start_row = self.row
        start_col = self.col
        
        self.advance() 
        
        nombre = ""
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            nombre += self.advance()
        
        if not nombre:
            self.errors.append("Se esperaba un nombre de atributo después del '.'")
            return
        
        if nombre.lower() not in ATRIBUTOS_VALIDOS:
            self.errors.append(f"Atributo desconocido: '.{nombre}'")
            return
        
        self.tokens.append(Token(
            TokenKind.ATTRIBUTE,
            "." + nombre,
            start_row, start_col
        ))


    def consumir_string(self):
        start_row = self.row
        start_col = self.col
        
        self.advance() 
        contenido = ""
        
        while self.pos < len(self.source) and self.peek() != '"':
            if self.peek() == '\n':
                self.errors.append("Cadena sin cerrar antes del fin de línea", start_row, start_col)
                return
            contenido += self.advance()
        
        if self.pos >= len(self.source):
            self.errors.append("Cadena sin cerrar (EOF)")
            return
        
        self.advance() 
        
        self.tokens.append(Token(
            TokenKind.STRING,
            '"' + contenido + '"',
            start_row, start_col
        ))


    def consumir_operador(self):
        start_row = self.row
        start_col = self.col
        ch = self.peek()
        sig = self.peek(1)
        
        if ch == '=' and sig == '=':
            self.advance(); self.advance()
            self.tokens.append(Token(TokenKind.EQUAL, "==", start_row, start_col))
            return
        
        if ch == '!' and sig == '=':
            self.advance(); self.advance()
            self.tokens.append(Token(TokenKind.NEGATE, "!=", start_row, start_col))
            return
        
        if ch == '>' and sig == '=':
            self.advance(); self.advance()
            self.tokens.append(Token(TokenKind.GREAT_EQUAL, ">=", start_row, start_col))
            return
        
        if ch == '<' and sig == '=':
            self.advance(); self.advance()
            self.tokens.append(Token(TokenKind.LESS_EQUAL, "<=", start_row, start_col))
            return
        
        if ch == '=':
            self.advance()
            self.tokens.append(Token(TokenKind.ASSIGN, "=", start_row, start_col))
            return
        
        if ch == '>':
            self.advance()
            self.tokens.append(Token(TokenKind.GREATER, ">", start_row, start_col))
            return
        
        if ch == '<':
            self.advance()
            self.tokens.append(Token(TokenKind.LESSER, "<", start_row, start_col))
            return
        
        if ch == '(':
            self.advance()
            self.tokens.append(Token(TokenKind.LPAREN, "(", start_row, start_col))
            return
        
        if ch == ')':
            self.advance()
            self.tokens.append(Token(TokenKind.RPAREN, ")", start_row, start_col))
            return
        
        if ch == '!':
            self.errors.append(f"Operador inválido: '!' (¿quisiste decir '!='?)")
            self.advance()
            return
        
        self.errors.append(f"Operador no reconocido: '{ch}'")
        self.advance()


def main():
    file_name = sys.argv[1]

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: archivo '{file_name}' no encontrado")
        sys.exit(1)
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    print("Errores encontrados:")
    for err in lexer.errors:
        print(f"  {err}")

    print("Análisis léxico exitoso.")
    for tok in tokens:
        print(tok)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecución interrumpida por teclado")

        sys.exit(130)
