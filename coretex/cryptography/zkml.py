from typing import Tuple, Optional
from pathlib import Path

import hashlib
import logging
import json
import uuid
import asyncio

from onnxruntime import InferenceSession

import ezkl
import numpy as np

from .. import folder_manager


def hashOnnxModel(modelPath: Path, length: int = 32) -> str:
    sha256 = hashlib.sha256()
    with modelPath.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()[:length]


async def compileOnnxModel(onnx: Path, compiledModel: Path, inputPath: Path, private: Optional[str]) -> None:
    circuitDir = compiledModel.parent
    proofKey = circuitDir / "proof.key"
    verifKey = circuitDir / "verification.key"
    settings = circuitDir / "settings.json"

    pyRunArgs = ezkl.PyRunArgs()

    pyRunArgs.input_visibility = "private" if private == "data" else "public"
    pyRunArgs.output_visibility = "public"
    pyRunArgs.param_visibility =  "private" if private == "model" else "fixed"

    ezkl.gen_settings(onnx, settings, py_run_args = pyRunArgs)
    await ezkl.calibrate_settings(inputPath, onnx, settings, target = "resources", max_logrows = 12, scales = [2])

    logging.info(f">> [Coretex] Compiling circuit {onnx.root}")
    ezkl.compile_circuit(onnx, compiledModel, settings)
    await ezkl.get_srs(settings)
    ezkl.setup(compiledModel, verifKey, proofKey)


def createCircuit(onnx: Path, inputPath: Path, private: Optional[str]) -> Tuple[Path, Path]:
    modelHash = hashOnnxModel(onnx)
    modelDir = folder_manager.temp / modelHash
    modelDir.mkdir(exist_ok = True)

    compiledModel = modelDir / f"{modelHash[:8]}.circuit"
    if not compiledModel.exists():
        print("Compiling model")
        asyncio.run(compileOnnxModel(onnx, compiledModel, inputPath, private))

    return compiledModel, modelDir / "proof.key"


async def gen_witness(inputPath: Path, circuit: Path, witnessPath: Path) -> None:
    await ezkl.gen_witness(inputPath, circuit, witnessPath)


def runVerifiedInference(onnx: Path, data: np.ndarray, private: Optional[str] = None) -> Tuple[np.ndarray, Path]:
    """
        Performs inference on the provided onnx model with the provided data and generates
        a zero knowledge proof, which can be used to verify that the result was gained by
        combining this specific model and input data with comparatively cheap computation.

        Parameters
        ----------
        onnx : Path
            path to the onnx model
        data : ndarray
            data which will be directly fed to the model
        private : Optinal[str]
            what part is private. Possible values: `\"model\"`, `\"data\"` and `None`

        Returns
        -------
        tuple[ndarray, Path]
            output of the model and path to the proof
    """

    if private not in [None, "model", "data"]:
        raise ValueError(">> [Coretex] Parameter private ro runVerifiedInference must be either \"model\", \"data\" or None")

    inferenceId = str(uuid.uuid1())

    session = InferenceSession(onnx)
    inputName = session.get_inputs()[0].name
    result = session.run(None, {inputName: data})

    inferenceDir = folder_manager.createTempFolder(inferenceId)
    witnessPath = inferenceDir / "witness.json"
    inputPath = inferenceDir / "input.json"
    proofPath = inferenceDir / "proof.pf"

    flattenedData = np.array(data).reshape(-1).tolist()
    inputData = dict(input_data = [flattenedData])
    with inputPath.open("w") as file:
        json.dump(inputData, file)

    circuit, pkPath = createCircuit(onnx, inputPath, private)

    asyncio.run(gen_witness(inputPath, circuit, witnessPath))
    ezkl.prove(
        witnessPath,
        circuit,
        pkPath,
        proofPath,
        "single"
    )

    return result, proofPath
