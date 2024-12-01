# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import datetime as dt
import math
import pathlib as pl
import os
import re

import numpy as np
from functools import partial

from pinmap.document.platypus import *
from pinmap.document.lib import colors
from pinmap.document.lib.pagesizes import A4, landscape
from pinmap.document.lib.styles import getSampleStyleSheet
from pinmap.document.lib.units import cm
from pinmap.document.lib.colors import CMYKColor

import pinmap.document.pagestyle as PageStyle

from pinmap.filebackend.base import FileBackend
from pinmap.filebackend import MappingColumnLabels

GRID_STYLE = TableStyle(
      [
        ('LINEABOVE',       ( 0, 0), (-1, 0), 2, colors.black),
        ('LINEBELOW',       ( 0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW',       ( 0,-1), (-1,-1), 2, colors.black),
        ('LINEBEFORE',      ( 0, 0), ( 0,-1), 2, colors.black),
        ('LINEAFTER',       (-1, 0), (-1,-1), 2, colors.black),
        #('FONTNAME',        ( 0, 0), (-1,-1), 'Arial'),                           # (or FACE) takes fontname.
        ('FONTSIZE',        ( 0, 0), (-1,-1),    9),                               # (or SIZE) takes fontsize in points; leading may get out of sync.
        ('LEADING',         ( 0, 0), (-1,-1),    0),                               #- takes leading in points.
        ('TEXTCOLOR',       ( 0, 0), (-1,-1),    colors.black),                    #- takes a color name or (R,G,B) tuple.
        ('ALIGNMENT',       ( 0, 0), (-1,0),    'CENTER'),                         # (or ALIGN)    #- takes one of LEFT, RIGHT and CENTRE (or CENTER) or DECIMAL.
        ('ALIGNMENT',       ( 0, 1), (-1,-1),    'LEFT'),                          # (or ALIGN)    #- takes one of LEFT, RIGHT and CENTRE (or CENTER) or DECIMAL.
        ('LEFTPADDING',     ( 0, 0), (-1,-1),    3),                               #- takes an integer, defaults to 6.
        ('RIGHTPADDING',    ( 0, 0), (-1,-1),    3),                               #- takes an integer, defaults to 6.
        ('BOTTOMPADDING',   ( 0, 0), (-1,-1),    1),                               #- takes an integer, defaults to 3.
        ('TOPPADDING',      ( 0, 0), (-1,-1),    1),                               #- takes an integer, defaults to 3.
        #('BACKGROUND',     ( 0, 0), (-1,-1),    colors.white),                    #- takes a color defined by an object, string name or numeric tuple/list,
                                                                                   #  or takes a list/tuple describing a desired gradient fill which should
                                                                                   #  contain three elements of the form [DIRECTION, startColor, endColor]
                                                                                   #  where DIRECTION is either VERTICAL or HORIZONTAL.
        ('ROWBACKGROUNDS',  ( 0, 0), (-1,-1),    [colors.gray, colors.white]),     #- takes a list of colors to be used cyclically.
        #('COLBACKGROUNDS', ( 0, 0), (-1,-1),    [colors.white, colors.white]),    #- takes a list of colors to be used cyclically.
        ('VALIGN',          ( 0, 0), (-1,-1),    'TOP'),                           #- takes one of TOP, MIDDLE or the default BOTTOM
      ]
    )

class PdfBackend(FileBackend):
    @staticmethod
    def getTextFileEnding() -> str:
        return '.pdf'

    def writeReportFile(adapterObj: object) -> None:
        numColsPerPage          = 3
        numRowsPerpage          = 33
        mappingTableColumnNames = {
                                    'ELO': ['Baseboard', 'MCU Board Pin'],
                                    'SW':  ['Baseboard', 'MCU Pinfunction']
                                  }
        pagesPerRow             = math.ceil(len(adapterObj.edbColVals[MappingColumnLabels.PINGRID_COLUMN])/numColsPerPage)
        pagesPerColumn          = math.ceil(len(adapterObj.edbRowVals[MappingColumnLabels.PINGRID_ROW])/numRowsPerpage)
        numTotalPages           = pagesPerRow*pagesPerColumn
        mappingTables           = {mappingGroup: [[np.full((numRowsPerpage,2), "", dtype=str) for __ in range(pagesPerRow)] for _ in range(numTotalPages)] for mappingGroup in mappingTableColumnNames.keys()}
        for mappingGroup in mappingTableColumnNames.keys():
            mappingTables[mappingGroup] = []
            for pageIdx in range(numTotalPages):
                mappingTables[mappingGroup].append([])
                for tableIdx in range(numColsPerPage):
                    mappingTables[mappingGroup][pageIdx].append(np.full((numRowsPerpage,2), '', dtype=np.dtype('U100')))
                    mappingTables[mappingGroup][pageIdx][tableIdx][0,:] = mappingTableColumnNames[mappingGroup]

        for _, pin in adapterObj.mapping.iterrows():
            rowIdx = adapterObj.edbRowVals[adapterObj.edbRowVals[MappingColumnLabels.PINGRID_ROW] == pin[MappingColumnLabels.PINGRID_ROW]].index[0]
            colIdx = adapterObj.edbColVals[adapterObj.edbColVals[MappingColumnLabels.PINGRID_COLUMN] == pin[MappingColumnLabels.PINGRID_COLUMN]].index[0]

            if pagesPerColumn > 1:
                pageIdx  = math.floor(colIdx / numColsPerPage) * pagesPerRow + math.floor(rowIdx / numRowsPerpage)
            else:
                pageIdx  = math.floor(rowIdx / numRowsPerpage) * pagesPerColumn + math.floor(colIdx / numColsPerPage)
            tableIdx     = colIdx % numColsPerPage
            onPageRowIdx = (rowIdx % numRowsPerpage) + 1

            baseboardPin    = str(pin[MappingColumnLabels.PINGRID_COLUMN]) + str(pin[MappingColumnLabels.PINGRID_ROW])
            baseboardSignal = re.match(r'[A-Za-z0-9]+_*[A-Za-z0-9]*', pin[MappingColumnLabels.SIGNAL]).group(0)
            (strBoardPin, strMcuPin, strModule, strFunction) = adapterObj._splitPinSelectorValueString(pin[MappingColumnLabels.MAPPED_PINMODFUNC])

            try:
                mappingTables['ELO'][pageIdx][tableIdx][onPageRowIdx, 0] = baseboardPin + ": " + baseboardSignal
            except:
                pass
            mappingTables['SW'][pageIdx][tableIdx][onPageRowIdx, 0]  = baseboardPin + ": " + baseboardSignal
            if len(strBoardPin) > 0 and len(strMcuPin) > 0:
                mappingTables['ELO'][pageIdx][tableIdx][onPageRowIdx, 1] = strBoardPin + " - " + strMcuPin
                mappingTables['SW'][pageIdx][tableIdx][onPageRowIdx, 1]  = strMcuPin + " - " + strModule + "_" + strFunction

        filename = adapterObj.name + adapterObj.backendReport.getTextFileEnding()
        filepath = str(adapterObj.exportDirPath.joinpath(filename))
        doc = BaseDocTemplate(filepath, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
        styles = getSampleStyleSheet()

        styles['bu'].leftIndent = -7

        story= []
        # Title Page
        story.append(Spacer(1,1*cm))
        story.append(Paragraph("Adapter for {} {} on {} {}".format(adapterObj.mcuboard.vendor, adapterObj.mcuboard.longname, adapterObj.baseboard.vendor, adapterObj.baseboard.longname), style=styles['Heading1']))
        story.append(Spacer(1,1.5*cm))
        story.append(Paragraph("Author: " + os.getlogin(), style=styles['Heading2']))
        story.append(Paragraph("Date: " + dt.datetime.today().strftime('%Y-%m-%d'), style=styles['Heading2']))
        story.append(Paragraph("Adapter-Revision: " + adapterObj.revision, style=styles['Heading2']))
        story.append(Paragraph("Baseboard: " + "_".join([adapterObj.baseboard.vendor, adapterObj.baseboard.shortname, adapterObj.baseboard.revision]), style=styles['Heading2']))
        story.append(Paragraph("MCU-Board: " + "_".join([adapterObj.mcuboard.vendor, adapterObj.mcuboard.shortname, adapterObj.mcuboard.revision]), style=styles['Heading2']))

        # Note Page
        story.append(PageBreak())
        story.append(Paragraph("Important Notes", style=styles['Heading2']))
        notesList = []
        for line in adapterObj.notes.split('\n'):
            notesList.append(ListItem(Paragraph(line.replace('* ', '').replace('- ', ''), style=styles['bu']),
                                leftIndent=25,
                                spaceBefore=2,
                                spaceAfter=2,
                                bulletOffsetY=-3,
                                value='square', bulletFontSize=5, bulletColor=CMYKColor(0.65, 0.0, 1.0, 0.0))
                            )
        story.append(ListFlowable(notesList, bulletType='bullet'))

        # Mapping pages
        story.append(NextPageTemplate('landscape'))
        for mappingGroup in mappingTableColumnNames.keys():
            for pageIdx in range(numTotalPages):
                story.append(PageBreak())
                story.append(Paragraph("Pin Mappings - {}".format(mappingGroup), style=styles['Heading2']))
                story.append(Table([[Table(npTable.tolist(), style=GRID_STYLE) for npTable in mappingTables[mappingGroup][pageIdx]]]))


        headerOffset  = 1.25*cm
        footerOffset  = 1.25*cm
        headerPadding = 0.50*cm
        footerPadding = 0.50*cm
        frameLandscape = Frame(doc.bottomMargin, doc.leftMargin+footerOffset, doc.height, doc.width-doc.leftMargin-headerOffset, topPadding=headerPadding, bottomPadding=footerPadding, id='landscape_frame ')
        framePortrait  = Frame(doc.leftMargin,   doc.topMargin+footerOffset,  doc.width,  doc.height-doc.topMargin-headerOffset, topPadding=headerPadding, bottomPadding=footerPadding, id='portrait_frame ' )

        doc.addPageTemplates([
                PageTemplate(id='portrait', frames=framePortrait,  onPage=partial(PageStyle.logosInternalPagenumber, landscape=False, numPages=numTotalPages+3, filename=filename)),
                PageTemplate(id='landscape',frames=frameLandscape, onPage=partial(PageStyle.logosInternalPagenumber, landscape=True , numPages=numTotalPages+3, filename=filename), pagesize=landscape(A4)),
            ])
        doc.build(story)
