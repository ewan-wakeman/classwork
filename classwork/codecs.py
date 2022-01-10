from json import JSONEncoder, JSONDecoder
from .meta import CodecABC


class ClassworkEncoder(CodecABC, JSONEncoder):

    ...


class ClassworkDecoder(CodecABC, JSONDecoder):
    ...
