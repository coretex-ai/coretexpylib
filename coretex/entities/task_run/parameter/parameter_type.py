from enum import Enum


class ParameterType(Enum):

    integer       = "int"
    floatingPoint = "float"
    string        = "str"
    boolean       = "bool"
    dataset       = "dataset"
    model         = "model"
    imuVectors    = "IMUVectors"
    enum          = "enum"
    intList       = "list[int]"
    floatList     = "list[float]"
    strList       = "list[str]"
    datasetList   = "list[dataset]"
    modelList     = "list[model]"
    enumList      = "list[enum]"
