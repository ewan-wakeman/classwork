from json import JSONEncoder, JSONDecoder
from typing import Any, Callable, Union, Dict
from .meta import CodecAbc


class ClassworkEncoder(JSONEncoder, CodecAbc):

    ...


class ClassworkDecoder(JSONDecoder, CodecAbc):
    def __init__(
        self,
        *,
        object_hook: Union[Callable[[Dict[str, Any]], Any], None] = None,
        **kwargs
    ) -> None:

        super().__init__(object_hook=object_hook, **kwargs)
