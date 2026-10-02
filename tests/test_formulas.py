import math

import pytest

from iol_calc import BiometryError, srk1_power, srkt_details, srkt_power, vergence_power

# A typical normal eye used across tests
AL, K, A = 23.5, 44.0, 118.4


# ---------- SRK I ----------

def test_srk1_matches_hand_calculation():
    # 118.4 - 2.5*23.5 - 0.9*44.0 = 118.4 - 58.75 - 39.6 = 20.05
    assert srk1_power(AL, K, A) == pytest.approx(20.05, abs=1e-9)


def test_srk1_second_hand_calculation():
    # AL 22.0, K 45.0, A 118.7
    # 118.7 - 2.5*22.0 - 0.9*45.0 = 118.7 - 55.0 - 40.5 = 23.2
    assert srk1_power(22.0, 45.0, 118.7) == pytest.approx(23.2, abs=1e-9)


# ---------- Vergence ----------

def test_vergence_hand_calculation():
    # n = 1336; AL 23.5, ELP 5.0, K 44, emmetropia
    expected = 1336 / (23.5 - 5.0) - 1336 / (1336 / 44.0 - 5.0)
    assert vergence_power(AL, K, 5.0) == pytest.approx(expected, rel=1e-12)


def test_vergence_second_hand_calculation():
    # AL 24.0, K 43.0, ELP 5.5, emmetropia, n = 1336
    # 1336 / (24.0 - 5.5)          = 1336 / 18.5    = 72.2162
    # 1336 / 43.0                  = 31.0698 mm (image distance)
    # 1336 / (31.0698 - 5.5)       = 1336 / 25.5698 = 52.2492
    # P = 72.2162 - 52.2492        = 19.967 D
    assert vergence_power(24.0, 43.0, 5.5) == pytest.approx(19.967, abs=0.001)


def test_vergence_myopic_target_needs_more_power():
    # Aiming for -1 D (slightly myopic) needs a stronger IOL than emmetropia
    assert vergence_power(AL, K, 5.0, target_refraction=-1.0) > vergence_power(AL, K, 5.0)


def test_vergence_short_eye_deep_elp_still_finite():
    # Shortest allowed eye with deepest allowed ELP must not divide by zero
    assert math.isfinite(vergence_power(18.0, 55.0, 8.0))


def test_vergence_rejects_implausible_elp():
    with pytest.raises(BiometryError):
        vergence_power(AL, K, 1.0)


# ---------- SRK/T ----------

def test_srkt_intermediates_follow_the_published_equations():
    # Equations as written out in PMC6849235
    d = srkt_details(AL, K, A)
    r = 337.5 / K
    assert d["corneal_radius"] == pytest.approx(r)
    assert d["lcor"] == AL                           # no long-eye correction at 23.5 mm
    cw = -5.40948 + 0.58412 * AL + 0.098 * K
    assert d["corneal_width"] == pytest.approx(cw)
    assert d["corneal_height"] == pytest.approx(r - math.sqrt(r ** 2 - cw ** 2 / 4))
    assert d["acd_constant"] == pytest.approx(0.62467 * A - 68.747)
    assert d["optical_axial_length"] == pytest.approx(AL + 0.65696 - 0.02029 * AL)


def test_srkt_target_zero_equals_emmetropia_formula():
    d = srkt_details(AL, K, A)
    na, ncm1 = 1.336, 0.333
    r, lopt, elp = d["corneal_radius"], d["optical_axial_length"], d["elp"]
    emme = 1000 * na * (na * r - ncm1 * lopt) / ((lopt - elp) * (na * r - ncm1 * elp))
    assert d["power"] == pytest.approx(emme, rel=1e-12)


def test_srkt_normal_eye_in_expected_range():
    # A normal eye with a standard A-constant should need roughly 19 to 23 D
    assert 19.0 < srkt_power(AL, K, A) < 23.0


def test_srkt_close_to_srk1_for_average_eye():
    # The regression and theoretical formulas agree within about 1 D for average eyes
    assert abs(srkt_power(AL, K, A) - srk1_power(AL, K, A)) < 1.0


def test_srkt_long_eye_correction_is_continuous_at_24_2():
    below = srkt_power(24.2, K, A)
    above = srkt_power(24.2001, K, A)
    assert abs(below - above) < 0.01


def test_srkt_long_eye_uses_lcor():
    d = srkt_details(28.0, K, A)
    assert d["lcor"] == pytest.approx(-3.446 + 1.716 * 28.0 - 0.0237 * 28.0 ** 2)


@pytest.mark.parametrize("al", [20.0, 22.0, 26.0, 30.0])
def test_srkt_boundary_eyes_give_finite_power(al):
    p = srkt_power(al, K, A)
    assert math.isfinite(p)
    assert -10 < p < 40


def test_srkt_refuses_undefined_corneal_height():
    # K 55, AL 34: Cw^2 / 4 exceeds r^2. Standard implementations clamp to 0;
    # this package raises instead of returning a number.
    with pytest.raises(BiometryError, match="Corneal height"):
        srkt_power(34.0, 55.0, A)


def test_srkt_higher_a_constant_gives_higher_power():
    assert srkt_power(AL, K, 119.0) > srkt_power(AL, K, 118.0)


# ---------- Monotonicity (property-style) ----------

@pytest.mark.parametrize("formula", [
    lambda al, k: srkt_power(al, k, A),
    lambda al, k: srk1_power(al, k, A),
    lambda al, k: vergence_power(al, k, 5.0),
])
def test_power_falls_as_axial_length_rises(formula):
    powers = [formula(al, K) for al in [21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 28.0]]
    assert all(a > b for a, b in zip(powers, powers[1:]))


@pytest.mark.parametrize("formula", [
    lambda al, k: srkt_power(al, k, A),
    lambda al, k: srk1_power(al, k, A),
    lambda al, k: vergence_power(al, k, 5.0),
])
def test_power_falls_as_keratometry_rises(formula):
    powers = [formula(AL, k) for k in [40.0, 42.0, 44.0, 46.0, 48.0]]
    assert all(a > b for a, b in zip(powers, powers[1:]))
