"""Input checks for biometry values.

Every formula in this package calls these checks before doing any arithmetic.
The ranges are deliberately generous: they reject values that are almost
certainly typos or unit mistakes, not unusual but real eyes.
"""

import math

# (low, high, unit) for each input
RANGES = {
    "axial_length": (18.0, 35.0, "mm"),
    "keratometry": (35.0, 55.0, "D"),
    "a_constant": (110.0, 125.0, ""),
    "elp": (2.0, 8.0, "mm"),
    "target_refraction": (-10.0, 10.0, "D"),
    "vertex_distance": (0.0, 20.0, "mm"),
}


class BiometryError(ValueError):
    """Raised when an input is missing, not a number, or implausible."""


def _check_number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BiometryError(f"{name} must be a number, got {type(value).__name__}")
    if math.isnan(value) or math.isinf(value):
        raise BiometryError(f"{name} must be a finite number, got {value}")
    return float(value)


def check_range(name, value):
    """Check a value against RANGES[name] and return it as a float."""
    value = _check_number(name, value)
    low, high, unit = RANGES[name]
    if not (low <= value <= high):
        raise BiometryError(
            f"{name} = {value} {unit} is outside the plausible range "
            f"{low} to {high} {unit}"
        )
    return value


def validate_axial_length(al):
    al = _check_number("axial_length", al)
    if 1.5 <= al <= 3.6:
        raise BiometryError(
            f"axial_length = {al} looks like centimetres. Enter it in mm "
            f"(for example {al * 10:.2f})."
        )
    return check_range("axial_length", al)


def validate_keratometry(k):
    k = _check_number("keratometry", k)
    if 6.0 <= k <= 10.0:
        raise BiometryError(
            f"keratometry = {k} looks like a corneal radius in mm. "
            f"Convert with K = 337.5 / r (here {337.5 / k:.2f} D)."
        )
    return check_range("keratometry", k)


def validate_a_constant(a):
    return check_range("a_constant", a)


def validate_elp(elp):
    return check_range("elp", elp)


def validate_target_refraction(r):
    return check_range("target_refraction", r)


def validate_vertex_distance(v):
    return check_range("vertex_distance", v)
