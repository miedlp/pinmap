# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

from pinmap.util import dependencyCheck as DEPENDENCY_CHECK

class StandardStrings:
    __slots__ = ()
    NOT_AVAILABLE        = 'N/A'
    NOT_CONNECTED        = 'N/C'
    PREFIX_USED          = 'USED@'
    PREFIX_SHARED        = 'SHARED-'
    STATUS_OPEN          = 'Open'
    STATUS_CLOSED        = 'Closed'
    STATUS_OPEN_SYMBOL   = '_\_'
    STATUS_CLOSED_SYMBOL = ''
    SUPPLY_5V_LABEL      = '5V'
    SUPPLY_3V3_LABEL     = '3V3'
    SUPPLY_GND_LABEL     = 'GND'

DEPENDENCY_CHECK(["jupyter", "numpy", "pandas", "ipywidgets", "pyarrow", "reportlab", "ipydatagrid"])

__all__ = ("Adapter")
