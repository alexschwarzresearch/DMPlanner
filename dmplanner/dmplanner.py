import json
import re

import inflect
import requests
from flask import Flask, render_template, request, Response, jsonify

import constants
import doi_oai_resolver as resolver
import filter
from dmp_creator import create_dmp_dict, create_machine_dmp
from utils import get_key_or_none

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

p = inflect.engine()

ORCID_SEARCH_URL = 'https://pub.orcid.org/v2.1/search/?q=%22{}%22'
ORCID_RECORD_URL = 'https://pub.orcid.org/v2.1/{}/record'
GITHUB_URL = 'https://api.github.com/repos/'

DOI_REGEX = r'10.\d{4,9}/[-._;()/:a-zA-Z0-9]+'
GITHUB_REGEX = r'(?<=github.com\/)[-a-zA-Z0-9:%_\+.~#?&=]+\/[-a-zA-Z0-9:%_\+.~#?&=]+[^\/]'

resource_cache = dict()
# key = full_name
github_cache = dict()
orcid_cache = dict()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search_orcid/', methods=['GET', 'POST'])
def search_orcid():
    if request.method == 'GET':
        # filter relevant information from orcid api
        orcid = request.args.get('orcid')

        reduced_entry = filter.filter_orcid_record(orcid_cache, orcid)
        return render_template('orcid_record.html', data=reduced_entry, orcid=orcid)

    name = request.form['name']
    name_encoded = '%20'.join(name.split())
    search_url = ORCID_SEARCH_URL.format(name_encoded)

    response = requests.get(search_url, headers={'Accept': 'application/json'})
    search_json_data = json.loads(response.text)

    record_list = list()

    for item in search_json_data['result']:
        record_url = ORCID_RECORD_URL.format(item['orcid-identifier']['path'])
        response = requests.get(record_url, headers={'Accept': 'application/json'})
        record_json_data = json.loads(response.text)

        first_name = get_key_or_none(record_json_data, 'person', 'name', 'given-names', 'value')
        last_name = get_key_or_none(record_json_data, 'person', 'name', 'family-name', 'value')

        if first_name and last_name:
            full_name = first_name + ' ' + last_name
            record_list.append((full_name, item['orcid-identifier']['path']))

            record_json_data['full_name'] = full_name
            orcid_cache[item['orcid-identifier']['path']] = record_json_data

    return render_template('orcid_search.html', records=record_list)


@app.route('/work_titles/', methods=['GET'])
def work_titles():
    orcid = request.args.get('orcid')
    works = orcid_cache[orcid]['works']

    return render_template('title_selection.html', works=works)


@app.route('/add_resource/', methods=['POST'])
def add_resource():
    resource_text = request.form['resource_text'].strip()

    doi_pattern = re.compile(DOI_REGEX)
    github_pattern = re.compile(GITHUB_REGEX)

    if doi_pattern.search(resource_text):
        record = search_doi(doi_pattern.search(resource_text).group(0))
        if record is None:
            return Response('DOI could not be resolved to OAI-PMI link.', status=404, mimetype='application/json')

    elif github_pattern.search(resource_text):
        match = github_pattern.search(resource_text).group(0)
        record = search_github(GITHUB_URL + match)
    else:
        record = search_github(GITHUB_URL + resource_text)

    if record is None:
        return Response('Could not find resource.', status=404, mimetype='application/json')

    return render_template('resource_element.html', record=record)


@app.route('/generate_human_dmp/', methods=['POST'])
def generate_human_dmp():
    data = request.get_json(force=True)
    human_dmp = create_dmp_dict(orcid_cache, github_cache, resource_cache, data)

    return render_template('dmp.html', dmph=human_dmp, inflect=p, resource_type=constants.resource_type)


@app.route('/generate_machine_dmp/', methods=['POST'])
def generate_machine_dmp():
    data = request.get_json(force=True)
    machine_dmp, message = create_machine_dmp(orcid_cache, github_cache, resource_cache, data)

    return jsonify({'dmp': machine_dmp, 'message': message})


def search_doi(doi):
    resource = resolver.get_metadata_for_doi(doi)
    if resource is None:
        return None

    identifier = resource['record']['header']['identifier']

    # oai_datacite specific
    host = get_key_or_none(resource, 'record', 'metadata', 'oai_datacite', 'payload', 'resource', 'publisher')
    if host is None:
        host = identifier.split(':')[1]
    name = get_key_or_none(resource, 'record', 'metadata', 'oai_datacite', 'payload', 'resource', 'titles', 'title')
    if name is None:
        name = doi

    resource['record']['doi'] = doi
    resource_cache[identifier] = resource['record']

    record = dict()
    record['id'] = identifier
    record['name'] = name
    record['host'] = host

    return record


def search_github(url):
    response = requests.get(url, headers={'Accept': 'application/json'})
    json_data = json.loads(response.text)

    if get_key_or_none(json_data, 'full_name') is None:
        return None

    github_cache[json_data['id']] = json_data

    record = dict()
    record['id'] = json_data['id']
    record['name'] = json_data['full_name']
    record['host'] = 'Github'

    return record


if __name__ == '__main__':
    app.run(host='0.0.0.0')
