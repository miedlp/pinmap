# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import ipywidgets as widgets

class PinSelector(widgets.Dropdown):
    """Element consisting of a ipywidget.Label and ipywidget.Dropdown which allows to select the MCU-Pin
    which should be mapped to a EDB-Pin."""
    def __init__(self, *args, **kwargs):
        super(PinSelector, self).__init__(*args, **kwargs)
        self._mappingIdx = kwargs.get('mappingIdx')
        self._parent     = kwargs.get('parent')
        self._previous   = kwargs.get('previous', None)
        self._next       = kwargs.get('next', None)
        self.fullLabel   = kwargs.get('fullLabel')

    @property
    def mappingIdx(self) -> int:
        if not hasattr(self, '_mappingIdx'):
            raise Exception('mappingIdx not set by constructor of PinSelector object')
        return self._mappingIdx

    @property
    def parent(self) -> object:
        if not hasattr(self, '_parent'):
            raise Exception('parent Adapter not set by constructor of PinSelector object')
        return self._parent

    @property
    def fullLabel(self) -> str:
        return getattr(self, '_fullLabel', '')

    @property
    def previous(self) -> object:
        return getattr(self, '_previous', None)

    @previous.setter
    def previous(self, value: object) -> None:
        self._previous = value

    @property
    def next(self) -> object:
        return getattr(self, '_next', None)

    @next.setter
    def next(self, value: object) -> None:
        self._next = value

    @fullLabel.setter
    def fullLabel(self, value: str) -> None:
        self._fullLabel = value

class ClearButton(widgets.Button):
    """Element consisting of a ipywidget.Label and ipywidget.Dropdown which allows to select the MCU-Pin
    which should be mapped to a EDB-Pin."""
    def __init__(self, *args, **kwargs):
        super(ClearButton, self).__init__(*args, **kwargs)
        self._bus    = kwargs.get('bus')
        self._parent = kwargs.get('parent')

    @property
    def bus(self) -> str:
        if not hasattr(self, '_bus'):
            raise Exception('Bus not set by constructor of ClearButton object')
        return self._bus

    @property
    def parent(self) -> object:
        if not hasattr(self, '_parent'):
            raise Exception('parent Adapter not set by constructor of ClearButton object')
        return self._parent
