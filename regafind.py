#!/usr/bin/env python3

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


import os
from bs4 import BeautifulSoup
from BaseDeclarations import RegafiDBSession, CompanyDescription, AuthorizedActivity, ProvidedService, \
    ACPR_authorized_activity, ACPR_service, ACPR_service, CB_service, CB_instrument
from Company import Company
from DomesticCompany import *
from PasseportingCompany import *
from Screener import Screener


def main():
    DBSession = RegafiDBSession()

    session = DBSession()
    companies = session.query(CompanyDescription).all()
    screener = Screener()
    screener.process(companies)
    screener.print('screened.txt')
    session.close()


if __name__ == '__main__':
    main()
