from enum import Enum


class ParameterType(Enum):

    integer       = "int"
    floatingPoint = "float"
    string        = "str"
    boolean       = "bool"
    dataset       = "dataset"
    imuVectors    = "IMUVectors"
    enum          = "enum"
    intList       = "list[int]"
    floatList     = "list[float]"
    strList       = "list[str]"
    enumList      = "list[enum]"
