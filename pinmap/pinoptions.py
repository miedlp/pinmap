# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import pandas as pd
from pinmap import StandardStrings as PMTSTR
from pinmap.filebackend import OptionsColumnLabels

class PinOptions(object):
    def __init__(self, options: pd.DataFrame):
        """Initialize the self.initTable object.

        Parameters
        ----------
        self.initTable as a panadas dataframe of follwoing structure:

        | Board-Pin                                | MCU-Pin                         | ALT0-Module                   | ALT1-Function                   | ALT1-Module                   | ALT1-Function                   | ... | ALTn-Module                   | ALTn-Function                   |
        |:-----------------------------------------|:--------------------------------|:------------------------------|:--------------------------------|:------------------------------|:--------------------------------|:---:|:------------------------------|:------------------------------- |
        | Name of the pin on the board, e.g. J10.2 | Name of the MCU-Pin, e.g. P3.12 | Function alternative 0 module | Function alternative 0 function | Function alternative 1 module | Function alternative 1 function | ... | Function alternative n module | Function alternative n function |
        """

        # Make sure all init columns have the correct type.
        self.initTable = options.copy().astype(str)

        if OptionsColumnLabels.COMMENT not in self.initTable.columns:
            self.pins = self.initTable[[OptionsColumnLabels.BOARD_PIN, OptionsColumnLabels.MCU_PIN]].copy()
            self.pins.insert(len(self.pins.columns), OptionsColumnLabels.COMMENT, '')
        else:
            self.initTable.astype({
                        OptionsColumnLabels.COMMENT: str
                    })
            self.pins = self.initTable[[OptionsColumnLabels.BOARD_PIN, OptionsColumnLabels.MCU_PIN, OptionsColumnLabels.COMMENT]].copy()
        self.modules   = pd.DataFrame(pd.concat([self.initTable[columnname] for columnname in self.initTable.filter(regex=r'ALT\d+-Module').columns], ignore_index=True).unique(), columns=['names'])
        self.functions = pd.DataFrame(pd.concat([self.initTable[columnname] for columnname in self.initTable.filter(regex=r'ALT\d+-Function').columns], ignore_index=True).unique(), columns=['names'])
        self.modFunc   = pd.DataFrame(columns=['Module-Key', 'Function-Key'])
        self.pinModFunc = pd.DataFrame(columns=['Pin-Key', 'ModFunc-Key'])

        # Remove empty, N/C or N/A modules and functions
        listRemovable = ['', PMTSTR.NOT_AVAILABLE, PMTSTR.NOT_CONNECTED]
        for removable in listRemovable:
            self.modules = self.modules[self.modules.names != removable]
            self.functions = self.functions[self.functions.names != removable]
        self.modules = self.modules.reset_index(drop=True)
        self.functions = self.functions.reset_index(drop=True)

        altModules = self.initTable.filter(regex=OptionsColumnLabels.REGEX_MODULES, axis=1).columns
        for rowIdx, row in self.initTable.iterrows():
            for altModule in altModules:
                altFunction = altModule.split('-')[0] + '-Function'
                if row[altModule] in listRemovable or row[altFunction] in listRemovable:
                    continue
                moduleIdx   = self.modules[self.modules.names == row[altModule]].index[0]
                functionIdx = self.functions[self.functions.names == row[altFunction]].index[0]
                existingEntry = self.modFunc[(self.modFunc['Module-Key'] == moduleIdx) & (self.modFunc['Function-Key'] == functionIdx)]
                if existingEntry.shape[0] > 0:
                    idx = existingEntry.index[0]
                else:
                    idx = self.modFunc.shape[0]
                    self.modFunc.loc[idx] = [moduleIdx, functionIdx]
                self.pinModFunc.loc[self.pinModFunc.shape[0]] = [rowIdx, idx]
