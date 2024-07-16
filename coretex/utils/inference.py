from typing import Tuple, Optional, Union, Any
from pathlib import Path

import json
import uuid
import asyncio

from onnxruntime import InferenceSession

import ezkl
import numpy as np

from .. import folder_manager


async def genWitness(inputPath: Path, circuit: Path, witnessPath: Path) -> None:
    await ezkl.gen_witness(inputPath, circuit, witnessPath)


def runOnnxInference(
    data: np.ndarray,
    onnxPath: Path,
    compiledModelPath: Optional[Path] = None,
    proveKey: Optional[Path] = None
) -> Union[np.ndarray, Tuple[np.ndarray, Path]]:

    """
        Performs inference on the provided onnx model with the provided data and also generates
        a zero knowledge proof if a compiled model and key are passed.
        This can be used to verify that the result was gained by
        combining this specific model and input data.

        Parameters
        ----------
        data : ndarray
            data which will be directly fed to the model
        onnxPath : Path
            path to the onnx model
        compiledModelPath : Optional[Path]
            path to the compiled model
        proveKey : Optional[Path]
            path to the proving key file of the model

        Returns
        -------
        Union[np.ndarray, Tuple[np.ndarray, Path]]
            output of the model or, if compiledModelPath and proveKey are passed, output of the model and path to the proof
    """

    inferenceId = str(uuid.uuid1())

    session = InferenceSession(onnxPath)
    inputName = session.get_inputs()[0].name
    result = np.array(session.run(None, {inputName: data}))

    if compiledModelPath is None and proveKey is None:
        return result

    if compiledModelPath is None or proveKey is None:
        raise ValueError(f">> [Coretex] Parameters compiledModelPath and proveKey have to either both be passed or None")

    inferenceDir = folder_manager.createTempFolder(inferenceId)
    witnessPath = inferenceDir / "witness.json"
    inputPath = inferenceDir / "input.json"
    proofPath = inferenceDir / "proof.pf"

    flattenedData = np.array(data).reshape(-1).tolist()
    inputData = dict(input_data = [flattenedData])
    with inputPath.open("w") as file:
        json.dump(inputData, file)

    asyncio.run(genWitness(inputPath, compiledModelPath, witnessPath))
    ezkl.prove(
        witnessPath,
        compiledModelPath,
        proveKey,
        proofPath,
        "single"
    )

    return result, proofPath
