import math

WLEN = 16
INT_MAX = 0x7FFF   # 16'h7FFF
INT_MIN = -0x8000  # 16'h8000

POS_FRAC = 7
DIR_FRAC = 14

# fmt_t in tinytracer_pkg
FMT_POS = 0
FMT_DIR = 1

# cordic_op_t in tinytracer_pkg
CORDIC_DIV = 0b00   # a / b
CORDIC_SQRT = 0b01  # sqrt(a)
CORDIC_COS = 0b10   # a * cos(b)
CORDIC_MAG = 0b11   # sqrt(a^2 + b^2)

OP_NAMES = {
    CORDIC_DIV: "DIV",
    CORDIC_SQRT: "SQRT",
    CORDIC_COS: "COS",
    CORDIC_MAG: "MAG",
}

# spec limit to 1.743 rads, about 99.8 degrees
COS_MAX_ANGLE = 1.743
COS_MAX_RAW = int(COS_MAX_ANGLE * (1 << DIR_FRAC))


def to_signed(raw: int) -> int:
    raw &= 0xFFFF
    return raw - 0x10000 if raw & 0x8000 else raw


def clamp(value: int) -> int:
    return max(INT_MIN, min(INT_MAX, value))


def to_fixed(value: float, frac_bits: int = DIR_FRAC) -> int:
    return clamp(round(value * (1 << frac_bits))) & 0xFFFF


def to_float(raw: int, frac_bits: int = DIR_FRAC) -> float:
    return to_signed(raw) / (1 << frac_bits)


def legal(opcode: int, a_raw: int, b_raw: int, fmt: int = FMT_POS) -> bool:
    a, b = to_signed(a_raw), to_signed(b_raw)
    if opcode == CORDIC_DIV:
        return b != 0
    if opcode == CORDIC_SQRT:
        return a >= 0
    if opcode == CORDIC_COS:
        return abs(b) <= COS_MAX_RAW
    if opcode == CORDIC_MAG:
        return True
    raise ValueError(f"unknown opcode {opcode}")


def ideal(opcode: int, a_raw: int, b_raw: int, fmt: int = FMT_POS):
    if not legal(opcode, a_raw, b_raw, fmt):
        return None
    a = to_signed(a_raw)
    b = to_signed(b_raw)

    if opcode == CORDIC_DIV:
        return a * (1 << DIR_FRAC) / b # a/b * 2^14

    elif opcode == CORDIC_SQRT:
        if fmt == FMT_DIR:
            frac = DIR_FRAC 
        else:
            frac = POS_FRAC
        return math.sqrt(a * (1 << frac))

    elif opcode == CORDIC_COS:
        return a * math.cos(b / (1 << DIR_FRAC))

    else:
        return math.hypot(a, b)


def expected(opcode: int, a_raw: int, b_raw: int, fmt: int = FMT_POS):
    exact = ideal(opcode, a_raw, b_raw, fmt)
    if exact is None:
        return None
    return clamp(round(exact))


