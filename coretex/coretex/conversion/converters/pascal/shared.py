#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Dict, Tuple

import xml.etree.ElementTree as ET


def getTag(root: ET.Element, tag: str) -> Optional[str]:
    element = root.find(tag)
    if element is None:
        return None

    return element.text


def toFloat(rootEl: ET.Element, firstEl: str, secondEl: str) -> Tuple[Optional[float], Optional[float]]:
    firstVal = getTag(rootEl, firstEl)
    secondVal = getTag(rootEl, secondEl)

    if firstVal is None or secondVal is None:
        return (None, None)

    return (float(firstVal), float(secondVal))


def toInt(rootEl: ET.Element, firstEl: str, secondEl: str) -> Tuple[Optional[int], Optional[int]]:
    firstVal = getTag(rootEl, firstEl)
    secondVal = getTag(rootEl, secondEl)

    if firstVal is None or secondVal is None:
        return (None, None)

    return (int(firstVal), int(secondVal))


def getBoxes(bndbox: ET.Element) -> Optional[Dict[str, float]]:
    xmin, ymin = toFloat(bndbox, "xmin", "ymin")
    xmax, ymax = toFloat(bndbox, "xmax", "ymax")

    if xmax is None: return None
    if xmin is None: return None
    if ymax is None: return None
    if ymin is None: return None

    return {
        "top_left_x": xmin,
        "top_left_y": ymin,
        "width": xmax - xmin,
        "height": ymax - ymin,
    }