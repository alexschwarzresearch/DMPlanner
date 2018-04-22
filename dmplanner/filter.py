from utils import get_key_or_none


def filter_orcid_record(orcid_cache, orcid):
    reduced_entry = dict()
    cache_entry = orcid_cache[orcid]

    reduced_entry['full_name'] = cache_entry['full_name']
    reduced_entry['orcid'] = orcid

    email_list = get_key_or_none(cache_entry, 'person', 'emails', 'email')
    if email_list:
        reduced_entry['email'] = email_list[0]['email']

    education_list = get_key_or_none(cache_entry, 'activities-summary', 'educations', 'education-summary')
    if education_list:
        for education in education_list:
            if not education['end-date']:
                reduced_entry['current_education_name'] = education['organization']['name']

    employment_list = get_key_or_none(cache_entry, 'activities-summary', 'employments', 'employment-summary')
    if employment_list:
        for employment in employment_list:
            if not employment['end-date']:
                reduced_entry['current_employment_name'] = employment['organization']['name']

    work_title_list = list()
    works = get_key_or_none(cache_entry, 'activities-summary', 'works', 'group')
    if works:
        for work in works:
            work_summaries = get_key_or_none(work, 'work-summary')
            if work_summaries:
                for work_summary in work_summaries:
                    title = get_key_or_none(work_summary, 'title', 'title', 'value')
                    if title:
                        work_title_list.append(title)

    reduced_entry['works'] = work_title_list

    orcid_cache[orcid] = reduced_entry
    return reduced_entry
