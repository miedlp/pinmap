# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import os
import ipywidgets as widgets
import pandas as pd
import pathlib as pl
import asyncio
import threading
import queue

from pinmap.specifiers.board import Board

from pinmap import StandardStrings as PMTSTR
from pinmap.helper import PinSelector, ClearButton
from pinmap.filebackend import MappingColumnLabels
from pinmap.filebackend import OptionsColumnLabels
from pinmap.filebackend.base import FileBackend
from pinmap.filebackend.raw  import RawBackend as DefaultDataBackend
from pinmap.filebackend.pdf  import PdfBackend as DefaultReportBackend

def PinSelectorUpdate(change: dict) -> None:
    """Static function which is used as callback for updates of pin-selectors in the frontend."""
    change['owner'].parent.updateQueue.put(change['owner'])

def UpdaterFunction(parent: object) -> None:
    while True:
        changedPinSelector = parent.updateQueue.get()
        parent.selectorChangeUpdateMapping(changedPinSelector)
        if parent.updateQueue.empty():
            parent.updateFrontend(changedPinSelector)

class Adapter(Board):
    """TODO PMi description"""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a AdaperPinMapping object.


        Parameters
        ---------
        baseboard               : Baseboard object, defaults to Board(vendor="XXX", longname='dummybaseboard', shortname="XXX", revision='A').
        mcuboard                : MCU-Board object, defaults to Board(vendor="XXX", longname='dummymcuboard', shortname="XXX", revision='A').
        revision                : Revision of the adapter, defaults to >A<.
        generate                : A tuple with two entries, mappingFile path to the file containing the pins to be mapped on, e.g. the baseboard pin file, and optionsFile path to the file containing the pins to be mapped, e.g. the MCU-board pin file. Not used if importPath is set. Filetype must fit file backend.
        importPath              : Path to a valid pinmapping export, which is a directory containing and export directory named >Adapter_[revision]_[baseboard.vendor]_[baseboard.shortname]_[baseboard.revision]_[mcuboard.vendor]_[mcuboard.shortname]_[mcuboard.revision]<, which itself contains at least two files which fit the used file backend: mapping.*, options.*. Ignored if generate is set.
        exportPath              : Path to which a pinmapping is exported to by generating a directory named >Adapter_[revision]_[baseboard.vendor]_[baseboard.shortname]_[baseboard.revision]_[mcuboard.vendor]_[mcuboard.shortname]_[mcuboard.revision]<. Defaults to the working directory.
        backendImport           : Sets the used file backend for import files. Default is >raw<.
        backendExport           : Sets the used file backend for export files. Default is >raw<.
        backendReport           : Sets the used file backend for the report. Default is >pdf<.
        guiLabelIdWidth         : String defining the pin-id label width in pixel, default is 25.
        guiLabelSignalWidth     : String defining the signal label width in pixel, defaults to 140
        guiDropboxWidth         : String defining the dropbox width in pixel, defaults to 350
        guiColumnSpacing        : String defining the spacing between the pinselector-columns in pixel, defaults to 10
        guiExtraEmtpyLines      : Number of empty lines in the extraMappingDatagrid, defaults to 10
        """

        self.baseboard = kwargs.pop('baseboard', Board(vendor="XXX", longname='dummybaseboard', shortname="XXX", revision='A'))
        self.mcuboard  = kwargs.pop('mcuboard',  Board(vendor="XXX", longname='dummymcuboard',  shortname="XXX",  revision='A'))

        # TODO PMi: it would be possible to properly tie this with import/export filenames
        self._generateParameters = kwargs.pop('generate', None)

        # The first thing we need to do is save the kwargs in the object, otherwise some of the
        # object properties might not work.
        super(Adapter, self).__init__(*args, **kwargs)

        if self._generateParameters is not None:
            self._readBaseFiles(self._generateParameters[0], self._generateParameters[1])
        else:
            self.importMapping()
        self._generateFrontendElements()

        self.updateQueue = queue.Queue(maxsize=self.mapping.shape[0])
        self._workerThread = threading.Thread(target=UpdaterFunction, args=(self, ))
        self._workerThread.start()

    def __del__(self) -> None:
        self._workerThread.join()

    @Board.name.getter
    def name(self) -> str:
        return "_".join(["Adapter", self.revision, self.baseboard.vendor, self.baseboard.shortname, self.baseboard.revision, self.mcuboard.vendor, self.mcuboard.shortname, self.mcuboard.revision])

    @property
    def mapping(self) -> pd.DataFrame:
        if not hasattr(self, '_mapping'):
            raise Exception("Object not populated yet, please import or generate.")
        return self._mapping

    @property
    def options(self) -> pd.DataFrame:
        if not hasattr(self, '_options'):
            raise Exception("Object not populated yet, please import or generate.")
        return self._options

    @property
    def notes(self) -> str:
        return self.noteBox.value

    @notes.setter
    def notes(self, value: str) -> str:
        self.noteBox.value = value

    @property
    def edbColVals(self):
        return getattr(self, '_edbColVals', pd.DataFrame())

    @property
    def edbRowVals(self):
        return getattr(self, '_edbRowVals', pd.DataFrame())

    @property
    def busList(self) -> list[str]:
        """Return a list of all buses present in the pinmapping."""
        busList = pd.unique(self.mapping[MappingColumnLabels.BUS])
        busList.sort()
        return busList.tolist()

    @property
    def importPath(self) -> pl.Path:
        return self._initkwargs.get('importPath', pl.Path(os.getcwd()))

    @property
    def exportPath(self) -> pl.Path:
        return self._initkwargs.get('exportPath', pl.Path(os.getcwd()))

    @property
    def importBundlePath(self) -> pl.Path:
        return self.importPath.joinpath(self.name + self.backendImport.getFileEnding())

    @property
    def importDirPath(self) -> pl.Path:
        return self.importPath.joinpath(self.name)

    @property
    def exportBundlePath(self) -> pl.Path:
        return self.exportPath.joinpath(self.name + self.backendExport.getFileEnding())

    @property
    def exportDirPath(self) -> pl.Path:
        return self.exportPath.joinpath(self.name)

    @property
    def backendImport(self) -> FileBackend:
        return self._initkwargs.get('backendImport', DefaultDataBackend)

    @property
    def backendExport(self) -> FileBackend:
        return self._initkwargs.get('backendExport', DefaultDataBackend)

    @property
    def backendReport(self) -> FileBackend:
        return self._initkwargs.get('backendReport', DefaultReportBackend)

    def importMapping(self):
        if self.backendImport.hasBundleSupport():
            self._mapping, self._options, self._notes = self.backendImport.readBundle(self.importBundlePath)
        else:
            self._readBaseFiles(self.importDirPath.joinpath('mapping' + self.backendImport.getDataFileEnding()), self.importDirPath.joinpath('options' + self.backendImport.getDataFileEnding()))
            self.notes = self.backendImport.readNotesfile(self.importDirPath.joinpath('notes' + self.backendImport.getTextFileEnding()))

    def generateMapping(self, optionsFile: pl.Path | str, mappingFile: pl.Path | str) -> None:
        self._readBaseFiles(optionsFile, mappingFile)

    def _readBaseFiles(self, mappingFilePath: pl.Path | str, optionsFilePath: pl.Path | str) -> None:
        self._mapping = self.backendImport.readMappingfile(mappingFilePath)
        self._edbColVals = pd.unique(self._mapping[MappingColumnLabels.PINGRID_COLUMN])
        self._edbColVals.sort()
        self._edbColVals = pd.DataFrame(self._edbColVals, columns=[MappingColumnLabels.PINGRID_COLUMN])
        self._edbRowVals = pd.unique(self._mapping[MappingColumnLabels.PINGRID_ROW])
        self._edbRowVals.sort()
        self._edbRowVals = pd.DataFrame(self._edbRowVals, columns=[MappingColumnLabels.PINGRID_ROW])
        self._options = self.backendImport.readOptionsfile(optionsFilePath)

    def exportMapping(self):
        if self.backendExport.hasBundleSupport():
            self.backendExport.writeBundle(self.exportBundle, self._mapping, self._options, self._notes)
        else:
            self.exportDirPath.mkdir(parents=True, exist_ok=True)
            self.backendExport.writeOptionsfile(self.exportDirPath.joinpath('options' + self.backendExport.getDataFileEnding()), self.options)
            self.backendExport.writeMappingfile(self.exportDirPath.joinpath('mapping' + self.backendExport.getDataFileEnding()), self.mapping)
            self.backendExport.writeNotesfile(self.exportDirPath.joinpath('notes' + self.backendExport.getTextFileEnding()), self.notes)
        self.backendReport.writeReportFile(self)

    @property
    def mappingGridShape(self):
        """Return the shape of the frontend baseboard pin-grid."""
        return (len(self.edbRowVals), len(self.edbColVals))

    @property
    def noteBox(self) -> widgets.Textarea:
        if not hasattr(self, '_noteBox'):
            self._noteBox = widgets.Textarea(value='', placeholder='Write any notes regarding the pinadapter here in Markdown notation.', description='Notes:', disabled=False,
                                            layout=widgets.Layout(width='100%', height='300px'))
        return self._noteBox

    @property
    def guiStyleDict(self) -> dict:
        return self._initkwargs.get('_guiStyleDict', dict())
        #return self._initkwargs.get('_guiStyleDict', dict(font_family='DejaVu Sans Mono'))
        #return self._initkwargs.get(dict(font_family='Consolas'))
        #return self._initkwargs.get(dict(font_family='Lucida Console'))
        #return self._initkwargs.get(dict(font_family='Source Code Pro'))
        #return self._initkwargs.get(dict(font_family='Cascadia Mono'))
        #return self._initkwargs.get(dict(font_family='Courier New'))

    @property
    def guiLabelIdWidth(self) -> int:
        if not hasattr(self, '_guiLabelIdWidth'):
            self._guiLabelIdWidth = self._initkwargs.pop('guiLabelIdWidth', 25)
        return self._guiLabelIdWidth

    @property
    def guiLabelIdWidthPxStr(self) -> str:
        return str(self.guiLabelIdWidth) + 'px'

    @property
    def guiLabelStatusWidth(self) -> int:
        if not hasattr(self, '_guiLabelStatusWidth'):
            self._guiLabelStatusWidth = self._initkwargs.pop('guiLabelStatusWidth', 17)
        return self._guiLabelStatusWidth

    @property
    def guiLabelStatusWidthPxStr(self) -> str:
        return str(self.guiLabelStatusWidth) + 'px'

    @property
    def guiLabelSignalWidth(self) -> int:
        if not hasattr(self, '_guiLabelSignalWidth'):
            self._guiLabelSignalWidth = self._initkwargs.pop('guiLabelSignalWidth', 130)
        return self._guiLabelSignalWidth

    @property
    def guiLabelSignalWidthPxStr(self) -> str:
        return str(self.guiLabelSignalWidth) + 'px'

    @property
    def guiDropboxWidth(self) -> int:
        if not hasattr(self, '_guiDropboxWidth'):
            self._guiDropboxWidth = self._initkwargs.pop('guiDropboxWidth', 350)
        return self._guiDropboxWidth

    @property
    def guiDropboxWidthPxStr(self) -> str:
        return str(self.guiDropboxWidth) + 'px'

    @property
    def guiColumnSpacing(self) -> int:
        if not hasattr(self, '_guiColumnSpacing'):
            self._guiColumnSpacing = self._initkwargs.get('guiColumnSpacing', 10)
        return self._guiColumnSpacing

    @property
    def guiColumnSpacingPxStr(self) -> str:
        return str(self.guiColumnSpacing) + 'px'

    @property
    def guiElementWidth(self) -> int:
        return (self.guiDropboxWidth + self.guiLabelSignalWidth + self.guiLabelStatusWidth +  self.guiLabelIdWidth  + self.guiColumnSpacing)

    @property
    def guiElementWidthPxStr(self) -> str:
        return str(self.guiElementWidth) + 'px'

    @property
    def guiGridWidth(self) -> int:
        return self.guiElementWidth * self.mappingGridShape[1]

    @property
    def guiGridWidthPxStr(self) -> str:
        return str(self.guiGridWidth) + 'px'

    @property
    def mappingFrontEnd(self) -> widgets.VBox:
        """Show the mapping frontend below the current cell."""
        return widgets.VBox([self.mappingGrid, widgets.HBox(self.refreshbuttons), self.noteBox], layout=widgets.Layout(overflow='scroll'))

    def _generateFrontendElements(self) -> None:
        """Generate the frontend elements, i.e. the dropdown menus with labels and the clear buttons."""
        self.mappingGrid = widgets.GridspecLayout(self.mappingGridShape[0], self.mappingGridShape[1], layout=widgets.Layout(width=self.guiGridWidthPxStr))
        self.buses       = {bus: {'Members': [], 'Module-Key': -1} for bus in self.busList}

        prevPinSelectorElement = None
        currPinSelectorElement = None
        nextPinSelectorElement = None
        for mappingIdx, pin in self.mapping.iterrows():
            rowIdx = self.edbRowVals[self.edbRowVals[MappingColumnLabels.PINGRID_ROW] == pin[MappingColumnLabels.PINGRID_ROW]].index[0]
            colIdx = self.edbColVals[self.edbColVals[MappingColumnLabels.PINGRID_COLUMN] == pin[MappingColumnLabels.PINGRID_COLUMN]].index[0]
            selectorLabel = "{:<1}{:<2}".format(pin[MappingColumnLabels.PINGRID_COLUMN], pin[MappingColumnLabels.PINGRID_ROW])
            statusSymbol  = PMTSTR.STATUS_OPEN_SYMBOL if PMTSTR.STATUS_OPEN in pin[MappingColumnLabels.STATUS] else PMTSTR.STATUS_CLOSED_SYMBOL
            tmpPinLabelElement = widgets.HBox([
                widgets.Label(value=selectorLabel                  , style=self.guiStyleDict, layout=widgets.Layout(width=self.guiLabelIdWidthPxStr, display='flex', justify_content="flex-end")),
                widgets.Label(value=statusSymbol                   , style=self.guiStyleDict, layout=widgets.Layout(width=self.guiLabelStatusWidthPxStr)),
                widgets.Label(value=pin[MappingColumnLabels.SIGNAL], style=self.guiStyleDict, layout=widgets.Layout(width=self.guiLabelSignalWidthPxStr)),
            ])

            prevPinSelectorElement = currPinSelectorElement
            currPinSelectorElement = nextPinSelectorElement
            nextPinSelectorElement = PinSelector(description="", disabled=False, layout=widgets.Layout(width=self.guiDropboxWidthPxStr, grid_area='header', style=self.guiStyleDict),
                                                mappingIdx=mappingIdx, parent=self, fullLabel=selectorLabel +  "-" + pin[MappingColumnLabels.SIGNAL] + " " + statusSymbol)

            if currPinSelectorElement != None:
                currPinSelectorElement.previous = prevPinSelectorElement
                currPinSelectorElement.next     = nextPinSelectorElement

            self.mappingGrid[rowIdx, colIdx] = widgets.HBox([tmpPinLabelElement, nextPinSelectorElement], layout=widgets.Layout(width=self.guiElementWidthPxStr))
            self.buses[pin[MappingColumnLabels.BUS]]['Members'].append(nextPinSelectorElement)
            nextPinSelectorElement.options = ['']
            nextPinSelectorElement.value = ''
            nextPinSelectorElement.observe(PinSelectorUpdate, names='value', type='change')
            self._updateSelectorOptions(nextPinSelectorElement)

        self.refreshbuttons = []
        for bus in self.busList:
            if bus == '':
                buttonLabel = "Clear All"
                bus = 'All'
            else:
                buttonLabel = "Clear " + bus
            self.refreshbuttons.append(ClearButton(description=buttonLabel, bus=bus, parent=self))
            self.refreshbuttons[-1].on_click(self._clearBus)

    def _getUsedPinKeys(self, ownPinKey: int = -1):
        usedPinKeys = self.options.pinModFunc.iloc[self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY][self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY] != -1]]['Pin-Key']
        usedPinKeys = usedPinKeys[usedPinKeys != ownPinKey] # Remove own ownPinKey from usedPinKeys
        return usedPinKeys

    def _getUsedModFuncKeys(self, ownModFuncKey: int = -1):
        usedModFuncKeys = self.options.pinModFunc.iloc[self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY][self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY] != -1]]['ModFunc-Key']
        usedModFuncKeys = usedModFuncKeys[usedModFuncKeys != ownModFuncKey] # Remove own modFuncKey from usedModFuncKeys
        return usedModFuncKeys

    def _updateSelectorOptions(self, pinSelector: PinSelector) -> None:
        """Update the PinSelector options list according to the current state of the mapping, i.e. the already selected pins and module-function-combinations."""
        currentPin = self.mapping.iloc[pinSelector.mappingIdx]
        if currentPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY] != -1 and currentPin[MappingColumnLabels.PRIMARY] != '':
            if "Pin>" in pinSelector.value:
                # The selected pin is already used, do not remove from usedPinKeys list
                ownPinKey     = -1
                ownModFuncKey = self.options.pinModFunc.iloc[currentPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY]]['ModFunc-Key']
            elif "Func>" in pinSelector.value:
                # The selected module-function-combination is already used, do not remove from usedPinKeys list
                ownPinKey     = self.options.pinModFunc.iloc[currentPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY]]['Pin-Key']
                ownModFuncKey = -1
            else:
                # The selected pin-module-function-combination is not already used, remove from usedPinKeys and usedModFuncKeys list to prevent getting
                # the shared label.
                ownPinKey     = self.options.pinModFunc.iloc[currentPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY]]['Pin-Key']
                ownModFuncKey = self.options.pinModFunc.iloc[currentPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY]]['ModFunc-Key']
        else:
            ownPinKey     = -1
            ownModFuncKey = -1
        if self.buses[currentPin[MappingColumnLabels.BUS]]['Module-Key'] >= 0:
            allowedModuleKeys = [self.buses[currentPin[MappingColumnLabels.BUS]]['Module-Key']]
        else:
            allowedModuleKeys   =  self.options.modules[self.options.modules.names.str.contains(currentPin[MappingColumnLabels.REGEX_MODULE], regex=True, na=False)].index
            # Remove all modules which are already in use
            if currentPin[MappingColumnLabels.BUS] != '':
                for bus in self.buses:
                    allowedModuleKeys = allowedModuleKeys[allowedModuleKeys != self.buses[bus]['Module-Key']]
        allowedFunKeys = self.options.functions[self.options.functions.names.str.contains(currentPin[MappingColumnLabels.REGEX_FUNCTION], regex=True, na=False)].index
        allowedModFuncKeys = self.options.modFunc[(self.options.modFunc['Module-Key'].isin(allowedModuleKeys)) & (self.options.modFunc['Function-Key'].isin(allowedFunKeys))].index
        allowedPinModFuncKeys = self.options.pinModFunc[self.options.pinModFunc['ModFunc-Key'].isin(allowedModFuncKeys)].index

        # Add Shared Label
        usedPinKeys = self._getUsedPinKeys(ownPinKey)
        usedModFuncKeys = self._getUsedModFuncKeys(ownModFuncKey)
        menuOptions = ['']

        for pinModFuncKey in allowedPinModFuncKeys:
            pinKey      = self.options.pinModFunc.iloc[pinModFuncKey]['Pin-Key']
            modFuncKey  = self.options.pinModFunc.iloc[pinModFuncKey]['ModFunc-Key']
            modKey      = self.options.modFunc.iloc[modFuncKey]['Module-Key']
            funcKey     = self.options.modFunc.iloc[modFuncKey]['Function-Key']

            strBoardPin = str(self.options.pins.iloc[pinKey][OptionsColumnLabels.BOARD_PIN])
            strMcuPin   = str(self.options.pins.iloc[pinKey][OptionsColumnLabels.MCU_PIN])
            strModule   = str(self.options.modules.iloc[modKey]['names'])
            strFunction = str(self.options.functions.iloc[funcKey]['names'])

            # TODO PMi: Dropdown widgets do not support monospaced fonts yet, so the formatting is not really useful....
            strOption   = "{:<6} - {:<5} - {} - {}".format(strBoardPin, strMcuPin, strModule, strFunction)

            # Add prefix that the pin or function has a conflict
            strConflictPrefix = ''
            if (pinKey in usedPinKeys.values):
                strConflictPrefix = strConflictPrefix + self._generateConflictTags(pinSelector, "Pin", self.options.pinModFunc[self.options.pinModFunc['Pin-Key'] == pinKey].index)
            if (modFuncKey in usedModFuncKeys.values) and len(strConflictPrefix) == 0: # Pin conflict overrules function conflict.
                strConflictPrefix = strConflictPrefix + self._generateConflictTags(pinSelector, "Func", self.options.pinModFunc[self.options.pinModFunc['ModFunc-Key'] == modFuncKey].index)
            strOption = "{}{}".format(strConflictPrefix, strOption)
            menuOptions.append(strOption)
        pinSelector.unobserve(PinSelectorUpdate, names='value', type='change')
        pinSelector.options = menuOptions
        pinSelector.observe(PinSelectorUpdate, names='value', type='change')
        self._safeSetPinSelectorValue(pinSelector, currentPin[MappingColumnLabels.MAPPED_PINMODFUNC])

    def _generateConflictTags(self, pinSelector: PinSelector, strSpecifier: str, primaryPinModFuncPinCandidates: pd.core.indexes.base.Index) -> str:
        """Check whether a pin or module-function-combination is already in use and attach the corresponding conflict tags. An empty tag
        is returend if not conflicts are found."""
        currentPin = self.mapping.iloc[pinSelector.mappingIdx]
        primaryMapping = self.mapping[(self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY].isin(primaryPinModFuncPinCandidates)) & (self.mapping[MappingColumnLabels.PRIMARY] != '')]
        primaryMapping = primaryMapping[primaryMapping[MappingColumnLabels.PINGRID_COLUMN].index != currentPin.name]   # Avoid adding shared prefix for own pin.
        if len(primaryMapping) == 0:
            # There is a pin conflict but the pin is used with another function where the other pin is not the primary usage of this pin,
            # or there is a function conflict but the function is used with another pin but the usage of the function is not the primary usage.
            # Therefore the primaryMapping is empty and we do not need to put an additional conflict tag.
            # The primary pin has changed and  now its the current pin, so primaryMapping ends up to be empty
            return ''
        primaryMapping = primaryMapping.iloc[0]
        if primaryMapping[MappingColumnLabels.BUS] != '':
            strPrimaryMappedBus = '@' + primaryMapping[MappingColumnLabels.BUS]
        else:
            strPrimaryMappedBus = ''
        strPrimaryMapped = str(primaryMapping[MappingColumnLabels.PINGRID_COLUMN]) + str(primaryMapping[MappingColumnLabels.PINGRID_ROW])
        return "{}>{}{}>> ".format(strSpecifier, strPrimaryMapped, strPrimaryMappedBus)

    def _removeSharedPrefixFromSelectorValue(self, value: str) -> str:
        """Remove the shared prefix from a PinSelector value string."""
        return value.split('>> ')[-1]

    def _safeSetPinSelectorValue(self, pinSelector: PinSelector, value: str) -> None:
        """Set the PinSelector Value in a fashion that will avoid Exceptions, even if the desired
        value is not in the options list anymore. In this case, an empty value will be set, i.e.
        the PinSelector is reset."""
        value = self._removeSharedPrefixFromSelectorValue(value)
        valueToSet = pinSelector.options[0]
        if value != '':
            for option in pinSelector.options:
                if value in option:
                    valueToSet = option
        pinSelector.unobserve(PinSelectorUpdate, names='value', type='change')
        pinSelector.value = valueToSet
        pinSelector.observe(PinSelectorUpdate, names='value', type='change')

    def _splitPinSelectorValueString(self, pinSelectorStr: str) -> tuple[str]:
        """Split the PinSelector value string into Board-Pin, MCU-Pin, Module and Function string."""
        newSelectedPin = self._removeSharedPrefixFromSelectorValue(pinSelectorStr)
        if len(newSelectedPin) == 0:
            # Empty string, return
            return ('', '', '', '')
        [strBoardPin, strMcuPin, strModule, strFunction] = newSelectedPin.split(' - ')
        strBoardPin   = strBoardPin.replace(' ', '')
        strMcuPin     = strMcuPin.replace(' ', '')
        strModule     = strModule.replace(' ', '')
        strFunction   = strFunction.replace(' ', '')
        return (strBoardPin, strMcuPin, strModule, strFunction)

    def selectorChangeUpdateMapping(self, pinSelector: PinSelector) -> None:
        """Update a single mapping for a given selector. Reset the value of the selector if reset is
        true and update the value of the corresponding row in the mapping table.
        """
        oldPinModFunc    = self.mapping.iloc[pinSelector.mappingIdx][MappingColumnLabels.MAPPED_PINMODFUNC]
        changePrimary    = self.mapping.iloc[pinSelector.mappingIdx][MappingColumnLabels.PRIMARY] != ''
        if pinSelector.value == '' or pinSelector.value == None:
            self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.MAPPED_PINMODFUNC] = ''
            self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.MAPPED_PINMODFUNC_KEY] = -1
            self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.PRIMARY] = ''
        else:
            (strBoardPin, strMcuPin, strModule, strFunction) = self._splitPinSelectorValueString(pinSelector.value)

            pinKey        = self.options.pins[(self.options.pins[OptionsColumnLabels.BOARD_PIN] == strBoardPin) & (self.options.pins[OptionsColumnLabels.MCU_PIN] == strMcuPin)].index[0]
            modKey        = self.options.modules[self.options.modules.names == strModule].index[0]
            funcKey       = self.options.functions[self.options.functions.names == strFunction].index[0]
            modFuncKey    = self.options.modFunc[(self.options.modFunc['Module-Key'] == modKey) & (self.options.modFunc['Function-Key']== funcKey)].index[0]
            pinModFuncKey = self.options.pinModFunc[(self.options.pinModFunc['Pin-Key'] == pinKey) & (self.options.pinModFunc['ModFunc-Key']== modFuncKey)].index[0]

            self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.MAPPED_PINMODFUNC]     = pinSelector.value
            self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.MAPPED_PINMODFUNC_KEY] = pinModFuncKey

            allPinModFuncForPin     = self.options.pinModFunc[self.options.pinModFunc['Pin-Key'] == pinKey].index
            allPinModFuncForModFunc = self.options.pinModFunc[self.options.pinModFunc['ModFunc-Key']== modFuncKey].index
            if (len(self.mapping[self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY].isin(allPinModFuncForPin)]) > 1) or (len(self.mapping[self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY].isin(allPinModFuncForModFunc)]) > 1):
                self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.PRIMARY] = ''
            else:
                self.mapping.loc[pinSelector.mappingIdx, MappingColumnLabels.PRIMARY] = 'x'

        if changePrimary:
            self._updatePrimary(oldPinModFunc)

        # Update bus module
        self._updateBusModuleKey(self.mapping.iloc[pinSelector.mappingIdx])

    def _updatePrimary(self, oldPinModFunc: str) -> None:
        (strOldBoardPin, strOldMcuPin, strOldModule, strOldFunction) = self._splitPinSelectorValueString(oldPinModFunc)
        oldPinKey       = self.options.pins[(self.options.pins[OptionsColumnLabels.BOARD_PIN] == strOldBoardPin) & (self.options.pins[OptionsColumnLabels.MCU_PIN] == strOldMcuPin)].index[0]
        oldModKey       = self.options.modules[self.options.modules.names == strOldModule].index[0]
        oldFuncKey      = self.options.functions[self.options.functions.names == strOldFunction].index[0]
        oldModFuncKey   = self.options.modFunc[(self.options.modFunc['Module-Key'] == oldModKey) & (self.options.modFunc['Function-Key']== oldFuncKey)].index[0]
        usedPinKeys     = self._getUsedPinKeys()
        usedModFuncKeys = self._getUsedModFuncKeys()

        if (oldPinKey in usedPinKeys.values):
            newPrimaryPinModFuncCandidateKeys = self.options.pinModFunc[self.options.pinModFunc['Pin-Key'] == oldPinKey].index
        elif (oldModFuncKey in usedModFuncKeys.values):
            newPrimaryPinModFuncCandidateKeys = self.options.pinModFunc[self.options.pinModFunc['ModFunc-Key']== oldModFuncKey].index
        else:
            newPrimaryPinModFuncCandidateKeys = []

        if len(newPrimaryPinModFuncCandidateKeys) > 0:
            # Set new primary pin
            newPrimaryIdx = self.mapping[self.mapping[MappingColumnLabels.MAPPED_PINMODFUNC_KEY].isin(newPrimaryPinModFuncCandidateKeys)].index
            if len(newPrimaryIdx) > 0:
                self.mapping.loc[newPrimaryIdx[0], MappingColumnLabels.PRIMARY] = 'x'
                self.mapping.loc[newPrimaryIdx[0], MappingColumnLabels.MAPPED_PINMODFUNC] = self._removeSharedPrefixFromSelectorValue(self.mapping.loc[newPrimaryIdx[0], MappingColumnLabels.MAPPED_PINMODFUNC])

    def _updateBusModuleKey(self, pinSelector: PinSelector):
        """Update the bus module that is associated with the bus of the current pinSelector."""
        if pinSelector[MappingColumnLabels.BUS] == '':
            return
        busMemModKey = -1
        for busMember in self.buses[pinSelector[MappingColumnLabels.BUS]]['Members']:
            busMemberPin     = self.mapping.iloc[busMember.mappingIdx]
            if busMemberPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY] != -1:
                busMemModFuncKey = self.options.pinModFunc.iloc[busMemberPin[MappingColumnLabels.MAPPED_PINMODFUNC_KEY]]['ModFunc-Key']
                busMemModKey     = self.options.modFunc.iloc[busMemModFuncKey]['Module-Key']
                break
        self.buses[pinSelector[MappingColumnLabels.BUS]]['Module-Key'] = busMemModKey

    def updateFrontend(self, startingPinSelector: PinSelector) -> None:
        """Update the pinmapping front end, i.e. update all options for all dropdown menus and the
        mappig table."""
        self._updateSelectorOptions(startingPinSelector)
        prev = startingPinSelector.previous
        next = startingPinSelector.next
        while prev != None or next != None:
            if prev != None:
                self._updateSelectorOptions(prev)
                prev = prev.previous
            if next != None:
                self._updateSelectorOptions(next)
                next = next.next

    def _resetPinSelector(self, pinSelector: PinSelector) -> None:
        pinSelector.unobserve(PinSelectorUpdate, names='value', type='change')
        pinSelector.value = pinSelector.options[0]
        pinSelector.observe(PinSelectorUpdate, names='value', type='change')
        self.updateQueue.put(pinSelector)

    def _clearBus(self, button: ClearButton) -> None:
        if button.bus == 'All':
            busesToClear = self.buses.keys()
        else:
            busesToClear = [button.bus]

        for bus in busesToClear:
            for pinSelector in self.buses[bus]['Members']:
                self._resetPinSelector(pinSelector)
