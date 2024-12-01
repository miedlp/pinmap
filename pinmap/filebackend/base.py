# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import pathlib as pl
import pandas as pd
import numpy as np

from pinmap.pinoptions import PinOptions

class FileBackend():
    @staticmethod
    def getDataFileEnding() -> str:
        return ''

    @staticmethod
    def getTextFileEnding() -> str:
        return ''

    @staticmethod
    def hasBundleSupport() -> bool:
        """Returns whether the backend supports bundles, i.e. readBundle and writeBundle are implemented."""
        return False

    @staticmethod
    def readBundle(filepath: pl.Path) -> tuple[pd.DataFrame, PinOptions, str]:
        """Read all data from one bundle, returns True if successful/supported and False if not."""
        raise Exception("This backend cannot be used to read the bundle files.")

    @staticmethod
    def readMappingfile(filepath: pl.Path) -> pd.DataFrame:
        raise Exception("This backend cannot be used to read the mapping file.")

    @staticmethod
    def readOptionsfile(filepath: pl.Path) -> PinOptions:
        raise Exception("This backend cannot be used to read the options file.")

    @staticmethod
    def readNotesfile(filepath: pl.Path) -> str:
        raise Exception("This backend cannot be used to read the notes file.")

    @staticmethod
    def writeBundle(filepath: pl.Path, mapping: pd.DataFrame, options: PinOptions, notes: str) -> None:
        """Write all data in one bundle, returns True if successful/supported and False if not."""
        raise Exception("This backend cannot be used to write the bundle files.")

    @staticmethod
    def writeMappingfile(filepath: pl.Path, mapping: pd.DataFrame) -> None:
        raise Exception("This backend cannot be used to write the mapping file.")

    @staticmethod
    def writeOptionsfile(filepath: pl.Path, options: PinOptions) -> None:
        raise Exception("This backend cannot be used to write the options file.")

    @staticmethod
    def writeNotesfile(filepath: pl.Path, notes, str) -> None:
        raise Exception("This backend cannot be used to write the notes file.")

    @staticmethod
    def writeReportFile(adapterObj: object) -> None:
        raise Exception("This backend cannot be used to write the report file.")

