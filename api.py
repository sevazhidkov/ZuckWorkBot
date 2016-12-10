class BackendApi:
    def get_vacancies(self):
        """Should return list of vacancies names vacancies sorted by popularity"""
        return ['Software engineer', 'Head of Machine Learning',
                'Developer Advocate (Cloud Platform)',
                'Account Executive, Google Cloud Platform',
                'Global Product Lead, AdWords Interfaces',
                'Sales Solutions Specialist', 'Brand Strategist, Google Cloud',
                'Android UX Engineer, Design']

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
