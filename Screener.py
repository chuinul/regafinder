
from sortedcontainers import SortedListWithKey
from BaseDeclarations import AuthorizedActivity, ProvidedService
from BaseDeclarations import Legend
from BaseDeclarations import ServiceList
from DomesticCompany import DomesticCompany


# Should be in screener, and built dynamically from a configuration file
ACTIVITY_RULES = {
    AuthorizedActivity(activity=2): 2, AuthorizedActivity(activity=3):4, AuthorizedActivity(activity=4):2
}
SERVICE_RULES = {
    ProvidedService(instrument=2, service=1): 2, ProvidedService(instrument=2, service=2): 5,
    ProvidedService(instrument=2, service=6): 2, ProvidedService(instrument=2, service=7): 2,
    ProvidedService(instrument=2, service=8): 4, ProvidedService(instrument=2, service=9): 9,
    ProvidedService(instrument=1, service=1): 1, ProvidedService(instrument=1, service=2): 3,       # if shares OK, not so much work left
    ProvidedService(instrument=1, service=6): 1, ProvidedService(instrument=1, service=7): 1,
    ProvidedService(instrument=1, service=8): 2, ProvidedService(instrument=1, service=9): 6
}


CB_TO_ACPR_INSTRUMENTS_MATCHER = {
    1: [1, 2],
    2: [5],
    3: [3],
    4: [4],
    5: [2, 9],
    6: [4],
    7: [4],
    8: [4],
    9: [5],
    10: [4]
}

CB_SERVICES_TO_ACPR_SERVICES_MATCHER = {
    1: [1],
    2: [2],
    3: [3],
    4: [4],
    5: [5],
    6: [6, 7],
    7: [8],
    8: [9]
}

CB_SERVICES_TO_ACPR_ACTIVITIES_MATCHER = {
    9: [3]
}


class Screener(object):
    def __init__(self):
        self.l = SortedListWithKey(key=lambda company: company.score)

    def process(self, companies):
        for company in companies:
            print("Processing %d..." % company.cib)
            self._computeScore(company)
            self.l.add(company)

    def print(self, file):
        with open(file, 'w') as f:
            for company in self.l[::-1]:
                f.write(str(company) + '\n\n\n')
    #
    # def _parseRules(self, rules):
    #     # Rules written on domestic authorizations and translated for passeporting companies
    #     for k, v in rules.items():
    #         if isinstance(k, dict):
    #             self._parseService(self, k, v)
    #         else:
    #             self._parseActivity(self, k, v)
    #
    # def _parseActivity(self, activity, weight):
    #     self.activities.update({AuthorizedActivity(activity=activity): weight})
    #     if Legend.getACPRActivities()[activity] == 'Tenue de compte-conservation':
    #         service_index = next(k for k, v in Legend.getCBServices().items() if v == 'Conservation et administration d\'IF pour le compte de clients, y compris la garde et les services connexes, comme la gestion de trésorerie de garanties')
    #         for instrument in Legend.getCBInstruments():
    #             self.CBservices.update({ProvidedService(service=service_index, instrument=instrument): weight})
    #
    # def _parseService(self, service_and_instrument, weight):
    #     service, instrument = service_and_instrument.popitem()
    #     self.services.update({ProvidedService(service=service, instrument=instrument): weight})

    def _computeScore(self, company):
        score = 0
        services = company.getServices()
        activities = company.getActivities()
        if not isinstance(company, DomesticCompany):
            domesticazedServices = ServiceList()
            domesticazedActivities = []
            for service in services:
                try:
                    for domesticazedService in CB_SERVICES_TO_ACPR_SERVICES_MATCHER[service.service]:
                        for domesticazedInstrument in CB_TO_ACPR_INSTRUMENTS_MATCHER[service.instrument]:
                            domesticazedServices.add(ProvidedService(service=domesticazedService, instrument=domesticazedInstrument))
                except KeyError: # maybe  service -> activity
                    try:
                        domesticazedActivities.append(AuthorizedActivity(activity=CB_SERVICES_TO_ACPR_ACTIVITIES_MATCHER[service.service]))
                    except KeyError:
                        pass
            services = domesticazedServices
            activities = domesticazedActivities

        for service, weight in SERVICE_RULES.items():
            if service in services:
                score += weight
        for activity, weight in ACTIVITY_RULES.items():
            if activity in activities:
                score += weight
        company.score = score


