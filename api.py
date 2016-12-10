import json
import requests


class BackendApi:


    def get_vacancies(self):
        """Should return list of vacancies names vacancies sorted by popularity"""
        all_vacancies = requests.get('http://185.106.143.4:8080/all_jobs').json()
        divisions = {}
        for division, group, vacancy in all_vacancies:
            divisions[division] = divisions.get(division, []) + [vacancy]
        return divisions

    def get_topics(self):
        return ['Python', 'Copywriting', 'Creating bots',
                'Sleeping', 'Hacking', 'Eating']

    def generate_program(self, vacancy, skills):
        print(vacancy, skills) # Developer Advocate (Cloud Platform) ['Copywriting', 'Sleeping']
        return [{'title': 'Using Databases with Python',
                 'time': '5 weeks of study, 2-3 hours/week',
                 'language': 'English',
                 'link': 'https://ru.coursera.org/learn/python-databases'},
                {'title': 'Lulz and smehuechki',
                 'time': '5 weeks of study, 2-3 hours/week',
                 'language': 'English',
                 'link': 'https://ru.coursera.org/learn/python-databases'},
                {'title': 'Using Databases with Python',
                 'time': '5 weeks of study, 2-3 hours/week',
                 'language': 'English',
                 'link': 'https://ru.coursera.org/learn/python-databases'}]
