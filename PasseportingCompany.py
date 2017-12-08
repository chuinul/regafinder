"""
From my investigations, one can find the following types of passeporting companies :
    - Etablissement de crédit
    - Entreprise d'investissement
    - Etablissement financier
Not all will be implemented (empty class defaulting to empty methods of parents)
"""


import sys
from Company import Company, ParsingError, PROVIDED_SERVICE_IMG
from BaseDeclarations import ProvidedService
import RegaLog


N_INVESTMENT_SERVICES = 150                        # Should get 10 instruments x  15 services


class PasseportingCompany(Company):
    def _retrieveInvestmentServices(self, frenchActivitiesDiv, cib):
        try:
            services = self._findInvestmentServices(frenchActivitiesDiv, N_INVESTMENT_SERVICES)
        except (ValueError, ParsingError) as e:
            RegaLog.logger.error("[CIB: {}]".format(cib) + e)
            return

        n_instrument = 1
        n_service = 0
        for serviceTd in services:
            # retrieving current service/instrument from position
            n_service += 1
            if n_service > 15:
                n_service = 1
                n_instrument += 1

            isServiceProvided = serviceTd.find('img')['src'] == PROVIDED_SERVICE_IMG
            if isServiceProvided:
                self.provided_services.add(ProvidedService(cib=int(cib), service=n_service, instrument=n_instrument))

class EUInvestmentServicesCompany(PasseportingCompany):
    # ex 10033
    __mapper_args__ = {'polymorphic_identity': 'Entreprise d\'investissement (EU)'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class EUCreditCompany(PasseportingCompany):
    # May have interesting authorizations (account keeping, share issuances, ...)
    # Ex.: 00023
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit (EU)'}

    pass

class EUFinancialCompany(PasseportingCompany):
    # What difference against credit institution ?
    # Ex.: 75567
    __mapper_args__ = {'polymorphic_identity':  'Etablissement financier (EU)'}

    pass
