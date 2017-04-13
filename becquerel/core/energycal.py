""""Energy calibration classes"""

from abc import ABCMeta, abstractmethod, abstractproperty
from future.utils import viewitems
from builtins import dict, super, zip  # pylint: disable=redefined-builtin
from uncertainties import unumpy
import numpy as np
from becquerel.core import handle_unc, handle_uncs


class EnergyCalError(Exception):
    """Base class for errors in energycal.py"""

    pass


class BadInput(EnergyCalError):
    """Error related to energy cal input"""

    pass


class EnergyCalBase(object):
    """Abstract base class for energy calibration.

    Subclasses must implement:
      _ch2kev (method)
      kev2ch (method)
      valid_coeffs (property)
      _perform_fit (method)
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        """Create an empty calibration instance.

        Normally you should use from_points or from_coeffs classmethods.

        Args:
          none
        """

        self._calpoints = dict()
        self._coeffs = dict()
        # initialize fit constraints?

    @classmethod
    def from_points(cls, chlist=None, ch_uncs=None, kevlist=None,
                    pairlist=None):
        """Construct EnergyCal from calibration points.

        Specify either pairlist, or (chlist and kevlist).

        Args:
          chlist: list/tuple/array of the channel values of calibration points.
            may be specified as UFloats
          ch_uncs (optional): list/tuple/array of uncertainties of the
            channel values
          kevlist: list/tuple/array of the corresponding energy values [keV]
          pairlist: list/tuple/array of paired values, (ch, kev)

        Raises:
          BadInput: for bad pairlist, chlist, and/or kevlist.
        """

        # np.arrays don't cast to bool like lists and tuples
        if isinstance(pairlist, np.ndarray):
            has_pair = bool(len(pairlist))
        else:
            has_pair = bool(pairlist)
        if isinstance(chlist, np.ndarray):
            has_ch = bool(len(chlist))
        else:
            has_ch = bool(chlist)
        if isinstance(kevlist, np.ndarray):
            has_kev = bool(len(kevlist))
        else:
            has_kev = bool(kevlist)

        if has_pair and (has_ch or has_kev):
            raise BadInput('Redundant calibration inputs')
        if (has_ch and not has_kev) or (has_kev and not has_ch):
            raise BadInput('Require both chlist and kevlist')
        if not has_ch and not has_kev and not has_pair:
            raise BadInput('Calibration points are required')
        if has_ch and has_kev:
            if (not isinstance(chlist, (list, tuple, np.ndarray)) or
                    not isinstance(kevlist, (list, tuple, np.ndarray))):
                raise BadInput('Inputs should be iterables, not scalars')
            if len(chlist) != len(kevlist):
                raise BadInput('Channels and energies must be same length')
            ch_array = handle_uncs(chlist, ch_uncs, lambda x: np.nan)
            pairlist = zip(ch_array, kevlist)
        elif not isinstance(pairlist[0], (list, tuple, np.ndarray)):
            raise BadInput('Inputs should be iterables, not scalars')

        cal = cls()

        for ch, kev in pairlist:
            cal.new_calpoint(ch, kev)

        return cal

    @classmethod
    def from_coeffs(cls, coeffs):
        """Construct EnergyCal from equation coefficients dict.

        Args:
          coeffs: a dict with keys equal to elements in valid_coeffs,
            and values specifying the value of the coefficient
        """

        cal = cls()

        for coeff, val in viewitems(coeffs):
            cal._set_coeff(coeff, val)

        # TODO make sure all coefficients are specified

        return cal

    @property
    def channels(self):
        """The channel values, with uncertainty, of calibration points.

        Returns:
          an np.ndarray of UFloat's
        """

        return np.array(list(self._calpoints.values()))

    @property
    def ch_vals(self):
        """The channel values (no uncertainty) of calibration points.

        Returns:
          an np.ndarray of floats or ints
        """

        return unumpy.nominal_values(self.channels)

    @property
    def ch_uncs(self):
        """The channel uncertainties of calibration points.

        Returns:
          an np.ndarray of floats
        """

        return unumpy.std_devs(self.channels)

    @property
    def energies(self):
        """The energy values of calibration points.

        Returns:
          an np.ndarray of energy values [keV]
        """

        return np.array(list(self._calpoints), dtype=float)

    @property
    def calpoints(self):
        """The calibration points, in (ch, kev) pairs.

        Returns:
          a list of 2-element tuples of (channel, energy[keV])
        """

        return list(zip(self.channels, self.energies))

    @property
    def coeffs(self):
        """The coefficients of the current calibration curve.

        Returns:
          a dict of {coeff: value}
        """

        # TODO: if there are no coeffs, error?
        return self._coeffs

    def add_calpoint(self, ch, kev, ch_unc=None):
        """Add a calibration point (ch, kev) pair. May be new or existing.

        Args:
          ch: the channel value of the calibration point
          kev: the energy value of the calibration point [keV]
        """

        ch_ufloat = handle_unc(ch, ch_unc, np.nan)
        self._calpoints[float(kev)] = ch_ufloat

    def new_calpoint(self, ch, kev, ch_unc=None):
        """Add a new calibration point. Error if energy matches existing point.

        Args:
          ch: the channel value of the calibration point
          kev: the energy value of the calibration point [keV]

        Raises:
          EnergyCalError: if energy value already exists in calibration
        """

        if kev in self._calpoints:
            raise EnergyCalError('Calibration energy already exists')
        self.add_calpoint(ch, kev, ch_unc=ch_unc)

    def rm_calpoint(self, kev):
        """Remove a calibration point, if it exists.

        Args:
          the energy value of the point to remove [keV]
        """

        if kev in self._calpoints:
            del self._calpoints[kev]
        # TODO erroring version?

    def ch2kev(self, ch):
        """Convert channel(s) to energy value(s).

        Args:
          ch: a scalar, np.array, list or tuple of channel values

        Returns:
          the energy value(s) corresponding to the channel value(s) [keV].
            a float if input is scalar. an np.array if input is iterable
        """

        if isinstance(ch, (list, tuple)):
            ch = np.array(ch)

        return self._ch2kev(ch)

    @abstractmethod
    def _ch2kev(self, ch):
        """Convert scalar OR np.array of channel(s) to energies.

        Should use numpy ufuncs so that the input dtype doesn't matter.

        Args:
          ch: an np.array, float, or int of channel values

        Returns:
          energy values, the same size/type as ch [keV]
        """

        pass

    def kev2ch(self, kev):
        """Convert energy value(s) to channel(s).

        Args:
          kev: a scalar, np.array, list or tuple of energy values [keV]

        Returns:
          the channel value(s) corresponding to the input energies.
            a float if input is scalar. an np.array if input is iterable
        """

        if isinstance(kev, (list, tuple)):
            kev = np.array(kev)

        return self._kev2ch(kev)

    @abstractmethod
    def _kev2ch(self, kev):
        """Convert energy value(s) to channel(s).

        Should use numpy ufuncs so that the input dtype doesn't matter.

        Args:
          kev: an np.array, float, or int of energy values [keV]

        Returns:
          the channel value(s) corresponding to the input energies.
            a float if input is scalar. an np.array if input is iterable
        """

        # if this is not possible, raise a NotImplementedError ?
        pass

    @abstractproperty
    def valid_coeffs(self):
        """A list of valid coefficients for the calibration curve.

        Returns:
          a tuple of strings, the names of the coefficients for this curve
        """

        pass

    def _set_coeff(self, name, val):
        """Set a coefficient for the calibration curve.

        Args:
          name: a string, the name of the coefficient to set
          val: the value to set the coefficient to

        Raises:
          EnergyCalError: if name is not in valid_coeffs
        """

        if name in self.valid_coeffs:
            self._coeffs[name] = val
        else:
            raise EnergyCalError('Invalid coefficient name: {}'.format(name))

    def update_fit(self):
        """Compute the calibration curve from the current points.

        Raises:
          EnergyCalError: if there are too few calibration points to fit
        """

        num_coeffs = len(self.valid_coeffs)
        # TODO: free coefficients, not all coefficients
        num_points = len(self._calpoints)

        if num_points == 0:
            raise EnergyCalError('No calibration points; cannot calibrate')
        elif num_points < num_coeffs:
            raise EnergyCalError('Not enough calibration points to fit curve')
        else:
            self._perform_fit()

    @abstractmethod
    def _perform_fit(self):
        """Do the actual curve fitting."""

        pass


class LinearEnergyCal(EnergyCalBase):
    """
    kev = b*ch + c
    """

    @classmethod
    def from_coeffs(cls, coeffs):
        """Construct LinearEnergyCal from equation coefficients dict.

        Valid coefficient names (slope, offset):
          ('b', 'c')
          ('p1', 'p0')
          ('slope', 'offset')
          ('m', 'b')

        Args:
          coeffs: a dict with keys equal to valid coeff names,
            and values specifying the value of the coefficient
        """

        new_coeffs = {}
        if 'p0' in coeffs and 'p1' in coeffs:
            new_coeffs['b'] = coeffs['p1']
            new_coeffs['c'] = coeffs['p0']
        elif 'slope' in coeffs and 'offset' in coeffs:
            new_coeffs['b'] = coeffs['slope']
            new_coeffs['c'] = coeffs['offset']
        elif 'm' in coeffs and 'b' in coeffs:
            new_coeffs['b'] = coeffs['m']
            new_coeffs['c'] = coeffs['b']
        else:
            new_coeffs = coeffs.copy()
        cal = super().from_coeffs(new_coeffs)
        return cal

    @property
    def valid_coeffs(self):
        """A list of valid coefficients for the calibration curve.

        Returns:
          a tuple of strings, the names of the coefficients for this curve
        """

        return ('b', 'c')

    @property
    def slope(self):
        """Return the slope coefficient value."""

        return self._coeffs['b']

    @property
    def offset(self):
        """Return the offset coefficient value."""

        return self._coeffs['c']

    def _ch2kev(self, ch):
        """Convert scalar OR np.array of channel(s) to energies.

        Should use numpy ufuncs so that the input dtype doesn't matter.

        Args:
          ch: an np.array, float, or int of channel values

        Returns:
          energy values, the same size/type as ch [keV]
        """

        return self.slope * ch + self.offset

    def _kev2ch(self, kev):
        """Convert energy value(s) to channel(s).

        Args:
          kev: an np.array, float, or int of energy values [keV]

        Returns:
          the channel value(s) corresponding to the input energies.
            a float if input is scalar. an np.array if input is iterable
        """

        return (kev - self.offset) / self.slope

    def _perform_fit(self):
        """Do the actual curve fitting.

        If some points have uncertainty and others don't, the points without
        are assigned the average uncertainty of the points with.
        """

        # normally channel is the independent variable.
        # but uncertainty is on channel, not energy. so fit the inverse
        x = self.energies
        y = unumpy.nominal_values(self.channels)
        sig = unumpy.std_devs(self.channels)
        nan_weights = np.isnan(sig)
        if nan_weights.all():
            sig = np.ones_like(nan_weights)
        if nan_weights.any():
            sig[nan_weights] = np.nanmean(sig)
        # w = 1/sigma rather than 1/sigma**2, as per np.polyfit docs
        slope_inverse, offset_inverse = np.polyfit(x, y, 1, w=1/sig)
        slope = 1 / slope_inverse
        offset = -offset_inverse / slope_inverse
        self._set_coeff('b', slope)
        self._set_coeff('c', offset)
