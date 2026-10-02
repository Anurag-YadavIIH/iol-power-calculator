"""IOL power formulas.

All lengths are in millimetres, powers in dioptres.

References
----------
- Thin-lens vergence: standard paraxial optics (e.g. Holladay, "Standardizing
  constants for ultrasonic biometry, keratometry, and intraocular lens power
  calculations", J Cataract Refract Surg 1997).
- SRK I: Sanders, Retzlaff, Kraff, "Comparison of the SRK II formula and other
  second generation formulas", J Cataract Refract Surg 1988.
- SRK/T: original source is Retzlaff, Sanders, Kraff, "Development of the SRK/T
  intraocular lens implant power calculation formula", J Cataract Refract Surg
  1990;16:333-340 (erratum 1990;16:528). This implementation follows the
  equations as written out step by step in "T2 formula in a highly myopic
  population, comparison with other methods and description of an improved
  approach for estimating corneal height" (PMC6849235,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6849235/). It has not been checked
  line by line against the 1990 paper or its erratum.

LEARNING TOOL ONLY. Not validated against clinical outcomes. Not for clinical use.
"""

import math

from .validation import (
    BiometryError,
    validate_a_constant,
    validate_axial_length,
    validate_elp,
    validate_keratometry,
    validate_target_refraction,
    validate_vertex_distance,
)

N_AQUEOUS = 1.336        # refractive index of aqueous and vitreous
N_CORNEA_SRKT = 1.333    # "fictitious" corneal index used by SRK/T
DEFAULT_VERTEX_MM = 12.0


def _refraction_at_cornea(refraction, vertex_mm):
    """Move a spectacle-plane refraction to the corneal plane."""
    return refraction / (1 - (vertex_mm / 1000.0) * refraction)


def vergence_power(axial_length, keratometry, elp,
                   target_refraction=0.0, vertex_distance=DEFAULT_VERTEX_MM):
    """Thin-lens vergence IOL power.

    P = n / (AL - ELP) - n / (n / (K + R_c) - ELP)

    with n = 1336 when lengths are in mm, and R_c the target refraction
    moved to the corneal plane.
    """
    al = validate_axial_length(axial_length)
    k = validate_keratometry(keratometry)
    d = validate_elp(elp)
    rx = validate_target_refraction(target_refraction)
    v = validate_vertex_distance(vertex_distance)

    if d >= al:
        raise BiometryError("ELP must be smaller than the axial length")

    n = N_AQUEOUS * 1000.0
    corneal_vergence = k + _refraction_at_cornea(rx, v)
    image_distance = n / corneal_vergence  # mm, behind the cornea
    if image_distance <= d:
        raise BiometryError("Inputs give an image in front of the IOL plane")

    return n / (al - d) - n / (image_distance - d)


def srk1_power(axial_length, keratometry, a_constant):
    """SRK I regression formula for emmetropia: P = A - 2.5 AL - 0.9 K."""
    al = validate_axial_length(axial_length)
    k = validate_keratometry(keratometry)
    a = validate_a_constant(a_constant)
    return a - 2.5 * al - 0.9 * k


def srkt_details(axial_length, keratometry, a_constant,
                 target_refraction=0.0, vertex_distance=DEFAULT_VERTEX_MM):
    """SRK/T power plus the intermediate values, as a dict.

    Returning the intermediates makes each step of the formula testable.

    Deliberate departure from standard implementations: when
    r^2 - Cw^2 / 4 is negative (very steep K with a very long eye), the corneal
    height is undefined. Standard implementations clamp that value to 0 and
    carry on. This function raises BiometryError instead of returning a number.
    """
    al = validate_axial_length(axial_length)
    k = validate_keratometry(keratometry)
    a = validate_a_constant(a_constant)
    rx = validate_target_refraction(target_refraction)
    v = validate_vertex_distance(vertex_distance)

    na = N_AQUEOUS
    ncm1 = N_CORNEA_SRKT - 1.0

    # Corneal radius from K (keratometric index 1.3375)
    r = 337.5 / k

    # Long-eye correction of axial length, used only for corneal width
    if al <= 24.2:
        lcor = al
    else:
        lcor = -3.446 + 1.716 * al - 0.0237 * al ** 2

    # Corneal width and corneal dome height.
    # The original paper is commonly cited with the rounded constant -5.41.
    # -5.40948 matches the later step-by-step write-ups (PMC6849235). The
    # difference changes the IOL power by less than 0.001 D.
    cw = -5.40948 + 0.58412 * lcor + 0.098 * k
    under_root = r ** 2 - (cw ** 2) / 4.0
    if under_root < 0:
        # Standard implementations clamp this to 0. We refuse instead.
        raise BiometryError("Corneal height undefined for these K and AL values")
    h = r - math.sqrt(under_root)

    # A-constant to ACD constant, then ELP
    acd_const = 0.62467 * a - 68.747
    offset = acd_const - 3.336
    elp = h + offset

    # Retinal thickness correction gives the optical axial length
    rethick = 0.65696 - 0.02029 * al
    lopt = al + rethick

    vm = v  # vertex distance in mm, as in the published equations
    num = 1000 * na * (na * r - ncm1 * lopt - 0.001 * rx * (vm * (na * r - ncm1 * lopt) + lopt * r))
    den = (lopt - elp) * (na * r - ncm1 * elp - 0.001 * rx * (vm * (na * r - ncm1 * elp) + elp * r))
    power = num / den

    return {
        "power": power,
        "corneal_radius": r,
        "lcor": lcor,
        "corneal_width": cw,
        "corneal_height": h,
        "acd_constant": acd_const,
        "elp": elp,
        "retinal_thickness": rethick,
        "optical_axial_length": lopt,
    }


def srkt_power(axial_length, keratometry, a_constant,
               target_refraction=0.0, vertex_distance=DEFAULT_VERTEX_MM):
    """SRK/T IOL power in dioptres."""
    return srkt_details(axial_length, keratometry, a_constant,
                        target_refraction, vertex_distance)["power"]
