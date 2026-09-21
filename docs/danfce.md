DANFCe (Auxiliary Document of the Electronic Consumer Invoice) is the receipt printed for the NFC-e (NF-e model 65), the invoice issued in over-the-counter retail sales. It is laid out for non-fiscal thermal printers, following the *Manual de Especificações Técnicas do DANFE NFC-e / QR Code*.

## Basic Usage

=== "Python"

    ```python
    from brazilfiscalreport.danfce import Danfce

    # Path to the XML file
    xml_file_path = 'nfce.xml'

    # Load XML Content
    with open(xml_file_path, "r", encoding="utf8") as file:
        xml_content = file.read()

    # Instantiate the DANFCe object with the loaded XML content
    danfce = Danfce(xml=xml_content)
    danfce.output('output_danfce.pdf')
    ```

=== "CLI"

    ```bash
    bfrep danfce /path/to/nfce.xml
    ```

The QR Code requires the `qrcode` package, installed with the extra:

```bash
pip install 'brazilfiscalreport[danfce]'
```

## Customizing DANFCe

This section describes how to customize the PDF output of the DANFCe using the `DanfceConfig` class.

### Paper width

The default roll is 80 mm wide. For 58 mm printers, set `paper_width`; the item columns are measured from their contents, so they adapt to the narrower roll:

```python
from brazilfiscalreport.danfce import Danfce, DanfceConfig

config = DanfceConfig(paper_width=58)

danfce = Danfce(xml=xml_content, config=config)
danfce.output('output_danfce.pdf')
```

`paper_height` (default 300 mm) only decides where the receipt breaks into pages — the roll itself is continuous.

### Margins

```python
from brazilfiscalreport.danfce import Danfce, DanfceConfig, Margins

config = DanfceConfig(
    margins=Margins(top=2, right=2, bottom=2, left=2)
)

danfce = Danfce(xml=xml_content, config=config)
```

### Font

Times is used by default. Helvetica and Courier are also available:

```python
from brazilfiscalreport.danfce import Danfce, DanfceConfig, FontType

config = DanfceConfig(font_type=FontType.HELVETICA)
```

### Decimal precision

Prices and quantities are printed with 2 decimal places by default. Retail quantities sold by weight usually need more:

```python
from brazilfiscalreport.danfce import Danfce, DanfceConfig, DecimalConfig

config = DanfceConfig(
    decimal_config=DecimalConfig(price_precision=2, quantity_precision=3)
)
```

## Layout notes

- The title is followed by the mandatory "Não permite aproveitamento de crédito de ICMS" notice.
- `tpAmb=2` prints "EMITIDA EM AMBIENTE DE HOMOLOGAÇÃO - SEM VALOR FISCAL", a `tpEmis` other than `1` prints "EMITIDA EM CONTINGÊNCIA", and a document with no `protNFe` prints "Pendente de autorização" — in place of the authorization protocol as well.
- The totals block closes arithmetically: `VALOR TOTAL - DESCONTO + ACRÉSCIMO = VALOR A PAGAR`. "ACRÉSCIMO" sums the components that add to `vNF` (`vST`, `vFCPST`, `vFrete`, `vSeg`, `vOutro`, `vII`, `vIPI`, `vIPIDevol`) and "DESCONTO" the ones that subtract (`vDesc`, `vICMSDeson`). Both lines are omitted when zero.
- The approximate taxes (Lei nº 12.741/2012) come from `ICMSTot/vTotTrib`, falling back to the sum of `det/imposto/vTotTrib` when the total is absent.
- The consumer is identified by `CPF`, `CNPJ` or `idEstrangeiro`; without any of them the document prints "CONSUMIDOR NÃO IDENTIFICADO".
- `infAdic/infCpl` is printed as the taxpayer's message, between the taxes line and the access key.
- When the item list spills over a page, the column header is repeated on the new page.
