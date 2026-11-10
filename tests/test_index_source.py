import pytest

from services.ingestion.import_issue import GRANT_INDEX_URL, validate_index_source

ARCHIVED = "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml"
ARCHIVED_GRANT = "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml"


def test_index_sources_are_scoped_to_official_dataset_and_issue():
    validate_index_source(ARCHIVED, "024018", grant=False)
    validate_index_source(GRANT_INDEX_URL, "053028", grant=True)
    validate_index_source(ARCHIVED_GRANT, "053028", grant=True)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(ARCHIVED_GRANT, "053027", grant=True)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(ARCHIVED_GRANT, "053028", grant=False)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(ARCHIVED, "024018", grant=True)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(ARCHIVED, "024019", grant=False)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(GRANT_INDEX_URL, "024018", grant=False)
    with pytest.raises(ValueError, match="dataset and issue"):
        validate_index_source(
            ARCHIVED.replace("ftp.tipo.gov.tw", "example.org"), "024018", grant=False
        )
