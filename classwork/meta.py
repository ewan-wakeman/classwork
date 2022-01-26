from abc import abstractmethod, ABCMeta
from enum import EnumMeta, Flag
from inspect import isfunction
from json import JSONDecoder, JSONEncoder
import operator
from typing import Dict, KeysView, Mapping, Any, Optional, Type, TypeVar, Union
from os import PathLike as ospath
from pathlib import Path
from logzero import logger

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

ClassworkType = TypeVar("ClassworkType", bound="ClassworkAbc")


class ClassworkAbc(metaclass=ClassworkMeta):
    """An abstract base class for all classes used in `classwork`. This class should be
    used either as a base class or a mixin class with another ABC defined in this file.
    Each"""

    def __new__(cls, params: Dict[str, Any] = {}, **kw):
        """Created a new instance of a class or one of its subclasses and optionally
        performs a check that any value provided to `_cls` (either as a keyword argument
        or as an item in the `params`) is the class from which the funciton invocation
        was called or a valid subclass of it. This ensures parameters loaded from json
        encoded versions of the the class are of the expected value."""

        # gather params and keyword args together
        params.update(kw)

        if "_cls" in params:
            kcls = {cls.cls_nm(): cls, cls.__qualname__: cls}
            kcls.update({_.cls_nm(): _ for _ in cls.__subclasses__()})
            kcls.update({_.__qualname__: _ for _ in cls.__subclasses__()})

            cls_nm = params.pop("_cls")
            try:
                _cls = kcls[cls_nm]
            except KeyError:
                raise Exception(f"Unknown class {cls_nm}")

            if "_params" in params:
                _params = params.pop("_params")
                params.update(_params)

            # if _cls was in params and identified a valid subclass (or itself)
            # then return an instance of that class with original parameters but no
            # _cls parameter and any _params in the main parameter dictionary
            inst = super().__new__(_cls)

        else:
            # return itself and call init
            inst = super().__new__(cls)

        return inst

    def __init__(
        self,
        params: Mapping[str, Any] = {},
        **kwargs,
    ):
        params = dict(params)
        if kwargs:
            params.update(kwargs)

        if "_cls" in params:
            del params["_cls"]

        self.update(params)

    @classmethod
    def cls_nm(cls: ClassworkMeta) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    @property
    @abstractmethod
    def encoder(self) -> Type[JSONEncoder]:
        ...

    @property
    @abstractmethod
    def decoder(self) -> Type[JSONDecoder]:
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
        cls: Type[ClassworkType],
        path: Optional[PathLike] = None,
        json_str: Optional[str] = None,
    ) -> ClassworkType:
        ...


class DefaultAbc(metaclass=DefaultsMeta):
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

        print(cls)
        for k, v in self.defaults.items():
            setattr(cls, k, v)

        setattr(cls, "_default_attrs", self.defaults)

        return cls


class KnownDefaultsAbc(Flag, metaclass=ClassworkEnumMeta):
    """An Abstract Base Class for `enum` objects which can be used with `.from_known`
    method on the DefaultAbc classes and subclasses"""

    ...


class CodecAbc(metaclass=CodecMeta):
    """An Abstract Base Class for codecs (encoders/decoders) as tagging for JSONEncoders
    and JSONDecoders"""

    ...


class GeographyAbc(Flag, metaclass=ClassworkEnumMeta):
    """An Abstract Base Class for `enum` objects which can be used to represent
    geographies"""

    ...


ParamsType = TypeVar("ParamsType", bound="ParamsAbc")


class ParamsAbc:
    def __init__(
        self,
        params={},
        **kwargs,
    ):
        prm_dict = {}
        prm_dict.update(params)
        prm_dict.update(kwargs)

        for attr in prm_dict:
            self[attr] = prm_dict[attr]

    def __getitem__(self, attr):
        hidden = f"_{attr}"
        if hasattr(self, attr):
            return getattr(self, attr)
        elif hasattr(self, hidden):
            return getattr(self, hidden)
        else:
            raise KeyError(f"attr {attr} not present on class")

    def __setitem__(self, attr, value):
        hidden = f"_{attr}" if not attr.startswith("_") else attr
        if hasattr(self, attr):
            setattr(self, attr, value)
        else:
            logger.debug(f"attr {attr} will be hidden and stored as {hidden}")
            setattr(self, hidden, value)

    def __iter__(self, *, hidden: bool = False, defaults: bool = False):
        for k in self.as_dict(hidden=hidden, defaults=defaults):
            yield self[k]

    def keys(self, *, hidden: bool = False, defaults: bool = False):
        return self.as_dict(hidden=hidden, defaults=defaults).keys()

    def as_dict(self, *, hidden: bool = False, defaults: bool = False):

        dct = {}

        if defaults:
            def_dct = {
                k: v
                for k, v in self.__class__.__dict__.items()
                if (not isfunction(v)) and (not k.startswith("__"))
            }
            dct.update(def_dct)

        dct.update(self.__dict__)
        if not hidden:
            dct = {k: v for k, v in dct.items() if not k.startswith("_")}

        return dct

    def update(self: ParamsType, other: Union[ParamsType, Dict[str, Any]]):
        """updates item to"""


OperableType = TypeVar("OperableType", bound="OperableAbc")


class OperableAbc(metaclass=ClassworkMeta):
    """
    Abstract mixin class for Parameter holding classes allowing for items of the same
    class to be combined mathematically.
    """

    @property
    @abstractmethod
    def _method(self) -> str:
        """
        default mathematical method for a class usually default would be "=" or "assign"
        """
        ...

    @abstractmethod
    def __getitem__(self, attr) -> Any:
        ...

    @abstractmethod
    def __setitem__(self, attr, value):
        ...

    @abstractmethod
    def keys(self) -> KeysView:
        ...

    @abstractmethod
    def as_dict(self, **kwargs) -> Dict[str, Any]:
        ...

    def _op(
        self: OperableType, other: OperableType, _method: Optional[str] = None
    ) -> OperableType:

        op_dct = {
            "=": lambda x, y: y,
            "assign": lambda x, y: y,
            "+": operator.add,
            "add": operator.add,
            "-": operator.sub,
            "sub": operator.sub,
            "*": operator.mul,
            "mul": operator.mul,
            "/": operator.truediv,
            "truediv": operator.truediv,
        }

        assert other.__class__ is self.__class__, (
            "Can only add together items of the same class "
            f"not ({self.__class__}, {other.__class__})"
        )

        if not _method:
            _method = other._method

        try:
            fn = op_dct[_method]
        except KeyError:
            raise AttributeError(f"method {other._method} not availible")

        sdct = self.as_dict()

        dct = {k: fn(self[k], other[k]) for k in other.keys()}

        sdct.update(dct)

        return self.__class__(**sdct)

    def __add__(self: OperableType, other: OperableType) -> OperableType:
        return self._op(other, _method="add")
