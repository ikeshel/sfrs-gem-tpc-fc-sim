"""Load field coordinates in mm, including explicitly labelled legacy cm CSVs."""
import numpy as np


def load_field_csv(path):
    data = np.atleast_1d(np.genfromtxt(path, delimiter=',', names=True))
    names = set(data.dtype.names or ())
    mm = {f'{axis}_mm' for axis in 'xyz'}
    cm = {f'{axis}_cm' for axis in 'xyz'}
    if mm <= names and not names.intersection(cm):
        return data
    if cm <= names and not names.intersection(mm):
        for name in cm:
            data[name] *= 10
        data.dtype.names = tuple(name.replace('_cm', '_mm') if name in cm else name
                                for name in data.dtype.names)
        print('Legacy CSV: converting coordinate columns from cm to mm; fields remain V/cm.')
        return data
    raise ValueError('CSV must contain exactly one complete coordinate set: x_mm/y_mm/z_mm or legacy x_cm/y_cm/z_cm')
