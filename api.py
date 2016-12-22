import json
import requests


class BackendApi:
    CLUSTER_NAMES = ['DevOps', 'Management & Communications',
                     'Predictive Analytics', 'Research', 'Art',
                     'Product', 'HR', 'Leadership',
                     'Legal & Audit', 'Strategy', 'Materials & Manufacturing',
                     'Marketing', 'Hardware', 'Data science', 'Communications',
                     'Sales', 'Machine learning', 'Infrasctructure',
                     'Networks & Systems', 'Architecture'
                     ]

    def get_vacancies(self):
        """Should return list of vacancies names vacancies sorted by popularity"""
        all_vacancies = requests.get('http://95.213.203.31:7000/all_jobs').json()
        divisions = {}
        for division, group, vacancy in all_vacancies:
            divisions[division] = divisions.get(division, []) + [vacancy]
        return divisions

    def get_topics(self):
        return self.CLUSTER_NAMES

    def generate_program(self, vacancy, skills):
        print(vacancy, skills) # Developer Advocate (Cloud Platform) ['Copywriting', 'Sleeping']
        vec = []
        for skill in self.CLUSTER_NAMES:
            if skill in skills:
                vec.append(1)
            else:
                vec.append(0)
        result = requests.get(
            'http://95.213.203.31:7000/recommend/{}&{}'.format(
                ','.join(map(str, vec)),
                vacancy
            )
        ).json()
        print(result[0])
        return result
