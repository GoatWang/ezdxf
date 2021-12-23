#  Copyright (c) 2021, Manfred Moitzi
#  License: MIT License
from typing import Dict, Any, Optional, List, Tuple, Iterator, TYPE_CHECKING

from ezdxf import colors
from ezdxf.lldxf import validator, const

if TYPE_CHECKING:
    from ezdxf.document import Drawing

__all__ = ["GfxAttribs"]


DEFAULT_LAYER = "0"
DEFAULT_ACI_COLOR = colors.BYLAYER
DEFAULT_TRUE_COLOR = (-1, -1, -1)
DEFAULT_LINETYPE = "ByLayer"
DEFAULT_LINEWEIGHT = const.LINEWEIGHT_BYLAYER
DEFAULT_TRANSPARENCY = 0.0
DEFAULT_LTSCALE = 1.0


class GfxAttribs:
    """
    Represents often used DXF attributes of graphical entities.

    .. versionadded:: 0.18

    Args:
        layer (str): layer name as string
        color (int): :ref:`ACI` color value as integer
        rgb: RGB true color (red, green, blue) tuple, each channel value in the
            range from 0 to 255
        linetype (str): linetype name, does not check if the linetype exist!
        lineweight (int):  see :ref:`lineweights` documentation for valid values
        transparency (float): transparency value in the range from 0.0 to 1.0,
            where 0.0 is opaque and 1.0 if fully transparent
        ltscale (float): linetype scaling value > 0.0, default value is 1.0


    Raises:
        DXFValueError: invalid attribute value

    """

    _layer: str = DEFAULT_LAYER
    _aci_color: int = DEFAULT_ACI_COLOR
    _true_color: colors.RGB = DEFAULT_TRUE_COLOR
    _linetype: str = DEFAULT_LINETYPE
    _lineweight: int = DEFAULT_LINEWEIGHT
    _transparency: float = DEFAULT_TRANSPARENCY
    _ltscale: float = DEFAULT_LTSCALE

    def __init__(
        self,
        *,
        layer: str = DEFAULT_LAYER,
        color: int = DEFAULT_ACI_COLOR,
        rgb: colors.RGB = None,
        linetype: str = DEFAULT_LINETYPE,
        lineweight: int = DEFAULT_LINEWEIGHT,
        transparency: float = DEFAULT_TRANSPARENCY,
        ltscale: float = DEFAULT_LTSCALE,
    ):
        self.layer = layer
        self.color = color
        self.rgb = rgb
        self.linetype = linetype
        self.lineweight = lineweight
        self.transparency = transparency
        self.ltscale = ltscale

    def __str__(self) -> str:
        s = []
        if self._layer != DEFAULT_LAYER:
            s.append(f"layer='{self._layer}'")
        if self._aci_color != DEFAULT_ACI_COLOR:
            s.append(f"color={self._aci_color}")
        if self._true_color is not DEFAULT_TRUE_COLOR:
            s.append(f"rgb={self._true_color}")
        if self._linetype != DEFAULT_LINETYPE:
            s.append(f"linetype='{self._linetype}'")
        if self._lineweight != DEFAULT_LINEWEIGHT:
            s.append(f"lineweight={self._lineweight}")
        if self._transparency != DEFAULT_TRANSPARENCY:
            s.append(f"transparency={round(self._transparency, 3)}")
        if self._ltscale != DEFAULT_LTSCALE:
            s.append(f"ltscale={round(self._ltscale, 3)}")

        return ", ".join(s)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Returns iter(self)."""
        return iter(self.items())

    def items(self) -> List[Tuple[str, Any]]:
        """Returns the DXF attributes as list of name, value pairs."""
        data: List[Tuple[str, Any]] = []
        if self._layer != DEFAULT_LAYER:
            data.append(("layer", self._layer))
        if self._aci_color != DEFAULT_ACI_COLOR:
            data.append(("color", self._aci_color))
        if self._true_color is not DEFAULT_TRUE_COLOR:
            data.append(("true_color", colors.rgb2int(self._true_color)))
        if self._linetype != DEFAULT_LINETYPE:
            data.append(("linetype", self._linetype))
        if self._lineweight != DEFAULT_LINEWEIGHT:
            data.append(("lineweight", self.lineweight))
        if self._transparency != DEFAULT_TRANSPARENCY:
            data.append(
                ("transparency", colors.float2transparency(self._transparency))
            )
        if self._ltscale != DEFAULT_LTSCALE:
            data.append(("ltscale", self._ltscale))
        return data

    def asdict(self) -> Dict[str, Any]:
        """Returns the DXF attributes as :class:`dict`."""
        return dict(self.items())

    @property
    def layer(self) -> str:
        """layer name"""
        return self._layer

    @layer.setter
    def layer(self, name: str):
        if validator.is_valid_layer_name(name):
            self._layer = name
        else:
            raise const.DXFValueError(f"invalid layer name '{name}'")

    @property
    def color(self) -> int:
        """:ref:`ACI` color value"""
        return self._aci_color

    @color.setter
    def color(self, value: int):
        if validator.is_valid_aci_color(value):
            self._aci_color = value
        else:
            raise const.DXFValueError(f"invalid ACI color value '{value}'")

    @property
    def rgb(self) -> Optional[colors.RGB]:
        """true color value as (red, green, blue) tuple"""
        _rgb = self._true_color
        if _rgb is DEFAULT_TRUE_COLOR:
            return None
        return _rgb

    @rgb.setter
    def rgb(self, value: Optional[colors.RGB]):
        if value is None:
            self._true_color = DEFAULT_TRUE_COLOR
        elif validator.is_valid_rgb(value):
            self._true_color = value
        else:
            raise const.DXFValueError(f"invalid true color value '{value}'")

    @property
    def linetype(self) -> str:
        """linetype name"""
        return self._linetype

    @linetype.setter
    def linetype(self, name: str):
        if validator.is_valid_table_name(name):
            self._linetype = name
        else:
            raise const.DXFValueError(f"invalid linetype name '{name}'")

    @property
    def lineweight(self) -> int:
        """lineweight"""
        return self._lineweight

    @lineweight.setter
    def lineweight(self, value: int):
        if validator.is_valid_lineweight(value):
            self._lineweight = value
        else:
            raise const.DXFValueError(f"invalid lineweight value '{value}'")

    @property
    def transparency(self) -> float:
        """transparency value, 0.0 is opaque, 1.0 is fully transparent"""
        return self._transparency

    @transparency.setter
    def transparency(self, value: float):
        if isinstance(value, float) and (0.0 <= value <= 1.0):
            self._transparency = value
        else:
            raise const.DXFValueError(f"invalid transparency value '{value}'")

    @property
    def ltscale(self) -> float:
        """linetype scaling factor"""
        return self._ltscale

    @ltscale.setter
    def ltscale(self, value: float):
        if isinstance(value, (float, int)) and (value > 1e-6):
            self._ltscale = float(value)
        else:
            raise const.DXFValueError(f"invalid linetype scale value '{value}'")

    @classmethod
    def load_from_header(cls, doc: "Drawing") -> "GfxAttribs":
        """Load default DXF attributes from the HEADER section.

        There is no default true color value and the default transparency is not
        stored in HEADER section.

        Loads following header variables:

            - ``$CLAYER`` - current layer name
            - ``$CECOLOR`` - current ACI color
            - ``$CELTYPE`` - current linetype name
            - ``$CELWEIGHT`` - current lineweight
            - ``$CELTSCALE`` - current linetype scaling factor

        """
        header = doc.header
        return cls(
            layer=header.get("$CLAYER", DEFAULT_LAYER),
            color=header.get("$CECOLOR", DEFAULT_ACI_COLOR),
            linetype=header.get("$CELTYPE", DEFAULT_LINETYPE),
            lineweight=header.get("$CELWEIGHT", DEFAULT_LINEWEIGHT),
            ltscale=header.get("$CELTSCALE", DEFAULT_LTSCALE),
        )

    def write_to_header(self, doc: "Drawing") -> None:
        """Write DXF attributes as default values to HEADER section.

        Writes following header variables:

            - ``$CLAYER`` - current layer name, if exist in `doc`
            - ``$CECOLOR`` - current ACI color
            - ``$CELTYPE`` - current linetype name, if exist in `doc`
            - ``$CELWEIGHT`` - current lineweight
            - ``$CELTSCALE`` - current linetype scaling factor

        """
        header = doc.header
        if doc.layers.has_entry(self.layer):
            header["$CLAYER"] = self.layer
        header["$CECOLOR"] = self.color
        if doc.linetypes.has_entry(self.linetype):
            header["$CELTYPE"] = self.linetype
        header["$CELWEIGHT"] = self.lineweight
        header["$CELTSCALE"] = self.ltscale

