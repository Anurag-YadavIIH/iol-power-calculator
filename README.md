# IOL Power Calculator

[![tests](https://github.com/Anurag-YadavIIH/iol-power-calculator/actions/workflows/tests.yml/badge.svg)](https://github.com/Anurag-YadavIIH/iol-power-calculator/actions/workflows/tests.yml)

A small, tested Python package that calculates intraocular lens (IOL) power for cataract surgery using three formulas:

| Formula | Type | Notes |
|---|---|---|
| Thin-lens vergence | Theoretical | You supply the effective lens position (ELP). Supports a target refraction. |
| SRK I | Regression | `P = A - 2.5 AL - 0.9 K`. Emmetropia only. Included for teaching. |
| SRK/T | Theoretical / empirical | Follows the equations as written out step by step in PMC6849235 (original formula: Retzlaff et al. 1990), with corneal height, retinal thickness correction and long-eye axial length correction. Supports a target refraction. |

> **Learning tool only. Not for clinical use.** The formulas are checked against hand calculations and the published equations, not against independent worked examples or post-operative patient outcomes.

## Quick start

```bash
git clone https://github.com/Anurag-YadavIIH/iol-power-calculator.git
cd iol-power-calculator
pip install -e ".[dev]"
pytest -v
```

Command line:

```bash
iol-calc --al 23.5 --k 44 --a 118.4
# SRK/T power : 20.04 D  (ELP 5.19 mm)
# SRK I power : 20.05 D  (emmetropia only)
```

Python:

```python
from iol_calc import srkt_power, srkt_details, vergence_power

srkt_power(23.5, 44.0, 118.4)                          # 20.04 D
srkt_power(23.5, 44.0, 118.4, target_refraction=-0.5)  # aim slightly myopic
srkt_details(23.5, 44.0, 118.4)                        # every intermediate value
vergence_power(23.5, 44.0, elp=5.0)
```

## Inputs and units

| Input | Unit | Accepted range |
|---|---|---|
| Axial length (AL) | mm | 18 to 35 |
| Mean keratometry (K) | D | 35 to 55 |
| A-constant | | 110 to 125 |
| ELP (vergence only) | mm | 2 to 8 |
| Target refraction | D | -10 to +10 |
| Vertex distance | mm | 0 to 20 (default 12) |

Input checks raise a clear `BiometryError` instead of returning a wrong number. They also catch two common unit mistakes: axial length entered in centimetres (2.35 instead of 23.5) and corneal radius in mm entered instead of K in dioptres (7.7 instead of 43.8).

## How SRK/T is computed

The steps follow the equations as written out in [PMC6849235](https://pmc.ncbi.nlm.nih.gov/articles/PMC6849235/). The original formula is Retzlaff et al. 1990; the implementation has not been checked line by line against that paper or its erratum.

1. Corneal radius `r = 337.5 / K`
2. Long-eye correction: `LCOR = AL` if AL <= 24.2, else `-3.446 + 1.716 AL - 0.0237 AL^2`
3. Corneal width `Cw = -5.40948 + 0.58412 LCOR + 0.098 K` (the original paper is commonly cited with the rounded constant -5.41; the difference changes the IOL power by less than 0.001 D)
4. Corneal dome height `H = r - sqrt(r^2 - Cw^2 / 4)`. **Deliberate departure:** when `r^2 - Cw^2 / 4` is negative (very steep K with a very long eye, for example K 55 D and AL 34 mm), standard implementations clamp it to 0 and carry on. This package raises `BiometryError` and refuses to give a number.
5. `ACD const = 0.62467 A - 68.747`, `offset = ACD const - 3.336`, `ELP = H + offset`
6. Retinal thickness `RETHICK = 0.65696 - 0.02029 AL`, optical axial length `LOPT = AL + RETHICK`
7. Vergence equation with aqueous index 1.336 and corneal index 1.333

`srkt_details()` returns every one of these values, and the tests check each step separately.

## Tests

`pytest` runs 43 tests covering:

- **Hand calculations** for SRK I and vergence
- **Each SRK/T intermediate** against the published equations
- **Consistency**: SRK/T with target 0 equals the emmetropia form of the equation
- **Boundary eyes**: short (20 mm) to very long (30 mm), continuity at the 24.2 mm long-eye cutoff
- **Monotonicity**: power falls as AL rises and as K rises, for all three formulas
- **Input safety**: out-of-range values, NaN, wrong types, unit mistakes
- **CLI** behaviour and exit codes

Tests run on Python 3.9, 3.11 and 3.12 through GitHub Actions on every push.

## Validation notebook

`notebooks/validation.ipynb` has:

- A comparison table for reference values. No independent SRK/T reference value has been sourced yet, so every row is currently empty (see Roadmap)
- A sensitivity plot: roughly 3 D of IOL power error per 1 mm of axial length error for an average eye, which is why accurate biometry matters
- A comparison of the three formulas across axial lengths, showing where SRK I drifts from SRK/T in short and long eyes

## Limitations

- **Validation is against hand calculations and the published equations only.** There are no independent reference values yet and no clinical outcome data. Real validation means comparing predicted and actual post-operative refraction (mean absolute error, percentage within 0.5 D), which needs patient data.
- **No modern formulas** (Barrett Universal II, Hill-RBF, Kane, EVO) and no toric or post-refractive-surgery adjustments.
- **No lens constant optimisation.**
- **Not a medical device** and not intended for clinical decisions.

## Roadmap

- [ ] Add SRK/T reference values from an independent calculator or textbook, with source and access date.
- [ ] Holladay 1 and Hoffer Q
- [ ] A-constant optimisation from a sample outcome dataset
- [ ] Simple web front end

## References

- Retzlaff JA, Sanders DR, Kraff MC. Development of the SRK/T intraocular lens implant power calculation formula. *J Cataract Refract Surg.* 1990;16:333-340 (erratum 16:528). Original source of the formula.
- T2 formula in a highly myopic population, comparison with other methods and description of an improved approach for estimating corneal height. [PMC6849235](https://pmc.ncbi.nlm.nih.gov/articles/PMC6849235/). Source of the step-by-step equations this implementation follows.
- Sanders DR, Retzlaff J, Kraff MC. Comparison of the SRK II formula and other second generation formulas. *J Cataract Refract Surg.* 1988;14:136-141.

## License

MIT
