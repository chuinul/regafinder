#!/usr/bin/python3

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
