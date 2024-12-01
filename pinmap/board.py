# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

class Board(object):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize a Board object.


        Parameters
        ---------
        vendor   : Vendor of the board, e.g. EA. Defaults to >ACME<.
        name     : Name of the  board, e.g. IMXRT1062OEM. Defaults to >Plank<.
        revision : Revision of the board, defaults to >A<.
        """
        self._initkwargs = kwargs

    @property
    def vendor(self) -> str:
        """Vendor of the board."""
        if not hasattr(self, '_vendor'):
          self._vendor = self._initkwargs.pop('vendor', 'ACME')
        return self._vendor

    @vendor.setter
    def vendor(self, value: str) -> None:
        self._initkwargs.pop('revision', '')
        self._vendor = value

    @property
    def longname(self) -> str:
        """Long name of the board."""
        if not hasattr(self, '_longname'):
          self._longname = self._initkwargs.pop('longname', 'Plank')
        return self._longname

    @longname.setter
    def longname(self, value: str) -> None:
        self._initkwargs.pop('longname', '')
        self._longname = value

    @property
    def shortname(self) -> str:
        """Short name of the board."""
        if not hasattr(self, '_shortname'):
          self._shortname = self._initkwargs.pop('shortname', 'PLK')
        return self._shortname

    @shortname.setter
    def shortname(self, value: str) -> None:
        self._initkwargs.pop('shortname', '')
        self._shortname = value

    @property
    def revision(self) -> str:
        """Revision of the board."""
        if not hasattr(self, '_revision'):
          self._revision = self._initkwargs.pop('revision', 'A')
        return self._revision

    @revision.setter
    def name(self, value: str) -> None:
        self._initkwargs.pop('revision', '')
        self._revision = value
