import unittest

import numpy as np

from pyowt.OpticalVariables import OpticalVariables


class TestNumpyTrapezoidCompat(unittest.TestCase):

    def test_calculate_area_uses_trapezoid_when_trapz_is_unavailable(self):
        band = np.arange(400, 801)
        Rrs = np.ones(len(band))

        ov = OpticalVariables(Rrs=Rrs, band=band)

        self.assertEqual(ov.Area.shape, (1, 1))
        self.assertAlmostEqual(ov.Area[0, 0], 222.0)

    def test_calculate_area_falls_back_to_trapz_when_trapezoid_is_unavailable(self):
        band = np.arange(400, 801)
        Rrs = np.ones(len(band))
        original_trapezoid = getattr(np, "trapezoid", None)
        original_trapz = getattr(np, "trapz", None)

        def trapz_fallback(y, x=None, dx=1.0, axis=-1):
            return np.sum((y[..., 1:] + y[..., :-1]) * np.diff(x) / 2.0, axis=axis)

        try:
            if original_trapezoid is not None:
                delattr(np, "trapezoid")
            np.trapz = trapz_fallback

            ov = OpticalVariables(Rrs=Rrs, band=band)

            self.assertEqual(ov.Area.shape, (1, 1))
            self.assertAlmostEqual(ov.Area[0, 0], 222.0)
        finally:
            if original_trapezoid is not None:
                np.trapezoid = original_trapezoid
            if original_trapz is not None:
                np.trapz = original_trapz
            elif hasattr(np, "trapz"):
                delattr(np, "trapz")


if __name__ == "__main__":
    unittest.main()
