#specgrid class
from scipy import interpolate
import numpy as np
try:
    from pyspec import oned
    pyspec_available = True
except ImportError:
    pyspec_available = False

import pandas as pd
import os
import h5py
from astropy import units as u

from astropy import modeling

from fix_spectrum1d import Spectrum1D


class BaseSpectralGrid(object):
    """
    A BaseSpectralGrid interpolation class. Can serve as a model maybe

    Parameters
    ----------

    grid_hdf5_fname: filename for HDF5 File
    """

    parameters = None

    def __init__(self, grid_hdf5_fname,
                 interpolator=interpolate.LinearNDInterpolator):

        super(BaseSpectralGrid, self).__init__()

        if not os.path.exists(grid_hdf5_fname):
            raise IOError('{0} does not exists'.format(grid_hdf5_fname))

        self._load_index(grid_hdf5_fname)
        self._load_fluxes(grid_hdf5_fname)


        self.interpolate_grid = interpolator(self.index.values, self.fluxes)
        self.interpolator = interpolator

    def __call__(self):
        return Spectrum1D.from_array(self.wavelength, self._interpolate_flux())

    def _interpolate_flux(self):
        parameter_values = [getattr(self, item) for item in self.parameters]
        return self.interpolate_grid(parameter_values)[0] * self.flux_unit

    def _load_index(self, grid_hdf5_fname):
        """
        Loading the index from the hdf5 file

        Parameters
        ----------

        grid_hdf5_fname: ~str
            path to HDF5 file
        """

        self.index = pd.read_hdf(grid_hdf5_fname, 'index')

        self.parameters = self.index.columns

        for parameter_name in self.parameters:
            setattr(self, parameter_name, self.index[parameter_name].iloc[0])

    def _load_fluxes(self, grid_hdf5_fname):
        """
        Loading the fluxes from the HDF5 file

        Parameters
        ----------

        grid_hdf5_fname: ~str
            path to HDF5 file

        """

        with h5py.File(grid_hdf5_fname, 'r') as h5file:
            wavelength_unit = u.Unit(h5file['fluxes'].attrs['wavelength.unit'])
            self.wavelength = h5file['fluxes'].attrs['wavelength'] * \
                              wavelength_unit
            self.flux_unit = u.Unit(h5file['fluxes'].attrs['flux.unit'])
            self.fluxes = np.array(h5file['fluxes'])

    def evaluate(self, **kwargs):
        """
        Interpolating on the grid to the necessary parameters
        """

        for key in kwargs:
            if key not in self.parameters:
                raise ValueError('{0} not a parameter of the current '
                                 'spectral grid (parameters are {1})'.format(
                    key, ','.join(self.parameters)))
            setattr(self, key, kwargs[key])

        return self.__call__()

