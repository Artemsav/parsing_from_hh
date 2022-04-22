import os
from itertools import count
from statistics import mean

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    try:
        salary_from = int(salary_from)
        salary_to = int(salary_to)
        if salary_from and salary_to > 0:
            return (salary_from + salary_to)/2
        elif salary_from > 0:
            return salary_from*1.2
        else:
            return salary_to*0.8
    except TypeError:
        return None


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
        fetch_jobs = response.json()
        if page >= int(fetch_jobs.get('pages')):
            break
        jobs = fetch_jobs.get('items')
        for job in jobs:
            job_salary = predict_rub_salary_hh(job)
            if job_salary:
                salaries.append(job_salary)
                vacancies_processed += 1
        results[language] = {
            "vacancies_found": fetch_jobs.get('found'),
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
        fetch_jobs = response.json()
        jobs = fetch_jobs.get('objects')
        for job in jobs:
            job_salary = predict_rub_salary_sj(job)
            if job_salary:
                salaries.append(job_salary)
                vacancies_processed += 1
        results[language] = {
            "vacancies_found": fetch_jobs.get('total'),
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
            language=language
            ).get(language)
    print(make_table(results_sj, title='SuperJob Moscow'))
    print(make_table(results_hh, title='HeadHunter Moscow'))
