from dataclasses import dataclass, field
from enum import Enum
from numbers import Number


class FontType(Enum):
    COURIER = "Courier"
    TIMES = "Times"
    HELVETICA = "Helvetica"


@dataclass
class Margins:
    top: Number = 2
    right: Number = 2
    bottom: Number = 2
    left: Number = 2


@dataclass
class DecimalConfig:
    price_precision: int = 2
    quantity_precision: int = 2


@dataclass
class DanfceConfig:
    """
    Configurações do layout de DANFCe (cupom NFC-e).

    As margens e precisões padrão são pensadas para impressoras térmicas
    de 80mm, podendo ser sobrescritas conforme necessidade.
    """

    margins: Margins = field(default_factory=Margins)
    decimal_config: DecimalConfig = field(default_factory=DecimalConfig)
    font_type: FontType = FontType.TIMES
    # Largura da bobina em mm. 80 e 58 são os formatos usuais das
    # impressoras térmicas não fiscais.
    paper_width: Number = 80
    # Altura da página. O padrão (None) gera uma página única com a altura
    # exata do conteúdo, que é como a bobina contínua funciona. Fixar um
    # valor volta a quebrar o cupom em páginas desse tamanho.
    paper_height: Number | None = None
