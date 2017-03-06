"""Test XCOM data queries."""

from __future__ import print_function
import unittest
from becquerel.tools import xcom

# pylint: disable=protected-access,too-many-public-methods
XCOM_URL_ORIG = xcom._URL


class XCOMQueryTests(unittest.TestCase):
    """Test XCOM queries."""

    def test_01(self):
        """Test XCOMQuery with symbol and one energy......................."""
        energies = [1460.]
        xd = xcom.XCOMQuery('Ge', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_02(self):
        """Test XCOMQuery with symbol and three energies..................."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('Ge', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_03(self):
        """Test XCOMQuery with uppercase symbol and three energies........."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('GE', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_04(self):
        """Test XCOMQuery with lowercase symbol and three energies........."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('ge', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_05(self):
        """Test XCOMQuery with z (integer) and three energies.............."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery(32, energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_06(self):
        """Test XCOMQuery with z (string) and three energies..............."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('32', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_07(self):
        """Test XCOMQuery with chemical compound (H2O) and three energies.."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('H2O', energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_08(self):
        """Test XCOMQuery with mixture and three energies.................."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery(['H2O 0.9', 'NaCl 0.1'], energies=energies)
        self.assertTrue(len(xd) == len(energies))

    def test_09(self):
        """Test XCOMQuery with three energies and standard energy grid....."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('Ge', energies=energies, e_range=[1., 10000.])
        self.assertTrue(len(xd) > len(energies))

    def test_10(self):
        """Test XCOMQuery for predefined mixtures.........................."""
        energies = [60., 662., 1460.]
        mixtures = [key for key in dir(xcom) if key.startswith('MIXTURE')]
        for mixture in mixtures:
            xd = xcom.XCOMQuery(getattr(xcom, mixture), energies=energies)
            self.assertTrue(len(xd) == len(energies))

    def test_11(self):
        """Test XCOMQuery raises exception if z is out of range............"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery(130, energies=[60., 662., 1460.])

    def test_12(self):
        """Test XCOMQuery raises exception for badly formed mixture (1)...."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery(['H2O 0.9', 'NaCl'], energies=[60., 662., 1460.])

    def test_13(self):
        """Test XCOMQuery raises exception for badly formed mixture (2)...."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery(['H2O 1 1', 'NaCl 1'], energies=[60., 662., 1460.])

    def test_14(self):
        """Test XCOMQuery raises exception if given bad argument..........."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery(None, energies=[60., 662., 1460.])

    def test_15(self):
        """Test XCOMQuery raises exception if no energies are requested...."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge')

    def test_16(self):
        """Test XCOMQuery raises exception if website not found............"""
        xcom._URL = 'http://httpbin.org/status/404'
        with self.assertRaises(xcom.XCOMRequestError):
            xcom.XCOMQuery('Ge', energies=[60., 662., 1460.])
        xcom._URL = XCOM_URL_ORIG

    def test_17(self):
        """Test XCOMQuery raises exception if data from website is empty..."""
        xcom._URL = 'http://httpbin.org/post'
        with self.assertRaises(xcom.XCOMRequestError):
            xcom.XCOMQuery('Ge', energies=[60., 662., 1460.])
        xcom._URL = XCOM_URL_ORIG

    def test_18(self):
        """Test XCOMQuery instantiated with perform=False.................."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('Ge', energies=energies, perform=False)
        xd.perform()
        self.assertTrue(len(xd) == len(energies))

    def test_19(self):
        """Test XCOMQuery instantiated with perform=False, update called..."""
        energies = [60., 662., 1460.]
        xd = xcom.XCOMQuery('Ge', perform=False)
        xd.update(energies=energies)
        xd.perform()
        self.assertTrue(len(xd) == len(energies))

    def test_20(self):
        """Test XCOMQuery raises exception if energies not iterable........"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', energies=1460.)

    def test_21(self):
        """Test XCOMQuery raises exception if energies out of range (low).."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', energies=[60., 662., 1460., 0.001])

    def test_22(self):
        """Test XCOMQuery raises exception if energies out of range (high)."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', energies=[60., 662., 1460., 1e9])

    def test_23(self):
        """Test XCOMQuery raises exception if e_range not an iterable......"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=100.)

    def test_24(self):
        """Test XCOMQuery raises exception if len(e_range) != 2............"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=[1., 10000., 100000.])

    def test_25(self):
        """Test XCOMQuery raises exception if e_range[0] is out of range..."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=[0.1, 10000.])

    def test_26(self):
        """Test XCOMQuery raises exception if e_range[1] is out of range..."""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=[0.1, 1e9])

    def test_27(self):
        """Test XCOMQuery raises exception if e_range is out of order......"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=[1000., 1.])

    def test_28(self):
        """Test XCOMQuery raises exception if bad keyword given............"""
        with self.assertRaises(xcom.XCOMInputError):
            xcom.XCOMQuery('Ge', e_range=[1., 10000.], bad_keyword=None)


def main():
    """Run unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()
