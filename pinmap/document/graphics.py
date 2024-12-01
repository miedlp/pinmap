# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import pathlib as pl

from pinmap.document.lib.utils import ImageReader
from pinmap.document.lib.units import cm

def getImageSize(path: pl.Path, height: float|int = 0.5*cm) -> tuple[float|int,float|int]:
    img = ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return (height / aspect, height)
