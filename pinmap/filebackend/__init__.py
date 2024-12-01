# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

class MappingColumnLabels():
    __slots__ = ()
    PINGRID_COLUMN = 'Column'
    PINGRID_ROW    = 'Row'
    REGEX_MODULE   = 'Regex-Module'
    REGEX_FUNCTION = 'Regex-Function'
    SIGNAL         = 'Signal'
    BUS            = 'Bus'
    STATUS         = 'Status'
    MAPPED_PINMODFUNC     = 'Mapped-PinModFunc'
    MAPPED_PINMODFUNC_KEY = 'Mapped-PinModFunc-Key'
    PRIMARY         = 'Primary'

class OptionsColumnLabels():
    __slots__ = ()
    BOARD_PIN       = 'Board-Pin'
    MCU_PIN         = 'MCU-Pin'
    REGEX_MODULES   = r'ALT\d+-Module'
    REGEX_FUNCTIONS = r'ALT\d+-Function'
    COMMENT         = 'Comment'

__all__ = ("StandardStrings", "EDBColumnLabels", "MCUColumnLabels")

