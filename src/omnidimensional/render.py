"""Safe presentation of exact values that can be astronomically large.

A closed form is O(1) to *compute*, but the value it returns is not O(1) to
*print*: ``Geometric(1, 2).sum(10**6)`` is an exact integer with 301,030
digits. CPython refuses ``int -> str`` above 4300 digits and ``float()``
overflows long before that, so naive rendering turns a correct answer into a
crash.

These helpers never round the value itself — they only bound its rendering.
"""

import math
from fractions import Fraction

# CPython's int -> str guard trips at 4300 digits; stay clear of it.
DIGIT_LIMIT = 4000


def as_fraction(x):
    """Coerce to an exact Fraction, binary-exact for floats."""
    return x if isinstance(x, Fraction) else Fraction(x)


def exact(x):
    """Coerce to a Fraction, reading floats through their decimal repr.

    ``Fraction(0.1)`` is the binary value 3602879701896397/36028797018963968;
    ``exact(0.1)`` is 1/10. Use this for anything a human typed.
    """
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        return Fraction(str(x))
    return Fraction(x)


def _log10_int(i):
    """log10 of a positive int, without ever building a float from it.

    Uses the top 64 bits plus the shift, so it works on integers with millions
    of digits where ``math.log10(i)`` would raise OverflowError.
    """
    if i <= 0:
        raise ValueError("_log10_int requires a positive integer")
    shift = max(0, i.bit_length() - 64)
    return math.log10(i >> shift) + shift * math.log10(2.0)


def _int_digits(i):
    """Number of decimal digits in an int, without stringifying it."""
    i = abs(int(i))
    if i == 0:
        return 1
    return int(_log10_int(i)) + 1


def log10_abs(x):
    """log10(|x|) for an exact rational. None when x == 0."""
    f = as_fraction(x)
    if f == 0:
        return None
    return _log10_int(abs(f.numerator)) - _log10_int(f.denominator)


def digit_count(x):
    """Decimal digits in the numerator of x."""
    if isinstance(x, float):
        return len("%.0f" % abs(x))
    return _int_digits(as_fraction(x).numerator)


def to_decimal(x):
    """``float(x)``, or None when the value overflows a float.

    Callers should treat None as "too large for IEEE 754" and fall back to
    :func:`log10_abs` for the magnitude.
    """
    try:
        return float(x)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def describe(x, limit=DIGIT_LIMIT):
    """A JSON-safe description of a value that may be astronomically large.

    Every API and UI surface reports numbers through this, so none of them can
    reintroduce the float/str overflows that bounded rendering exists to stop.
    """
    text, truncated, digits = to_exact_str(x, limit)
    return {
        "text": text,
        "truncated": truncated,
        "digits": digits,
        "decimal": to_decimal(x),
        "log10": log10_abs(x),
    }


def to_exact_str(x, limit=DIGIT_LIMIT):
    """Render x exactly when it fits, else in scientific notation.

    Returns ``(text, truncated, digits)``. When ``truncated`` is True the text
    is an approximation of a value that is still exact in memory — only the
    rendering was bounded.
    """
    if isinstance(x, float):
        return "%.12g" % x, False, digit_count(x)

    f = as_fraction(x)
    num_digits = _int_digits(f.numerator)
    den_digits = _int_digits(f.denominator)
    if num_digits <= limit and den_digits <= limit:
        return str(f), False, num_digits

    lg = log10_abs(f)
    if lg is None:
        return "0", False, 1
    exponent = math.floor(lg)
    mantissa = 10.0 ** (lg - exponent)
    sign = "-" if f < 0 else ""
    return "%s%.10fe%+d" % (sign, mantissa, exponent), True, num_digits
