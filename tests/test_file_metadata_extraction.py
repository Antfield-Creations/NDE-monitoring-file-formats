from http.client import HTTPSConnection

from analysis.config import load_config
from analysis.scrape_dans import scrape_version_metadata


def test_extractor() -> None:
    config = load_config()
    dans_cfg = config['data']['dans']

    # Example below: "Prehistorie onder de Prijs; bewoningssporen uit de vroege en midden ijzertijd te Culemborg-Hoge
    # Prijs; gemeente Culemborg"
    # NOTE this test will fail as soon as this dataset has been migrated.
    # TODO: Either mock response or extract data snapshot
    not_migrated_doi = 'doi:10.17026/dans-z7n-aer9'
    conn = HTTPSConnection(dans_cfg['root_url'].split('/')[-1])
    file_metadata = scrape_version_metadata(not_migrated_doi, conn, dans_cfg)
    assert file_metadata is None, "It should skip datasets that are not yet migrated"

    # "Veldhoven MFA midden Proefsleuvenonderzoek"
    migrated_doi = 'doi:10.17026/dans-zbe-b8h5'
    file_metadata = scrape_version_metadata(migrated_doi, conn, dans_cfg)
    assert file_metadata is not None

    filenames, date = file_metadata  # unpack
    assert len(file_metadata) > 0, 'It should return metadata for a migrated dataset'

    # The deposit date should be 2013-02-14
    assert date == '2013-02-14'
