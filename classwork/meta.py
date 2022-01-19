from abc import abstractmethod, ABCMeta
from enum import EnumMeta, Flag
from typing import Dict, Mapping, Any, Optional, TypeVar, Union
from os import PathLike as ospath
from pathlib import Path
from logzero import logger

_Type = TypeVar("_Type")
PathLike = Union[ospath, str]

# Metaclasses
# Parent metaclasses for the types of class used in classwork


class ClassworkMeta(ABCMeta):
    "A metaclass for all classes belonging to the `classwork` package"
    ...


class CodecMeta(ClassworkMeta):
    "A metaclass for `classwork` codecs (encoders/decoders)"
    ...


class DefaultsMeta(ClassworkMeta):
    "A metaclass for classes which assign defaults to decorated classes"
    ...


class ClassworkEnumMeta(EnumMeta, ClassworkMeta):
    "A metaclass for enums in `classwork`"
    ...


class ParamMeta(ClassworkMeta):
    "A metclass for parameter holding classes in classwork"
    ...


class SetMeta(ClassworkMeta):
    """A metaclass for sets of parameter holding classes derivedfrom `ParamMeta` and
    `ParamAbc`"""


# Abstract Base Classes (ABCs)


class ClassworkABC(metaclass=ClassworkMeta):
    """An abstract base class for all classes used in `classwork`. This class should be
    used either as a base class or a mixin class with another ABC defined in this file.
    Each"""

    def __init__(
        self,
        params: Mapping[str, Any] = {},
        ignore_check: bool = False,
        **kwargs,
    ):
        params = dict(params)
        if kwargs:
            params.update(kwargs)

        params = self._check_params(params, ignore_check)

        self.update(params)

    @classmethod
    def _check_params(
        cls, params: Dict[str, Any], ignore_check: bool = False
    ) -> Dict[str, Any]:
        if not ignore_check:
            kn_cls = {cls.__name__: cls}
            for subcls in cls.__subclasses__():
                kn_cls[subcls.__name__] = subcls

            if "_cls" in params:
                _cls = params.pop("_cls")
                try:
                    _cls = kn_cls[_cls]
                except KeyError:
                    raise AttributeError(
                        f"__init__ recieved object encoded as {_cls} but requires "
                        f"{cls} or on of its subclasses "
                        f"{[kn_cls[x] for x in kn_cls if x != cls.__name__]}."
                    )

        if "_params" in params:
            _params = params.pop("_params")
            params.update(_params)

        return params

    @property
    @abstractmethod
    def encoder(self) -> CodecMeta:
        ...

    @property
    @abstractmethod
    def decoder(self) -> CodecMeta:
        ...

    @abstractmethod
    def __getitem__(self, attr: str) -> Any:

        if not isinstance(attr, str):
            raise AttributeError(
                f"`attr` must be a string, recieved {attr} ({type(attr)})."
            )

        if not hasattr(self, attr):
            raise KeyError(f"Object has no attr {attr}.")

        return getattr(self, attr)

    @abstractmethod
    def __setitem__(self, attr: str, value: Any) -> None:

        if not isinstance(attr, str):
            logger.warning("Attribute name is not a string. Attempting to convert...")
            try:
                attr = str(attr)
            except Exception:
                raise AttributeError(
                    "Attribute has no str implementation and cannot be used as a key"
                )

        setattr(self, attr, value)

    @abstractmethod
    def asdict(self) -> Dict[Any, Any]:
        return self.__dict__

    @abstractmethod
    def update(self, params: Mapping[str, Any] = {}, **kwargs) -> None:
        params = dict(params)
        if kwargs:
            params.update(kwargs)

        for attr, value in params.items():
            self[attr] = value

    @abstractmethod
    def to_json_file(self, path: PathLike, **kwargs) -> Path:
        ...

    @abstractmethod
    def to_json_str(self, **kwargs) -> str:
        ...

    @classmethod
    @abstractmethod
    def from_json(
        cls: _Type, path: Optional[PathLike] = None, json_str: Optional[str] = None
    ) -> _Type:
        ...


class DefaultAbc(ClassworkABC, metaclass=DefaultsMeta):
    """
    A Base Class for assigning default values to another class.

    When initialised with a dict or named args, the defaults attributes
    are set. When an class based on DefaultAbc is called with another
    uninitialised class, it will return that class with a default attributes
    set."""

    defaults: Dict[str, Any] = {}

    @abstractmethod
    def __init__(self, params: Dict[str, Any] = {}, **kwargs):
        """
        For setting default attrs. This signature must be reimplemented on
        inheriting classes when implemented. This is to encourage good
        documentation practices including implementation of docstrings. The
        default super().__init__() method can be reused however in most cases.
        """
        params.update(kwargs)
        self.defaults = params

    @abstractmethod
    def __call__(self, cls: ClassworkMeta) -> ClassworkMeta:
        """For assigning default attrs to another class. This signature must
        be reimplemented on inheriting classes when implemented. This is to
        encourage good documentation practices including implementation of
        docstrings. The default super().__init__() method can be reused
        however in most cases."""
        for k, v in self.defaults.items():
            setattr(cls, k, v)

        return cls


class KnownDefaultsABC(Flag, metaclass=ClassworkEnumMeta):
    ...


class CodecABC(metaclass=CodecMeta):
    ...


class GeographyABC(Flag, metaclass=ClassworkEnumMeta):
    ...
