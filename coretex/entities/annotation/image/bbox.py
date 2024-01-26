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

from typing import Final, List, Dict
from typing_extensions import Self

from ....codable import Codable, KeyDescriptor


class BBox(Codable):

    """
        Bounding Box as a python class with utility methods

        Properties
        ----------
        minX : int
            top left x coordinate
        minY : int
            top left y coordinate
        width : int
            width of the bounding box
        height : int
            height of the bounding box
    """

    def __init__(self, minX: int = 0, minY: int = 0, width: int = 0, height: int = 0) -> None:
        self.minX: Final = minX
        self.minY: Final = minY

        self.width: Final = width
        self.height: Final = height

    @property
    def maxX(self) -> int:
        """
            Returns
            -------
            int -> bottom right x coordinate
        """

        return self.minX + self.width

    @property
    def maxY(self) -> int:
        """
            Returns
            -------
            int -> bottom right y coordinate
        """

        return self.minY + self.height

    @property
    def polygon(self) -> List[int]:
        """
            Returns
            -------
            List[int] -> Bounding box represented as a polygon (x, y) values
        """

        return [
            self.minX, self.minY,  # top left
            self.maxX, self.minY,  # top right
            self.maxX, self.maxY,  # bottom right
            self.minX, self.maxY,  # bottom left
            self.minX, self.minY   # top left
        ]

    @property
    def area(self) -> int:
        return self.width * self.height

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["minX"] = KeyDescriptor("top_left_x")
        descriptors["minY"] = KeyDescriptor("top_left_y")

        return descriptors

    @classmethod
    def create(cls, minX: int, minY: int, maxX: int, maxY: int) -> Self:
        """
            Utility constructor which has maxX and maxY as parameters instead
            of width and height

            Parameters
            ----------
            minX : int
                top left x coordinate
            minY : int
                top left y coordinate
            maxX : int
                bottom right x coordinate
            maxY : int
                bottom right y coordinate

            Returns
            -------
            Self -> bounding box
        """

        return cls(minX, minY, maxX - minX, maxY - minY)

    @classmethod
    def fromPoly(cls, polygon: List[int]) -> Self:
        """
            Creates bounding box from a polygon, by finding
            the minimum x and y coordinates and calculating
            width and height of the polygon

            Parameters
            ----------
            polygon : List[int]
                list of x, y points - length must be even

            Returns
            -------
            Self -> bounding box

            Example
            -------
            >>> from coretex import Bbox
            \b
            >>> polygon = [0, 0, 0, 3, 4, 3, 4, 0]
            >>> bbox = Bbox.fromPoly(polygon)
            >>> print(f"minX: {bbox.minX}, minY: {bbox.minY}, width: {bbox.width}, height: {bbox.height}")
            "minX: 0, minY: 0, width: 4, height: 3"
        """

        x: List[int] = []
        y: List[int] = []

        for index, value in enumerate(polygon):
            if index % 2 == 0:
                x.append(value)
            else:
                y.append(value)

        return cls.create(min(x), min(y), max(x), max(y))

    def iou(self, other: 'BBox') -> float:
        """
            Calculate Intersection over Union (IoU) between two bounding boxes

            Parameters:
            other : BBox
                bounding box for which the IoU will be calculated

            Returns
            float -> IoU score
        """

        x1 = max(self.minX, other.minX)
        y1 = max(self.minY, other.minY)
        x2 = min(self.maxX, other.maxX)
        y2 = min(self.maxY, other.maxY)

        intersectionArea = max(0, x2 - x1) * max(0, y2 - y1)

        unionArea = self.area + other.area - intersectionArea
        return intersectionArea / unionArea if unionArea > 0 else 0.0
