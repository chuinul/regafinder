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
from BaseDeclarations import buildInspectEmptyDict
from BaseDeclarations import CompanyDescription
import RegaLog


COMPANY_DIV_ID = 'zone_description'
FRENCH_ACTIVITIES_DIV_ID = 'zone_en_france'
SERVICES_TABLE_CLASS = ['petite-police', 'services-invest']     # class attributes returned in a list
SERVICES_TABLE_SUMMARY = 'Services d\'investissement'
PROVIDED_SERVICE_IMG = 'squelettes/img/checked.png'
NOT_PROVIDED_SERVICE_IMG = 'squelettes/img/unchecked.png'


class Company(CompanyDescription):
    score = 0   # used to sort, cf. screener

    @classmethod
    def makeFromMainDiv(cls, mainDiv, cib):
        # Storing mainDiv in the object is meaningless (it may not be built from HTML) and useless (once processed, data
        # is stored elsewhere)

        companyDiv = cls._findCompanyDiv(mainDiv)
        if companyDiv is None:
            RegaLog.logger.error("Error while loading company description for CIB %s, skipping..." % cib)
            return None

        try:
            properties = buildInspectEmptyDict(CompanyDescription)
            properties['cib'] = int(cib)
            properties['authorized_activities'] = []
            properties['provided_services'] = []
            cls._processCompanyDiv(companyDiv, properties)
        except (ValueError, TypeError) as e:
            RegaLog.logger.error(e)
            return None

        company = cls._buildCompany(properties)
        if company is not None:
            company.process(mainDiv, cib)
        return company

    @staticmethod
    def _buildCompany(properties):
        # Dirty trick to avoid circular dependencies
        # Other solution: transform this staticmethod into a function, but less consistent with OOP paradigm
        from DomesticCompany import CreditInvestmentServicesCompany, CreditCompany, MutualCreditCompany, SpecializedCreditCompany, \
            SpecializedCreditInvestmentServicesCompany, MunicipalCreditCompany, MutualCreditInvestmentServicesCompany, \
            FinancingFinancialHoldingCompany, InvestmentServicesCompany, FinancingInvestmentServicesCompany, \
            FinancingCompany, FinancingPaymentCompany, ElectronicMoneyCompany, PaymentCompany, LightPaymentCompany, \
            ThirdPartyFinancingCompany, MicrofinanceCompany, FinancialHoldingCompany, ParentFinancingCompany, MoneyChangerCompany
        from PasseportingCompany import EUInvestmentServicesCompany, EUCreditCompany, EUFinancialCompany
        if properties['type'] == 'Institut de microfinance':
            return MicrofinanceCompany(**properties)
        elif properties['type'] == 'Compagnie financière holding':
            return FinancialHoldingCompany(**properties)
        elif properties['type'] == 'Entreprise mère de société de financement':
            return ParentFinancingCompany(**properties)
        elif properties['type'] == 'Société de financement':
            return FinancingCompany(**properties)
        elif properties['type'] == 'Société de financement/Etablissement de paiement':
            return FinancingPaymentCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Banque - Prestataire de services d\'investissement':
            return CreditInvestmentServicesCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Banque mutualiste ou coopérative - Prestataire de services d\'investissement':
            return MutualCreditInvestmentServicesCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Caisse de crédit municipal et établissement assimilable - Non prestataire de services d\'investissement':
            return MunicipalCreditCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Banque - Non prestataire de services d\'investissement':
            return CreditCompany(**properties)
        elif properties['type'] == 'Entreprise d\'investissement' and properties['auth_type'] == 'Passeport européen en entrée':
            properties['type'] = 'Entreprise d\'investissement (EU)'
            return EUInvestmentServicesCompany(**properties)
        elif properties['type'] == 'Entreprise d\'investissement':
            return InvestmentServicesCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Établissement de crédit spécialisé - Prestataire de services d\'investissement':
            return SpecializedCreditInvestmentServicesCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Établissement de crédit spécialisé - Non prestataire de services d\'investissement':
            return SpecializedCreditCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit - Banque mutualiste ou coopérative - Non prestataire de services d\'investissement':
            return MutualCreditCompany(**properties)
        elif properties['type'] == 'Etablissement de paiement':
            return PaymentCompany(**properties)
        elif properties['type'] == 'Société de tiers-financement':
            return ThirdPartyFinancingCompany(**properties)
        elif properties['type'] == 'Etablissement de monnaie électronique':
            return ElectronicMoneyCompany(**properties)
        elif properties['type'] == 'Exempté - Etablissement de paiement':
            RegaLog.logger.info("CIB %s is registered as '%s', skipping..." % (properties['cib'], properties['type']))
            return None
        elif properties['type'] == 'Société de financement/Entreprise d\'investissement':
            return FinancingInvestmentServicesCompany(**properties)
        elif properties['type'] == 'Société de financement/Compagnie financière holding':
            return FinancingFinancialHoldingCompany(**properties)
        elif properties['type'] == 'Etablissement de paiement à régime dérogatoire':
            return LightPaymentCompany(**properties)
        elif properties['type'] == 'Changeur manuel':
            return MoneyChangerCompany(**properties)
        elif properties['type'] == 'Etablissement de crédit':
            properties['type'] = 'Etablissement de crédit (EU)'
            return EUCreditCompany(**properties)
        elif properties['type'] == 'Etablissement financier':
            properties['type'] = 'Etablissement financier (EU)'
            return EUFinancialCompany(**properties)
        else:
            RegaLog.logger.error("Unknown company type '%s' with CIB %s" % (properties['type'], properties['cib']))
            return None

    @classmethod
    def _processCompanyDiv(cls, companyDiv, output):
        def findLi(tag):
            return tag.name == 'li' and not tag.has_attr('class')

        def findType(tag):
            return tag.name == 'strong' and tag.has_attr('class') and tag['class'] == ['description']

        type = companyDiv.find(findType)
        if type is None:
            raise TypeError("No type found for company with CIB %s" % output['cib'])

        output['type'] = type.contents[0].strip()

        for descriptionLi in companyDiv.find_all(findLi):
            cls._processLi(descriptionLi, output)

    @staticmethod
    def _processLi(descriptionLi, output):
        """ Beware: may give weird results in case a field appears twice (e.g. 'Ville' for branches
            which will appear after branch address and headquarters adress)."""
        key = descriptionLi.contents[0].strip()
        value = descriptionLi.find('span').contents[0].strip()
        if key == 'Code banque (CIB) :':
            if int(value) != output['cib']:
                raise ValueError("Extracted CIB does not match with value provided (%d)" % output['cib'])
        elif key == 'Dénomination sociale :':
            output['name'] = value
        elif key == 'Nom commercial :':
            output['trade_name'] = value
        elif key == 'Forme juridique :':
            output['legal_form'] = value
        elif key == 'SIREN :':
            output['siren'] = value
        elif key == 'LEI :':
            output['lei'] = value
        elif key == 'Nature d\'autorisation :':
            output['auth_type'] = value
        elif key == 'Nature d\'exercice :':
            output['status'] = value
        elif key == 'Adresse du siège social :':
            output['address'] = value
        elif key == 'Code postal :':
            output['postcode'] = value
        elif key == 'Ville :':
            output['city'] = value
        elif key == 'Pays :':
            output['country'] = value

    @staticmethod
    def _findCompanyDiv(mainDiv):
        def findCompanyDiv(tag):
            return tag.name == 'div' and tag.has_attr('id') and tag['id'] == COMPANY_DIV_ID

        return mainDiv.find(findCompanyDiv)

    def process(self, mainDiv, cib):
        # fallback
        pass

    def getServices(self):
        return self.provided_services

    def getActivities(self):
        return self.authorized_activities

    def save(self, session):
        session.add(self)
        # for activity in self._activities:
        #     session.add(activity)
        # for service in self._services:
        #     session.add(service)
        session.commit()

    def _retrieveFrenchActivities(self, mainDiv, cib):
        frenchActivitiesDiv = self._findFrenchActivitiesDiv(mainDiv)
        if frenchActivitiesDiv is None:
            RegaLog.logger.error("Error while loading provided services for CIB %s, skipping..." % cib)
            return

        self._processFrenchActivities(frenchActivitiesDiv, cib)

    def _processFrenchActivities(self, frenchActivitiesDiv, cib):
        # fallback
        pass


    def _retrieveInvestmentServices(self, frenchActivitiesDiv, cib):
        # fallback
        pass

    def _retrieveAuthorizedActivities(self, frenchActivitiesDiv, number, cib):
        # fallback
        pass

    def _findFrenchActivitiesDiv(self, mainDiv):
        def findFrenchActivitiesDiv(tag):
            return tag.name == 'div' and tag.has_attr('id') and tag['id'] == FRENCH_ACTIVITIES_DIV_ID

        return mainDiv.find(findFrenchActivitiesDiv)

    def _findInvestmentServices(self, frenchActivitiesDiv, number):
        """ find in two steps not necessary but cleaner from a semantic point of view """
        def findServiceTable(tag):
            if tag.name != 'table':
                return False
            if not tag.has_attr('class') or not tag.has_attr('summary'):
                return False
            return tag['class'] == SERVICES_TABLE_CLASS and tag['summary'] == SERVICES_TABLE_SUMMARY

        servicesTable = frenchActivitiesDiv.find(findServiceTable)
        if servicesTable is None:
            raise ParsingError("Error while parsing CB services")

        return self._makeInvestmentServicesList(servicesTable, number)

    def _makeInvestmentServicesList(self, servicesTable, number):
        def findServiceTd(tag):
            if tag.name != 'td':
                return False
            if not tag.has_attr('headers'):
                return False
            nexttag = tag
            while nexttag.next_element is not None and isinstance(nexttag.next_element, NavigableString):
                nexttag = nexttag.next_element
            if nexttag.next_element is None or nexttag.next_element.name != 'img':
                return False
            return nexttag.next_element['src'] == PROVIDED_SERVICE_IMG or nexttag.next_element['src'] == NOT_PROVIDED_SERVICE_IMG

        serviceTds = servicesTable.find_all(findServiceTd)
        if len(serviceTds) != number:
            raise ValueError("%d services retrieved instead of %d" % (len(serviceTds), number))
        return serviceTds

    #todo maube not useful
    def __eq__(self, other):
        return self.score == other.score

    def __lt__(self, other):
        return self.score < other.score

    def __le__(self, other):
        return self.score <= other.score


class ParsingError(Exception):
    pass
