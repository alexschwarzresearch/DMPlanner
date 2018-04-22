import configparser
import datetime
import json
import os
from http.client import responses

import requests

import constants
from utils import get_key_or_none

# load api keys from config file
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dmplanner.config'))
ZENODO_TOKEN = config['zenodo.org']['ZENODO_TOKEN']

ZENODO_FILES_URL = 'https://zenodo.org/api/deposit/depositions/{}/files'


def create_dmp_dict(orcid_cache, github_cache, resource_cache, data):
    dmp = dict()

    # orcid

    orcid_element = orcid_cache[data['orcid']]
    dmp['full_name'] = orcid_element['full_name']
    dmp['orcid'] = orcid_element['orcid']

    email = get_key_or_none(orcid_element, 'email')
    if email:
        dmp['email'] = email

    current_education_name = get_key_or_none(orcid_element, 'current_education_name')
    if current_education_name:
        dmp['current_education_name'] = current_education_name

    current_employment_name = get_key_or_none(orcid_element, 'current_employment_name')
    if current_employment_name:
        dmp['current_employment_name'] = current_employment_name

    # title

    dmp['title'] = data['title']

    # resources

    output_licenses = set()
    software_licenses = set()

    for resource in data['resources']:
        type = resource['tag']

        if not get_key_or_none(dmp, 'resources'):
            dmp['resources'] = dict()

        if not get_key_or_none(dmp, 'resources', type):
            dmp['resources'][type] = list()

        dmp_resource_element = dict()
        dmp_resource_element['host'] = resource['host']

        rights_list = list()

        if resource['host'] == 'Github':
            cache_element = github_cache[int(resource['id'])]
            dmp_resource_element['size'] = str(cache_element['size']) + ' kB'
            dmp_resource_element['language'] = cache_element['language']
            rights_list.append(cache_element['license']['name'])
            dmp_resource_element['rights'] = rights_list
            dmp_resource_element['title'] = cache_element['name']
            dmp_resource_element['html_url'] = cache_element['html_url']
            dmp_resource_element['datestamp'] = cache_element['updated_at']
            dmp_resource_element['description'] = cache_element['description']
        else:
            cache_element = resource_cache[resource['id']]

            dmp_resource_element['html_url'] = 'https://doi.org/' + cache_element['doi']
            dmp_resource_element['datestamp'] = cache_element['header']['datestamp']

            dmp_resource_element['title'] = get_key_or_none(cache_element, 'metadata', 'oai_datacite', 'payload', 'resource', 'titles', 'title')
            dmp_resource_element['language'] = get_key_or_none(cache_element, 'metadata', 'oai_datacite', 'payload', 'resource', 'language')

            description = get_key_or_none(cache_element, 'metadata', 'oai_datacite', 'payload', 'resource', 'descriptions', 'description')
            if description:
                # check if there are multiple descriptions
                if isinstance(description, (list,)):
                    description = description[0]
                else:
                    description = description['#text']

                dmp_resource_element['description'] = description

            for right in get_key_or_none(cache_element, 'metadata', 'oai_datacite', 'payload', 'resource', 'rightsList', 'rights'):
                rights_list.append(right['#text'])

            dmp_resource_element['rights'] = rights_list

        if type == '2':
            output_licenses.update(rights_list)
        if type == '4':
            software_licenses.update(rights_list)

        dmp['resources'][type].append(dmp_resource_element)

    dmp['output_licenses'] = output_licenses
    dmp['software_licenses'] = software_licenses

    # preservation times

    dmp['times'] = dict()
    for time in data['times']:
        for key, value in time.items():
            dmp['times'][key] = value

    return dmp


