import os
from functools import reduce
from itertools import count
from statistics import mean

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if not salary_from:
        return int(salary_to)*0.8
    elif not salary_to:
        return int(salary_from)*1.2
    elif not salary_from and salary_to:
        return None
    avg_salary = (int(salary_from) + int(salary_to))/2
    return avg_salary


def predict_rub_salary_hh(job):
    if not job.get('salary').get('currency') == 'RUR':
        return None
    salary_from = job.get('salary').get('from')
    salary_to = job.get('salary').get('to')
    return predict_salary(salary_from, salary_to)


def predict_rub_salary_sj(job):
    if not job.get('currency') == 'rub':
        return None
    salary_from = job.get('payment_from')
    salary_to = job.get('payment_to')
    if salary_from:
        if salary_to:
            return None
    return predict_salary(salary_from, salary_to)


def make_table(results, title):
    table = [
             ['Язык программирования', 'Вакансий найдено',
              'Вакансий обработано', 'Средняя зарплата'
              ]
             ]
    for language, language_statistic in results.items():
        row = []
        row.append(language)
        for stats in language_statistic.values():
            row.append(stats)
        table.append(row)
    table_instance = AsciiTable(table, title)
    return table_instance.table


def fetch_jobs_hh(language):
    url = 'https://api.hh.ru/vacancies'
    headers = {'user-agent': 'my-app/0.0.1'}
    results = {}
    salaries = []
    vacancies_processed = 0
    for page in count(0):
        params = {
            'specialization': '1.221', 'area': '1',
            'date_from': '2022-03-15', 'text': language,
            'only_with_salary': 'true', 'page': page
            }
        response = requests.get(url=url, headers=headers, params=params)
        response.raise_for_status()
        response_dict = response.json()
        if page >= int(response_dict.get('pages')):
            break
        jobs = response_dict.get('items')
        for job in jobs:
            if not predict_rub_salary_hh(job) is None:
                salaries.append(predict_rub_salary_hh(job))
                vacancies_processed += 1
        results[language] = {
            "vacancies_found": response_dict.get('found'),
            "vacancies_processed": vacancies_processed,
            "average_salary": mean(salaries)
            }
    return results


def fetch_jobs_sj(secret_key, access_token, language):
    results = {}
    headers = {'X-Api-App-Id': secret_key,
               'Authorization': f'Bearer {access_token}'}
    url = 'https://api.superjob.ru/2.0/vacancies/'
    salaries = []
    vacancies_processed = 0
    for page in count(0):
        max_page_ammount = 25
        if page >= max_page_ammount:
            break
        params = {
            'period': '30', 'catalogues': '48',
            'town': '4', 'keyword': language, 'page': page
            }
        response = requests.get(url=url, headers=headers, params=params)
        response.raise_for_status()
        response_dict = response.json()
        jobs = response_dict.get('objects')
        for job in jobs:
            if not predict_rub_salary_sj(job):
                salaries.append(predict_rub_salary_sj(job))
                vacancies_processed += 1
        results[language] = {
            "vacancies_found": response_dict.get('total'),
            "vacancies_processed": vacancies_processed,
            "average_salary": mean(salaries)
            }
    return results


if __name__ == '__main__':
    load_dotenv()
    secret_key = os.getenv('SECRET_KEY')
    access_token = os.getenv('ACCESS_TOKEN')
    popular_lang = (
        'JavaScript', 'Java', 'Python',
        'Ruby', 'PHP', 'C++', 'C#',
        'C', 'Go', 'Shell'
    )
    results_hh = {}
    results_sj = {}
    for language in popular_lang:
        results_hh[language] = fetch_jobs_hh(language).get(language)
        results_sj[language] = fetch_jobs_sj(
            secret_key=secret_key,
            access_token=access_token,
            popular_lang=popular_lang
            ).get(language)
    print(make_table(results_sj, title='SuperJob Moscow'))
    print(make_table(results_hh, title='HeadHunter Moscow'))
