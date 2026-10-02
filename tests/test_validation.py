import math

import pytest

from iol_calc import BiometryError, srk1_power, srkt_power, vergence_power
from iol_calc.cli import main


@pytest.mark.parametrize("al", [17.9, 35.1, -1.0, 0.0])
def test_axial_length_out_of_range(al):
    with pytest.raises(BiometryError, match="axial_length"):
        srkt_power(al, 44.0, 118.4)


def test_axial_length_in_cm_is_caught():
    with pytest.raises(BiometryError, match="centimetres"):
        srkt_power(2.35, 44.0, 118.4)


@pytest.mark.parametrize("k", [34.9, 55.1])
def test_keratometry_out_of_range(k):
    with pytest.raises(BiometryError, match="keratometry"):
        srk1_power(23.5, k, 118.4)


def test_corneal_radius_entered_instead_of_k_is_caught():
    with pytest.raises(BiometryError, match="radius"):
        srkt_power(23.5, 7.7, 118.4)


@pytest.mark.parametrize("a", [100.0, 130.0])
def test_a_constant_out_of_range(a):
    with pytest.raises(BiometryError, match="a_constant"):
        srkt_power(23.5, 44.0, a)


@pytest.mark.parametrize("bad", [None, "23.5", math.nan, math.inf, True])
def test_non_numeric_inputs_rejected(bad):
    with pytest.raises(BiometryError):
        srkt_power(bad, 44.0, 118.4)


def test_elp_out_of_range():
    with pytest.raises(BiometryError, match="elp"):
        vergence_power(23.5, 44.0, 9.0)


def test_cli_ok(capsys):
    assert main(["--al", "23.5", "--k", "44", "--a", "118.4"]) == 0
    assert "SRK/T power" in capsys.readouterr().out


def test_cli_bad_input(capsys):
    assert main(["--al", "2.35", "--k", "44", "--a", "118.4"]) == 2
    assert "centimetres" in capsys.readouterr().err
