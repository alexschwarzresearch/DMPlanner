import requests
import xmltodict

from utils import get_key_or_none

# since the doi cannot be uniformly mapped to a oai-pmh link, a map for each supported doi registrant is needed
doi_oai_url_map = {'10.5281': 'https://zenodo.org/oai2d'}

# the metadataPrefix could be chosen automatically but since the doi has to be mapped to the oai url anyway a map with the preferred metadata type is also stored
doi_pref_metadata_map = {'10.5281': 'oai_datacite'}


def get_metadata_for_doi(doi):
    prefix = doi.split('/')[0]
    suffix = doi.split('/')[1]

    if not get_key_or_none(doi_oai_url_map, prefix):
        return None

    oai_url = doi_oai_url_map[prefix]
    oai_url += '?verb=GetRecord'
    oai_url += '&metadataPrefix=' + doi_pref_metadata_map[prefix]
    oai_url += '&identifier=' + get_identifier_for_doi_suffix(prefix, suffix)

    dict_response = xmltodict.parse(requests.get(oai_url).text)
    return dict_response['OAI-PMH']['GetRecord']


# only supports zenodo and similarly structured suffixes
def get_identifier_for_doi_suffix(prefix, suffix):
    host = doi_oai_url_map[prefix].replace('https://', '').replace('http://', '').split('/')[0]
    record = suffix.split('.')[1]
    identifier = 'oai:{host}:{record}'.format(host=host, record=record)

    return identifier
