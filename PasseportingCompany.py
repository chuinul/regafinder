"""
Copyright © 2017 Nicolas Garnier (nicolas@github.equinoxe.ovh).
This file is part of RegaFinder, a personal tool designed to perform
reverse searches in the French financial firms register REGAFI.

RegaFinder is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RegaFinder is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RegaFinder. If not, see <http://www.gnu.org/licenses/>
"""


import sys
from Company import Company, ParsingError, PROVIDED_SERVICE_IMG
from BaseDeclarations import ProvidedService
import RegaLog


N_INVESTMENT_SERVICES = 150                        # Should get 10 instruments x  15 services


class PasseportingCompany(Company):
    """
    From my investigations, one can find the following types of passeporting companies :
        - Etablissement de crédit
        - Entreprise d'investissement
        - Etablissement financier
    Not all will be implemented for my needs.
    """
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
