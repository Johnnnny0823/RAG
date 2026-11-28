import pytest

from services.ingestion.grant_drawing import drawing_source

SOURCE = "ftps://ftp.tipo.gov.tw/PatentPubXML/115/PatentPubXML_053030/5330D000001/000000001-DEMO.xml"
XML = b"""<specification application-num="000000001"><drawings>
    <figure><img file="IMG-2/Draw/000000001-DEMO.JPG" /></figure>
</drawings></specification>"""


def test_official_drawing_url_and_position_are_derived_from_verified_xml():
    path, locator = drawing_source(SOURCE, XML, "D000001", "000000001", "053030", 1)
    assert path.endswith("/5330D000001/IMG-2/Draw/000000001-DEMO.JPG")
    assert locator == "/specification/drawings/figure[1]/img[1]"


@pytest.mark.parametrize(
    ("source", "xml", "position"),
    [
        (SOURCE.replace("ftp.tipo.gov.tw", "example.com"), XML, 1),
        (SOURCE.replace("053030", "053029"), XML, 1),
        (SOURCE, XML.replace(b"IMG-2/Draw/", b"../"), 1),
        (SOURCE, XML.replace(b"000000001-DEMO", b"000000002-DEMO"), 1),
        (SOURCE, XML, 2),
    ],
)
def test_drawing_rejects_unverified_paths_and_positions(source, xml, position):
    with pytest.raises(ValueError):
        drawing_source(source, xml, "D000001", "000000001", "053030", position)
