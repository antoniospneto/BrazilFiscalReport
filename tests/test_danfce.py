import re

import pytest

from brazilfiscalreport.danfce import Danfce, DanfceConfig, Margins
from brazilfiscalreport.danfce.danfce import ITEM_CODE_WIDTH
from brazilfiscalreport.danfce.danfce_conf import (
    CONTINGENCY_NOTICE,
    HOMOLOGATION_NOTICE,
    PENDING_AUTH_NOTICE,
)
from tests.conftest import assert_pdf_equal, get_pdf_output_path


@pytest.fixture
def load_danfce(load_xml):
    def _load_danfce(filename, config=None):
        xml_content = load_xml(f"danfce/{filename}")
        return Danfce(xml=xml_content, config=config)

    return _load_danfce


# --- Comparação com os PDFs de referência ---


def test_danfce_default(tmp_path, load_danfce):
    danfce = load_danfce("danfce_default.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_default")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_without_consumer(tmp_path, load_danfce):
    danfce = load_danfce("danfce_without_consumer.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_without_consumer")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_foreign_consumer(tmp_path, load_danfce):
    danfce = load_danfce("danfce_foreign_consumer.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_foreign_consumer")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_with_margins(tmp_path, load_danfce):
    config = DanfceConfig(
        margins=Margins(top=4, right=4, bottom=4, left=4),
    )
    danfce = load_danfce("danfce_default.xml", config=config)
    pdf_path = get_pdf_output_path("danfce", "danfce_margin")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_narrow_paper(tmp_path, load_danfce):
    danfce = load_danfce("danfce_default.xml", config=DanfceConfig(paper_width=58))
    pdf_path = get_pdf_output_path("danfce", "danfce_narrow_paper")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_multi_page(tmp_path, load_danfce):
    danfce = load_danfce("danfce_multi_page.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_multi_page")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_sem_valor_fiscal(tmp_path, load_danfce):
    danfce = load_danfce("danfce_sem_valor_fiscal.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_sem_valor_fiscal")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


def test_danfce_long_fields(tmp_path, load_danfce):
    danfce = load_danfce("danfce_long_fields.xml")
    pdf_path = get_pdf_output_path("danfce", "danfce_long_fields")
    assert_pdf_equal(danfce, pdf_path, tmp_path)


# --- Paginação do bloco de itens ---


def test_danfce_multi_page_breaks_inside_item_list(load_danfce):
    """
    O bloco de itens é desenhado em coordenadas absolutas. Antes da reserva
    de espaço, um item que cruzasse a quebra de página fazia cada célula
    abrir uma página nova (36 itens chegavam a 10 páginas).
    """
    danfce = load_danfce("danfce_multi_page.xml")
    assert len(danfce.pages) == 2


def test_danfce_repeats_item_header_after_page_break(load_xml, monkeypatch):
    calls = []
    original = Danfce._draw_items_header

    def spy(self):
        calls.append(self.page)
        return original(self)

    monkeypatch.setattr(Danfce, "_draw_items_header", spy)
    Danfce(xml=load_xml("danfce/danfce_multi_page.xml"))

    assert calls == [1, 2], "cabeçalho de colunas deve ser repetido na página nova"


def test_danfce_item_lines_fit_their_column(load_danfce):
    """Código longo sem espaços tem de quebrar dentro da própria coluna."""
    danfce = load_danfce("danfce_long_fields.xml")
    code = danfce.data["items"][0]["code"]
    assert len(code) > 20, "a fixture deve trazer um código maior que a coluna"

    danfce.set_font(danfce.default_font, "", 7)
    lines = danfce.wrap_text(code, ITEM_CODE_WIDTH)
    assert len(lines) > 1
    assert "".join(lines) == code
    for line in lines:
        assert danfce.get_string_width(line) <= ITEM_CODE_WIDTH


# --- Totais ---


def to_float(value):
    return float(value.replace(".", "").replace(",", "."))


