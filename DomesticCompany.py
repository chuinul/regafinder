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
from bs4 import NavigableString
from Company import Company, ParsingError, PROVIDED_SERVICE_IMG
from BaseDeclarations import ProvidedService, AuthorizedActivity, Legend
import RegaLog


N_INVESTMENT_SERVICES = 45                        # Should get 5 instruments x 9 services


class DomesticCompany(Company):
    """
    From my investigations, one can find the following types of domestically regulated/registered companies :
        - Institut de microfinance (Habilitation)
        - Compagnie financière holding (Inscription liste)
        - Entreprise mère de société de financement (Inscription liste)
        - Société de financement (Agrément ACPR)
        - Société de financement/Etablissement de paiement (Agrément ACPR)
        - Etablissement de crédit - Banque - Prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de crédit - Banque mutualiste ou coopérative - Prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de crédit - Caisse de crédit municipal et établissement assimilable - Non prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de crédit - Banque - Non prestataire de services d'investissement (Agrément ACPR)
        - Entreprise d'investissement (Agrément ACPR)
        - Etablissement de crédit - Établissement de crédit spécialisé - Prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de crédit - Établissement de crédit spécialisé - Non prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de crédit - Banque mutualiste ou coopérative - Non prestataire de services d'investissement (Agrément ACPR)
        - Etablissement de paiement (Agrément ACPR)
        - Société de tiers-financement (Autorisation)
        - Etablissement de monnaie électronique (Agrément ACPR)
        - Exempté - Etablissement de paiement (-)
        - Société de financement/Entreprise d'investissement (Agrément ACPR)
        - Société de financement/Compagnie financière holding (Agrément ACPR)
        - Etablissement de paiement à régime dérogatoire (Agrément ACPR)
        - Changeur manuel (-)
    Not all will be implemented for my needs.
    """
    ACPR_activities = {v: k for k, v in Legend.getACPRActivities().items()}  # need reverse legend here

    def _retrieveInvestmentServices(self, frenchActivitiesDiv, cib):
        try:
            services = self._findInvestmentServices(frenchActivitiesDiv, N_INVESTMENT_SERVICES)
        except (ValueError, ParsingError) as e:
            RegaLog.logger.error("[CIB: {}]".format(cib) + e)
            return

        n_instrument = 0
        n_service = 1
        for serviceTd in services:
            # retrieving current service/instrument from position
            n_instrument += 1
            if n_instrument > 5:
                n_instrument = 1
                n_service += 1

            isServiceProvided = serviceTd.find('img')['src'] == PROVIDED_SERVICE_IMG
            if isServiceProvided:
                self.provided_services.add(ProvidedService(cib=int(cib), service=n_service, instrument=n_instrument))

    def _retrieveAuthorizedActivities(self, frenchActivitiesDiv, number, cib):
        """
            :param number the number of services listed (whether ticked or not) that we must find,
            or 0 to skip check
        """
        def findActivitiesTables(tag):
            if tag.name != 'table':
                return False
            if tag.has_attr('class') or not tag.has_attr('summary'):
                return False
            return tag['summary'] == ''

        activityTrs = []
        for table in frenchActivitiesDiv.find_all(findActivitiesTables):
            activityTrs += table.find_all('tr')

        if number and len(activityTrs) != number:
            RegaLog.logger.error("[CIB: {}]".format(cib) + "Got unexpected number of authorized services, skipping")

        for activityTr in activityTrs:
            tds = activityTr.find_all('td')
            if tds[0].find('img')['src'] == PROVIDED_SERVICE_IMG:
                self.authorized_activities.append(AuthorizedActivity(cib=cib, activity=DomesticCompany.ACPR_activities.get(tds[1].contents[0].strip())))


class CreditInvestmentServicesCompany(DomesticCompany):
    # ex 10057
    __mapper_args__ = {'polymorphic_identity': 'Etablissement de crédit - Banque - Prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 0, cib)
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class CreditCompany(DomesticCompany):
    # ex 10160
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Banque - Non prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 0, cib)


class SpecializedCreditCompany(DomesticCompany):
    # ex 11128
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Établissement de crédit spécialisé - Non prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 4, cib)


class SpecializedCreditInvestmentServicesCompany(DomesticCompany):
    # ex 10918
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Établissement de crédit spécialisé - Prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 4, cib)
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class MunicipalCreditCompany(DomesticCompany):
    # ex 10140
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Caisse de crédit municipal et établissement assimilable - Non prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 4, cib)


class MutualCreditCompany(DomesticCompany):
    # ex 11307
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Banque mutualiste ou coopérative - Non prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 4, cib)


class MutualCreditInvestmentServicesCompany(DomesticCompany):
    # ex 10107
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de crédit - Banque mutualiste ou coopérative - Prestataire de services d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 4, cib)
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class FinancingFinancialHoldingCompany(DomesticCompany):
    # ex 16718
    __mapper_args__ = {'polymorphic_identity':  'Société de financement/Compagnie financière holding'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 1, cib)


class InvestmentServicesCompany(DomesticCompany):
    # ex 10183
    __mapper_args__ = {'polymorphic_identity':  'Entreprise d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 2, cib)
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class FinancingInvestmentServicesCompany(DomesticCompany):
    # ex 13959
    __mapper_args__ = {'polymorphic_identity':  'Société de financement/Entreprise d\'investissement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 3, cib)
        self._retrieveInvestmentServices(frenchActivitiesDiv, cib)


class FinancingCompany(DomesticCompany):
    # ex 10008
    __mapper_args__ = {'polymorphic_identity':  'Société de financement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 1, cib)


class FinancingPaymentCompany(DomesticCompany):
    # ex 10050
    __mapper_args__ = {'polymorphic_identity':  'Société de financement/Etablissement de paiement'}

    def process(self, mainDiv, cib):
        self._retrieveFrenchActivities(mainDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        self._retrieveAuthorizedActivities(frenchActivitiesDiv, 1, cib)


class ElectronicMoneyCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de monnaie électronique'}

    def process(self, mainDiv, cib):
        pass


class PaymentCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Etablissement de paiement'}

    def process(self, mainDiv, cib):
        pass


class LightPaymentCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity': 'Etablissement de paiement à régime dérogatoire'}

    def process(self, mainDiv, cib):
        pass


class ThirdPartyFinancingCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Société de tiers-financement'}

    def process(self, mainDiv, cib):
        pass


class MicrofinanceCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Institut de microfinance'}

    def process(self, mainDiv, cib):
        pass


class FinancialHoldingCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Compagnie financière holding'}

    def process(self, mainDiv, cib):
        pass


class ParentFinancingCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Entreprise mère de société de financement'}

    def process(self, mainDiv, cib):
        pass


class MoneyChangerCompany(DomesticCompany):
    __mapper_args__ = {'polymorphic_identity':  'Changeur manuel'}

    def process(self, mainDiv, cib):
        pass