def create_machine_dmp(orcid_cache, github_cache, resource_cache, data):
    dmp_dict = create_dmp_dict(orcid_cache, github_cache, resource_cache, data)
    message = None

    dmp = dict()
    dmp['@context'] = dict()
    dmp['@context']['dc'] = 'https://purl.org/dc/elements/1.1/'
    dmp['@context']['dcterms'] = 'https://purl.org/dc/terms/'
    dmp['@context']['foaf'] = 'http://xmlns.com/foaf/0.1/'
    dmp['@context']['dmp'] = 'https://purl.org/madmps#'
    dmp['@context']['time'] = 'https://www.w3.org/2006/time#'
    dmp['@context']['premis'] = 'http://id.loc.gov/ontologies/premis.html#'
    dmp['@context']['schema'] = 'https://schema.org/'

    # creator

    dmp['dc:creator'] = dict()
    dmp['dc:creator']['@id'] = 'https://orcid.org/' + dmp_dict['orcid']
    dmp['dc:creator']['@type'] = 'foaf:Person'
    dmp['dc:creator']['foaf:name'] = dmp_dict['full_name']

    email = get_key_or_none(dmp_dict, 'email')
    if email:
        dmp['dc:creator']['foaf:mbox'] = email

    current_education_name = get_key_or_none(dmp_dict, 'current_education_name')
    current_employment_name = get_key_or_none(dmp_dict, 'current_employment_name')

    if current_education_name and current_employment_name:
        dmp['dc:creator']['foaf:Organization'] = list()
        dmp['dc:creator']['foaf:Organization'].append(current_education_name)
        dmp['dc:creator']['foaf:Organization'].append(current_employment_name)
    elif current_education_name:
        dmp['dc:creator']['foaf:Organization'] = current_education_name
    elif current_employment_name:
        dmp['dc:creator']['foaf:Organization'] = current_employment_name

    # general

    dmp['@type'] = 'dmp:DataManagementPlan'
    dmp['dcterms:title'] = dmp_dict['title']
    dmp['dcterms:created'] = datetime.datetime.now().date().isoformat()

    # dataobject

    dmp['dmp:hasDataObject'] = list()

    for resource_type, resource_list in dmp_dict['resources'].items():
        for resource in resource_list:
            data_object = dict()
            data_object['@id'] = resource['html_url']

            # type
            if resource_type == '4':
                data_object['@type'] = 'dmp:SourceCode'
            elif resource_type == '6':
                data_object['@type'] = 'dmp:Documentation'
            else:
                data_object['dcterms:description'] = constants.resource_type[resource_type]

            # metadata
            data_object['dmp:hasMetadata'] = dict()
            data_object['dmp:hasMetadata']['dcterms:title'] = resource['title']

            if get_key_or_none(resource, 'rights'):
                data_object['dmp:hasIntelectualPropertyRights'] = list()
                for right in resource['rights']:
                    data_object['dmp:hasIntelectualPropertyRights'].append({'dcterms:license': right})

            if get_key_or_none(resource, 'size'):
                data_object['dmp:hasMetadata']['dmp:hasDataVolume'] = resource['size']

            data_object['dmp:hasRepository'] = {'dc:publisher': resource['host']}
            data_object['dmp:hasPreservation'] = {'time:years': dmp_dict['times'][resource_type]}

            if get_key_or_none(resource, 'language'):
                data_object['dmp:hasMetadata']['dcterms:language'] = resource['language']

            if resource['description']:
                data_object['dmp:hasMetadata']['dcterms:abstract'] = resource['description']

            data_object['dmp:hasMetadata']['dc:date'] = resource['datestamp']

            # zenodo files
            if resource['host'] == 'Zenodo':
                data_object['dmp:hasDataObject'] = list()
                zenodo_id = resource['html_url'].split('.')[-1]
                code, files = get_zenodo_files(zenodo_id)

                if code >= 400:
                    message = 'Could not access Zenodo Files. Reason: ' + responses[code]
                else:
                    for file in files:
                        file_dict = dict()
                        file_dict['@id'] = file['id']
                        file_dict['@type'] = 'dmp:File'
                        file_dict['schema:url'] = file['links']['download']

                        file_dict['dmp:hasMetadata'] = dict()
                        file_dict['dmp:hasMetadata']['dcterms:title'] = file['filename']
                        file_dict['dmp:hasMetadata']['dmp:hasDataVolume'] = str(file['filesize']) + ' B'

                        if '.' in file['filename']:
                            file_dict['dmp:hasMetadata']['premis:hasFormat'] = 'premis:Format:' + file['filename'].split('.')[-1]

                        file_dict['dmp:hasMetadata']['premis:Fixity'] = dict()
                        file_dict['dmp:hasMetadata']['premis:Fixity']['premis:hasMessageDigestAlgorithm'] = 'MD5'
                        file_dict['dmp:hasMetadata']['premis:Fixity']['premis:messageDigest'] = file['checksum']

                        data_object['dmp:hasDataObject'].append(file_dict)

        dmp['dmp:hasDataObject'].append(data_object)

    return dmp, message


def get_zenodo_files(id):
    response = requests.get(ZENODO_FILES_URL.format(id), headers={'Accept': 'application/json', 'Authorization': 'Bearer ' + ZENODO_TOKEN})
    json_data = json.loads(response.text)

    return response.status_code, json_data