@pytest.mark.parametrize(
    "fixture",
    [
        "danfce_default.xml",
        "danfce_without_consumer.xml",
        "danfce_multi_page.xml",
    ],
)
def test_danfce_totals_add_up(load_danfce, fixture):
    """VALOR TOTAL - DESCONTO + ACRÉSCIMO tem de fechar com VALOR A PAGAR."""
    totals = load_danfce(fixture).data["totals"]
    payable = (
        to_float(totals["products"])
        - to_float(totals["discount"] or "0")
        + to_float(totals["increase"] or "0")
    )
    assert round(payable, 2) == to_float(totals["payable"])


def test_danfce_item_quantity_is_an_integer(load_danfce):
    assert load_danfce("danfce_default.xml").data["totals"]["item_quantity"] == "3"


def test_danfce_taxes_fall_back_to_item_totals(load_danfce):
    """vTotTrib ausente no ICMSTot é somado a partir dos itens."""
    totals = load_danfce("danfce_default.xml").data["totals"]
    assert to_float(totals["taxes"]) == pytest.approx(8.29 + 23.08 + 3.19)


def test_danfce_accepts_totals_without_optional_tags(load_xml):
    """ICMSTot incompleto não pode derrubar a geração."""
    xml = load_xml("danfce/danfce_default.xml")
    for tag in ("vFrete", "vSeg", "vOutro", "vDesc", "vICMSDeson"):
        xml = re.sub(rf"\s*<{tag}>[^<]*</{tag}>", "", xml)

    totals = Danfce(xml=xml).data["totals"]
    assert totals["increase"] == ""
    assert totals["discount"] == ""


# --- Avisos e identificação ---


def test_danfce_notices_for_unauthorized_document(load_danfce):
    notices = load_danfce("danfce_sem_valor_fiscal.xml").data["notices"]
    assert notices == [HOMOLOGATION_NOTICE, CONTINGENCY_NOTICE, PENDING_AUTH_NOTICE]


def test_danfce_authorized_document_has_no_notices(load_danfce):
    assert load_danfce("danfce_default.xml").data["notices"] == []


def test_danfce_shows_additional_information(load_danfce):
    info = load_danfce("danfce_sem_valor_fiscal.xml").data["additional_info"]
    assert info.startswith("Documento emitido por ME/EPP")


def test_danfce_identifies_foreign_consumer(load_danfce):
    consumer = load_danfce("danfce_foreign_consumer.xml").data["consumer"]
    assert consumer["credentials"] == "Id. Estrangeiro: AB123456789  John Doe"


def test_danfce_unidentified_consumer(load_danfce):
    assert load_danfce("danfce_without_consumer.xml").data["consumer"] == {
        "credentials": "",
        "address": "",
        "neighborhood": "",
    }


def test_danfce_requires_inf_nfe(load_xml):
    xml = (
        load_xml("danfce/danfce_default.xml")
        .replace("<infNFe ", "<infNFeAusente ")
        .replace("</infNFe>", "</infNFeAusente>")
    )
    with pytest.raises(ValueError, match="infNFe"):
        Danfce(xml=xml)


def test_danfce_strips_cdata_whitespace(load_danfce):
    """qrCode/urlChave em CDATA indentado não podem levar espaços no payload."""
    footer = load_danfce("danfce_default.xml").data["footer"]
    assert footer["qr_code"].startswith("http://")
    assert footer["qr_code"] == footer["qr_code"].strip()
    assert footer["url"] == "www.sefaz.ba.gov.br/nfce/consulta"


@pytest.mark.parametrize("paper_width", [80, 58])
def test_danfce_split_rows_are_not_truncated(load_xml, paper_width, monkeypatch):
    """Nenhum valor de rótulo/valor pode sair com reticências por falta de 1mm."""
    truncated = []
    original = Danfce.long_field

    def spy(self, text="", limit=0, **kwargs):
        result = original(self, text=text, limit=limit, **kwargs)
        if result != text:
            truncated.append((text, result, limit))
        return result

    monkeypatch.setattr(Danfce, "long_field", spy)
    Danfce(
        xml=load_xml("danfce/danfce_default.xml"),
        config=DanfceConfig(paper_width=paper_width),
    )

    values = [item for item in truncated if item[0] != item[1]]
    assert values == [], f"valores cortados: {values}"
