from enum import IntEnum


class NodeMode(IntEnum):

    execution         = 1
    functionExclusive = 2
    functionShared    = 3
