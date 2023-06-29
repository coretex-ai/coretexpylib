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

from typing import Any, Optional, List, Dict

import os
import xml.etree.ElementTree as ET

from PIL import Image
from skimage import measure
from shapely.geometry import Polygon

import numpy as np

from .shared import getTag, getBoxes
from ....annotation import CoretexSegmentationInstance, BBox
from ....dataset import ImageDataset


ContourPoints = List[List[int]]
SegmentationPolygon = List[ContourPoints]


class ObjectCandidate:

    """
        Represents the groundtruth object for contour matching
    """

    def __init__(self, object: ET.Element):
        self.object = object
        self.matched = False


class ContourCandidate:

    """
        Represents the extracted contour from segmentation mask
    """

    def __init__(self, contours: ContourPoints, iou: Optional[float] = None):
        if iou is None:
            iou = 0.0

        self.contours = contours
        self.iou = iou
        self.matched = False


class InstanceExtractor:

    def __init__(self, dataset: ImageDataset) -> None:
        self.__dataset = dataset

    def createSubmasks(self, maskImage: Image) -> Dict[str, Any]:
        """
            Creates submasks for each segmentation mask

            Parameters
            ----------
            maskImage : Image
                Segmentation mask

            Returns
            -------
            Dict[str, Any] -> Dictionary with submask image and color
        """

        width, height = maskImage.size

        # Initialize a dictionary of sub-masks indexed by RGB colors
        subMasks: Dict[str, Any] = {}
        for x in range(width):
            for y in range(height):
                # Get the RGB values of the pixel
                pixel = maskImage.getpixel((x, y))[:3]

                if pixel == (0, 0, 0):
                    continue

                pixelStr = str(pixel)
                subMask = subMasks.get(pixelStr)
                if subMask is None:
                    subMasks[pixelStr] = Image.new('1', (width + 2, height + 2))

                # Set the pixel value to 1 (default is 0), accounting for padding
                subMasks[pixelStr].putpixel((x + 1, y + 1), 1)

        return subMasks

    def reshapeContour(self, candidate: ContourCandidate) -> ContourPoints:
        listOfPoints: ContourPoints = []

        for segmentContour in candidate.contours:
            for value in range(0, len(segmentContour) - 1, 2):
                point = [segmentContour[value], segmentContour[value + 1]]
                listOfPoints.append(point)

        return listOfPoints

    def calculateIoU(self, boxA: Dict[str, float], boxB: List[float]) -> float:
        """
            Calculates area of overlap for object boxes and contour boxes

            Parameters
            ----------
            boxA : Dict[str, float]
                annotated object boxes
            boxB : Dict[str, float]
                extracted boxes from contour

            Returns
            -------
            Value of boxes area overlap
        """

        xmax = boxA['top_left_x'] + boxA['width']
        ymax = boxA['top_left_y'] + boxA['height']

        xA = max(boxA['top_left_x'], boxB[0])
        yA = max(boxA['top_left_y'], boxB[1])
        xB = min(xmax, boxB[2])
        yB = min(ymax, boxB[3])

        # Compute the area of intersection rectangle
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

        # Compute the area of both the prediction and ground-truth rectangles
        boxAArea = (xmax - boxA['top_left_x'] + 1) * (ymax - boxA['top_left_y'] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

        return interArea / float(boxAArea + boxBArea - interArea)

    def boxesOverlap(self, bbox: Dict[str, Any], listOfPoints: ContourPoints) -> float:
        """
            Extracts boxes from contour and calculates IoU

            Parameters
            ----------
            bbox : Dict[str, Any]
                annotated object boxes
            listOfPoints : ContourPoints
                contour points

            Returns
            -------
            float -> Calculated overlap of boxes area
        """

        xmin: Optional[float] = None
        ymin: Optional[float] = None
        xmax: Optional[float] = None
        ymax: Optional[float] = None

        for point in listOfPoints:
            currentX = point[0]
            currentY = point[1]

            if xmin is None or xmax is None:
                xmin = currentX
                xmax = currentX

            if ymin is None or ymax is None:
                ymin = currentY
                ymax = currentY

            # get xmin, xmax, ymin, ymax
            xmin = min(xmin, currentX)
            ymin = min(ymin, currentY)
            xmax = max(xmax, currentX)
            ymax = max(ymax, currentY)

        if xmax is not None and xmin is not None and ymin is not None and ymax is not None:
            contourBox = [xmin, ymin, xmax, ymax]
            iou = self.calculateIoU(bbox, contourBox)

        return iou

    def matchContour(self, bbox: Dict[str, Any], objectCandidate: ObjectCandidate, contourCandidates: List[ContourCandidate]) -> ContourPoints:
        """
            Matches object and contour with max area of overlap

            Parameters
            ----------
            bbox : Dict[str, Any]
                annotated object boxes
            objectCandidate : ObjectCandidate
                groundtruth object
            contourCandidates : List[ContourCandidate]
                list of ContourCandidate objects

            Returns
            -------
            ContourPoints -> The corresponding contour which matches given object
        """

        maxIoU = -1.0
        contourIndex = 0

        for candidate in contourCandidates:
            if candidate.matched:
                continue

            listOfPoints = self.reshapeContour(candidate)
            candidate.iou = self.boxesOverlap(bbox, listOfPoints)

            if maxIoU < candidate.iou:
                maxIoU = candidate.iou
                contourIndex = contourCandidates.index(candidate)

        objectCandidate.matched = True
        contourCandidates[contourIndex].matched = True

        return contourCandidates[contourIndex].contours

    def extractSubmaskContours(self, subMask: Image) -> ContourPoints:
        """
            Extracts contours from submask image

            Parameters
            ----------
            subMask : Image
                binary image

            Returns
            -------
            ContourPoints -> List of contours
        """

        subMaskArray = np.asarray(subMask)
        contours = measure.find_contours(subMaskArray, 0.5)

        segmentations: ContourPoints = []
        for contour in contours:
            for i in range(len(contour)):
                row, col = contour[i]
                contour[i] = (col - 1, row - 1)

            # Make a polygon and simplify it
            poly = Polygon(contour)
            #poly = poly.simplify(1.0, preserve_topology=False)

            if poly.geom_type == 'MultiPolygon':
                # If MultiPolygon, take the smallest convex Polygon containing all the points in the object
                poly = poly.convex_hull

            # Ignore if still not a Polygon (could be a line or point)
            if poly.geom_type == 'Polygon':
                segmentation = np.array(poly.exterior.coords).ravel().tolist()
                segmentations.append(segmentation)

        return segmentations

    def getSegmentationInstance(
        self,
        objectCandidate: ObjectCandidate,
        contourCandidates: Optional[List[ContourCandidate]]=None
    ) -> Optional[CoretexSegmentationInstance]:

        label = getTag(objectCandidate.object, "name")
        if label is None:
            return None

        clazz = self.__dataset.classByName(label)
        if clazz is None:
            return None

        bndbox = objectCandidate.object.find('bndbox')
        if bndbox is None:
            return None

        boxes = getBoxes(bndbox)
        if boxes is None:
            return None

        polygon: ContourPoints = []
        if contourCandidates is not None:
            polygon = self.matchContour(boxes, objectCandidate, contourCandidates)

        bbox = BBox.decode(boxes)

        if len(polygon) == 0:
            polygon = [bbox.polygon]

        return CoretexSegmentationInstance.create(clazz.classIds[0], bbox, polygon)

    def __extractNonSegmentedInstances(self, objectCandidates: List[ObjectCandidate]) -> List[CoretexSegmentationInstance]:
        coretexInstances: List[CoretexSegmentationInstance] = []

        for objectCandidate in objectCandidates:
            instance = self.getSegmentationInstance(objectCandidate)
            if instance is None:
                continue

            coretexInstances.append(instance)

        return coretexInstances

    def __extractSegmentedInstances(
        self,
        segmentationPath: str,
        filename: str,
        objectCandidates: List[ObjectCandidate]
    ) -> List[CoretexSegmentationInstance]:

        maskImage = Image.open(os.path.join(segmentationPath, filename))
        if maskImage is None:
            return []

        contourCandidates: List[ContourCandidate] = []

        maskImage = maskImage.convert("RGB")
        subMasks = self.createSubmasks(maskImage)

        for color, subMask in subMasks.items():
            # Ignore border contours
            if color == '(224, 224, 192)':
                continue

            annotation = self.extractSubmaskContours(subMask)
            contourCandidates.append(ContourCandidate(annotation))

        coretexInstances: List[CoretexSegmentationInstance] = []

        for objectCandidate in objectCandidates:
            if objectCandidate.matched:
                continue

            instance = self.getSegmentationInstance(objectCandidate, contourCandidates)
            if instance is None:
                continue

            coretexInstances.append(instance)

        return coretexInstances

    def extractInstances(
        self,
        root: ET.Element,
        filename: str,
        segmentationPath: str
    ) -> List[CoretexSegmentationInstance]:
        """
            Extracts polygons from segmentation masks and creates instances

            Parameters
            ----------
            filename : str
                file with annotations
            objects : List[ET.Element]
                annotated objects
        """

        objects = root.findall("object")
        objectCandidates: List[ObjectCandidate] = [ObjectCandidate(obj) for obj in objects]

        segmented = getTag(root, "segmented")
        if segmented is not None:
            isSegmented = bool(int(segmented))

            if isSegmented:
                return self.__extractSegmentedInstances(segmentationPath, filename, objectCandidates)
            else:
                return self.__extractNonSegmentedInstances(objectCandidates)

        # TODO: Raise error or fallback to extracting non-segmented instances?
        raise RuntimeError(">> [Coretex] (segmented) XML tag missing")
