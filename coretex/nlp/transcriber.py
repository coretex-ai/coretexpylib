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

# from typing import Dict, Any, List, Tuple
# from pathlib import Path

# import wave
# import logging

# from deepspeech import Model

# import numpy as np

# from .token import Token
# from .utils import isTxtSample, getAudioFilePath
# from .transcription import Transcription
# from .text import loadTxtSample
# from ..coretex import CustomSample, CustomDataset
# from ..folder_management import FolderManager


# TranscriptionList = List[Tuple[CustomSample, Transcription]]


# def _instantiateModel(modelPath: Path, modelScorerPath: Path) -> Model:
#     model = Model(str(modelPath))
#     model.enableExternalScorer(str(modelScorerPath))

#     model.setScorerAlphaBeta(0.93, 1.18)  # 0.93 represents lm_alpha, and 1.18 represents lm_beta
#     model.setBeamWidth(100)  # 100 represents beam_width

#     return model


# def _readAudioFile(path: Path) -> bytes:
#     with wave.open(str(path), 'rb') as audioFile:
#         frames = audioFile.getnframes()
#         buffer = audioFile.readframes(frames)

#     return buffer


# def _hasCachedTranscription(dataset: CustomDataset, meta: Dict[str, Any]) -> bool:
#     fetchedDatasets = CustomDataset.fetchAll([
#         f"name={dataset.name}_cached",
#         "include_sessions=1"
#     ])

#     if fetchedDatasets != 1:
#         print("1", len(fetchedDatasets))
#         return False

#     cachedDataset = fetchedDatasets[0]
#     if cachedDataset.meta is None:
#         print("2", cachedDataset.meta)
#         return False

#     for key, value in meta.items():
#         if cachedDataset.meta.get(key) != value:
#             print("3", cachedDataset.meta.get(key), "!=", value)
#             return False

#     return True


# def _fetchCachedTranscription(dataset: CustomDataset, meta: Dict[str, Any]) -> TranscriptionList:
#     fetchedDatasets = CustomDataset.fetchAll([f"name={dataset.name}_cached"])
#     if fetchedDatasets != 1:
#         raise ValueError(">> [Coretex] Fetched more than one cached dataset")

#     cachedDataset = fetchedDatasets[0]
#     if cachedDataset.meta is None:
#         raise ValueError(">> [Coretex] Dataset.meta field is None")

#     for key, value in meta.items():
#         if cachedDataset.meta.get(key) != value:
#             raise ValueError(">> [Coretex] Dataset.meta field does not match parameters of TaskRun")

#     cachedDataset.download()

#     result: TranscriptionList = []

#     for sample in dataset.samples:
#         cachedSample = cachedDataset.getSample(f"{sample.name}_cached")
#         if cachedSample is None:
#             raise ValueError(f">> [Coretex] {sample.name} has invalid cache")

#         cachedSample.unzip()
#         folderContent = list(cachedSample.load().folderContent)

#         if len(folderContent) != 1:
#             raise ValueError(f">> [Coretex] {sample.name} has invalid cache")

#         result.append((sample, Transcription.load(folderContent[0])))

#     return result


# def _cacheTranscription(
#     dataset: CustomDataset,
#     transcriptions: TranscriptionList,
#     meta: Dict[str, Any]
# ) -> bool:

#     logging.info(">> [Coretex] Caching dataset transcription")

#     cachedDataset = CustomDataset.createDataset(f"{dataset.name}_cached", dataset.projectId, meta = meta)
#     if cachedDataset is None:
#         return False

#     try:
#         cachedSamplesPath = Path(FolderManager.instance().createTempFolder("cached_samples"))
#         for sample, transcription in transcriptions:
#             logging.info(f">> [Coretex] Caching sample: {sample.name}")

#             cachedSamplePath = transcription.save(cachedSamplesPath / f"{sample.name}.json")

#             cachedSample = CustomSample.createCustomSample(f"{sample.name}_cached", cachedDataset.id, str(cachedSamplePath))
#             if cachedSample is None:
#                 raise ValueError
#     except ValueError:
#         cachedDataset.delete()
#         return False

#     return True


# class AudioTranscriber:

#     """
#         Transcribes audio dataset into text, and tokens

#         Properties:
#         model: Model -> deepspeech model used for transcription
#         parameters: Dict[str, Any] -> parameters which affect model output,
#         these parameters are stored as metadata about cached dataset after transcription
#         has been performed
#     """

#     def __init__(self, modelPath: Path, modelScorerPath: Path, parameters: Dict[str, Any]):
#         self.model = _instantiateModel(modelPath, modelScorerPath)
#         self.parameters = parameters

#     def __transcribeSingle(self, sample: CustomSample, batchSize: int) -> Transcription:
#         logging.info(f">> [Coretex] Transcribing: {sample.name}")

#         sample.unzip()

#         if isTxtSample(sample):
#             return loadTxtSample(sample)

#         audioFilePath = getAudioFilePath(sample)
#         if audioFilePath is None:
#             raise ValueError(f">> [Coretex] {sample.name} does not contain a valid audio file")

#         stream = self.model.createStream()

#         buffer = _readAudioFile(audioFilePath)
#         offset = 0

#         while offset < len(buffer):
#             endOffset = offset + batchSize
#             chunk = buffer[offset:endOffset]

#             data16 = np.frombuffer(chunk, dtype = np.int16)
#             stream.feedAudioContent(data16)

#             text = stream.intermediateDecodeWithMetadata()
#             normalText = stream.intermediateDecode()

#             offset = endOffset

#         return Transcription.create(normalText, Token.fromTokenMetadata(text.transcripts[0].tokens))

#     def transcribe(
#         self,
#         dataset: CustomDataset,
#         batchSize: int,
#         ignoreCache: bool = False
#     ) -> TranscriptionList:

#         """
#             Transcribes audio dataset into text and separates
#             text into tokens.
#             If text sample is contained inside the dataset
#             it is also processed and tokenized

#             Parameters
#             ----------
#             dataset : CustomDataset
#                 dataset used for transcription
#             batchSize : int
#                 size of the chunk extracted for transcription
#             ignoreCache : bool
#                 if True cached dataset is ignored

#             Returns
#             -------
#             TranscriptionList -> list of tuples, each tuple contains sample and its transcription
#         """

#         # TODO: Enable once backend is working
#         # if not ignoreCache and _hasCachedTranscription(dataset, self.parameters):
#         #     logging.info(f">> [Coretex] Using cached transcription for: {dataset.name}")
#         #     return _fetchCachedTranscription(dataset, self.parameters)

#         result: TranscriptionList = []

#         for sample in dataset.samples:
#             result.append((sample, self.__transcribeSingle(sample, batchSize)))

#         # TODO: Enable once backend is working
#         # if _cacheTranscription(dataset, result, self.parameters):
#         #     logging.info(f">> [Coretex] Cached transcription for: {dataset.name}")
#         # else:
#         #     logging.info(f">> [Coretex] Failed to cache transcription for: {dataset.name}")

#         return result
