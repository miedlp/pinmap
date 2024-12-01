# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import pathlib as pl
import os

from pinmap.document.pdfgen import canvas

import pinmap.document.graphics as GraphicsHelper

def headerLogoInternal(canvas, doc, landscape: bool = False, logoPath: pl.Path, filename='') -> None:
    # Save the state of our canvas so we can draw on it
    canvas.saveState()
    logoPathAspect = GraphicsHelper.getImageSize(logoPath)
    if landscape:
        canvas.drawImage(logoPath, doc.topMargin, doc.width, width=logoPathAspect[0], height=logoPathAspect[1])
        canvas.drawRightString(doc.height, doc.width, filename)
    else:
        canvas.drawImage(logoPath, doc.leftMargin, doc.height, width=logoPathAspect[0], height=logoPathAspect[1])
        canvas.drawRightString(doc.width, doc.height, filename)
    # Release the canvas
    canvas.restoreState()

def footerLogoPagenumber(canvas, doc, landscape: bool = False, logoPath: pl.Path, numPages: int = 0, extraString: str = '') -> None:
    # Save the state of our canvas so we can draw on it
    canvas.saveState()
    logoPathAspect = GraphicsHelper.getImageSize(logoPath)
    pageNumStr = "%d/%d" % (canvas._pageNumber, numPages)
    if landscape:
        canvas.drawImage(logoPath, doc.topMargin, doc.leftMargin, width=logoPathAspect[0], height=logoPathAspect[1])
        canvas.drawCentredString((doc.height-doc.topMargin)/2+doc.topMargin, doc.leftMargin, extraString)
        canvas.drawRightString(doc.height, doc.leftMargin, pageNumStr)
    else:
        canvas.drawImage(logoPath, doc.leftMargin, doc.bottomMargin, width=logoPathAspect[0], height=logoPathAspect[1])
        canvas.drawCentredString((doc.width-doc.leftMargin)/2+doc.leftMargin, doc.bottomMargin, extraString)
        canvas.drawRightString(doc.width, doc.bottomMargin, pageNumStr)
    # Release the canvas
    canvas.restoreState()

def logosInternalPagenumber(canvas, doc, landscape: bool = False, headerLogoPath: pl.Path, footerLogoPath: pl.Path, numPages: int = 0, filename='') -> None:
    headerLogoInternal(canvas, doc, landscape, headerLogoPath, filename)
    footerLogoPagenumber(canvas, doc, landscape, footerLogoPath, numPages)

