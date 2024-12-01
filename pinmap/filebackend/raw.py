# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import pathlib as pl
import pandas as pd

from pinmap.pinoptions import PinOptions
from pinmap.filebackend import MappingColumnLabels
from pinmap.filebackend import OptionsColumnLabels
from pinmap.filebackend.base import FileBackend

class RawBackend(FileBackend):
    @staticmethod
    def getDataFileEnding() -> str:
        return '.csv'

    @staticmethod
    def getTextFileEnding() -> str:
        return '.md'

    @staticmethod
    def readMappingfile(filepath: pl.Path | str) -> pd.DataFrame:
        """
        Read the mapping file, i.e. the file defining the pins on the host board. This can be, for example, the MT_EDB.
        This file must have following structure, whereas the columns are comma separated:

        | Column                   | Row                   | Bus                                          | Signal     | Status                 | Regex-Module                    | Regex-Function                    |
        |:-------------------------|:----------------------|:---------------------------------------------|:-----------|:-----------------------|:--------------------------------|:----------------------------------|
        | Column identifier of pin | Row identifeir of pin | To which bus the pin belong to, can be empty | Signalname | Default open or closed | Regex to filter allowed modules | Regex to filter allowed functions |

        Parameters
        ----------
        filepath: Path to the mapping file as string or pathlib.Path
        """
        mapping = pd.read_csv(filepath, sep='\s*,\s*', engine='python')

        # Add missing colmns mapped pin and mapped pin key if they are not present
        if MappingColumnLabels.MAPPED_PINMODFUNC not in mapping.columns:
            mapping.insert(len(mapping.columns), MappingColumnLabels.MAPPED_PINMODFUNC, '')
        if MappingColumnLabels.MAPPED_PINMODFUNC_KEY not in mapping.columns:
            mapping.insert(len(mapping.columns), MappingColumnLabels.MAPPED_PINMODFUNC_KEY, -1)
        if MappingColumnLabels.PRIMARY not in mapping.columns:
            mapping.insert(len(mapping.columns), MappingColumnLabels.PRIMARY, '')

        # Replace N/A values
        mapping[MappingColumnLabels.PINGRID_COLUMN]        = mapping[MappingColumnLabels.PINGRID_COLUMN].fillna('')
        mapping[MappingColumnLabels.PINGRID_ROW]           = mapping[MappingColumnLabels.PINGRID_ROW].fillna(-1)
        mapping[MappingColumnLabels.SIGNAL]                = mapping[MappingColumnLabels.SIGNAL].fillna('')
        mapping[MappingColumnLabels.BUS]                   = mapping[MappingColumnLabels.BUS].fillna('')
        mapping[MappingColumnLabels.STATUS]                = mapping[MappingColumnLabels.STATUS].fillna('')
        mapping[MappingColumnLabels.REGEX_MODULE]          = mapping[MappingColumnLabels.REGEX_MODULE].fillna('')
        mapping[MappingColumnLabels.REGEX_FUNCTION]        = mapping[MappingColumnLabels.REGEX_FUNCTION].fillna('')
        mapping[MappingColumnLabels.MAPPED_PINMODFUNC]     = mapping[MappingColumnLabels.MAPPED_PINMODFUNC].fillna('')
        mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY] = mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY].fillna(-1)
        mapping[MappingColumnLabels.PRIMARY]               = mapping[MappingColumnLabels.PRIMARY].fillna('')

        # Make sure all columns have the correct type.
        mapping = mapping.astype({
                MappingColumnLabels.PINGRID_COLUMN: str,
                MappingColumnLabels.PINGRID_ROW: int,
                MappingColumnLabels.SIGNAL: str,
                MappingColumnLabels.BUS: str,
                MappingColumnLabels.STATUS: str,
                MappingColumnLabels.REGEX_MODULE: str,
                MappingColumnLabels.REGEX_FUNCTION: str,
                MappingColumnLabels.MAPPED_PINMODFUNC: str,
                MappingColumnLabels.MAPPED_PINMODFUNC_KEY: int,
                MappingColumnLabels.PRIMARY: str
            })
        return mapping

    @staticmethod
    def readOptionsfile(filepath: pl.Path) -> PinOptions:
        """
        Read the options file, i.e. the file definint the pins on the MCU-Board. This can be, for example, a LPCXpresso board.
        For a MCU with n-functions per pin, this file must have following structure, whereas the columns are comma separated:

        | Board-Pin                                | MCU-Pin                         | ALT0-Module                   | ALT1-Function                   | ALT1-Module                   | ALT1-Function                   | ... | ALTn-Module                   | ALTn-Function                   |
        |:-----------------------------------------|:--------------------------------|:------------------------------|:--------------------------------|:------------------------------|:--------------------------------|:---:|:------------------------------|:------------------------------- |
        | Name of the pin on the board, e.g. J10.2 | Name of the MCU-Pin, e.g. P3.12 | Function alternative 0 module | Function alternative 0 function | Function alternative 1 module | Function alternative 1 function | ... | Function alternative n module | Function alternative n function |

        Parameters
        ----------
        filepath: Path to the options file as string or pathlib.Path
        """
        options = PinOptions(pd.read_csv(filepath, sep='\s*,\s*', engine='python').fillna(''))
        return options


    @staticmethod
    def readNotesfile(filepath: pl.Path) -> str:
        with open(filepath, "r") as notes:
            notes = notes.read()
        return notes

    @staticmethod
    def writeMappingfile(filepath: pl.Path, mapping: pd.DataFrame) -> None:
        mapping.to_csv(filepath, index=False)

    @staticmethod
    def writeOptionsfile(filepath: pl.Path, options: PinOptions) -> None:
        options.initTable.to_csv(filepath, index=False)

    @staticmethod
    def writeNotesfile(filepath: pl.Path, notes: str) -> None:
        with open(filepath, "w") as notefile:
            notefile.write(notes)
