# Copyright (c) 2023-2024 METTLER TOLEDO
# Copyright (c) 2024 Philipp Miedl
#
# SPDX-License-Identifier: EUPL-1.2

import importlib

def dependencyCheck(packageList: list[str]) -> None:
    exceptionMessage = ""
    for requiredPackage in packageList:
        if importlib.util.find_spec(requiredPackage) is None:
            exceptionMessage += "\n- " + requiredPackage
    if len(exceptionMessage) > 0:
      raise Exception("Following packages are missing, please install using pip install [package]:" + exceptionMessage)
