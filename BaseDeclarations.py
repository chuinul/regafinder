"""
@section LICENSE

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
from sortedcontainers import SortedList
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, Date
from sqlalchemy import ForeignKey


DATABASE = 'results.db'
Base = declarative_base()


class ServiceList(SortedList):
    # see http://stackoverflow.com/questions/42346770/how-to-use-sortedcontainers-sortedlist-with-sqlalchemy-relationship
    def append(self, item):
        self.add(item)


def buildInspectEmptyDict(base):
    d = dict()
    mapper = inspect(base)
    for column in mapper.attrs:
        d[column.key] = None
    return d


class CompanyDescription(Base):
    __tablename__ = 'companies'
    cib = Column(Integer, primary_key=True)
    name = Column(Text)
    trade_name = Column(Text)
    type = Column(Text)
    legal_form = Column(Text)
    siren = Column(String(10))
    lei = Column(String(21))
    auth_type = Column(Text)
    status = Column(Text)
    address = Column(Text)
    postcode = Column(Text)
    city = Column(Text)
    country = Column(Text)
    last_update = Column(Date)

    __mapper_args__ = {'polymorphic_on': type,
                       'with_polymorphic': '*'}

    def __repr__(self):
        repr = "%s (%s) : %s, %s" % (self.name, self.cib, self.type, self.auth_type)
        if len(self.provided_services) > 0:
            repr += "\n" + "\tServices fournis"
            for service in self.provided_services:
                repr += "\n\t\t" + service.__repr__()
        if len(self.authorized_activities) > 0:
            repr += "\n" + "\tActivités authorisées"
            for activity in self.authorized_activities:
                repr += "\n\t\t" + activity.__repr__()
        return repr


class AuthorizedActivity(Base):
    __tablename__ = 'authorized_activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cib = Column(Integer, ForeignKey("companies.cib"), nullable=False)
    activity = Column(Integer, nullable=False)

    company = relationship("CompanyDescription", back_populates="authorized_activities")
    CompanyDescription.authorized_activities = relationship("AuthorizedActivity", back_populates="company")

    def __repr__(self):
        return "%s" % Legend.getACPRActivities()[self.activity]

    def __eq__(self, other):
        # useful for screener
        return self.activity == other.activity

    def __hash__(self):
        # risky but necessary... we want to avoid adding two rules for the same service in screener
        return self.activity


class ProvidedService(Base):
    __tablename__ = 'provided_services'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cib = Column(Integer, ForeignKey("companies.cib"), nullable=False)
    service = Column(Integer, nullable=False)
    instrument = Column(Integer, nullable=False)

    company = relationship("CompanyDescription", back_populates="provided_services")
    CompanyDescription.provided_services = relationship("ProvidedService", back_populates="company", collection_class=ServiceList)

    def __repr__(self):
        if self.company.auth_type == 'Passeport européen en entrée':
            return "%s: %s" % (Legend.getCBInstruments()[self.instrument], Legend.getCBServices()[self.service])
        else:
            return "%s: %s" % (Legend.getACPRInstruments()[self.instrument], Legend.getACPRServices()[self.service])

    """ All comparison operators deal with the service, not the company involved. In other words, Service1 == Service2
    iff service1==service2 and instrument1==instrument2 whatever cib is."""
    def __eq__(self, other):
        return self.service == other.service and self.instrument == other.instrument

    def __lt__(self, other):
        if self.instrument < other.instrument:
            return True
        elif self.instrument > other.instrument:
            return False
        elif self.service < other.service:
            return True
        return False

    def __le__(self, other):
        if self.instrument < other.instrument:
            return True
        elif self.instrument > other.instrument:
            return False
        elif self.service <= other.service:
            return True
        return False

    def __hash__(self):
        # performance unnecessary
        return hash((self.service, self.instrument))


class ACPR_authorized_activity(Base):
    __tablename__ = 'ACPR_authorized_activities'
    activity = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class ACPR_service(Base):
    __tablename__ = 'ACPR_services'
    service = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class ACPR_instrument(Base):
    __tablename__ = 'ACPR_instruments'
    instrument = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class CB_service(Base):
    __tablename__ = 'CB_services'
    service = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class CB_instrument(Base):
    __tablename__ = 'CB_instruments'
    instrument = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class RegafiDBSession(sessionmaker):
    def __init__(self, database=DATABASE, reset=False):
        self.db = database
        db_exists = os.path.exists(self.db)
        if reset and db_exists:
            os.remove(DATABASE)
        self.engine = create_engine('sqlite:///' + self.db)
        super().__init__(bind=self.engine)
        Base.metadata.create_all(self.engine)
        if reset or not db_exists:
            self._fill_legends()

    def _fill_legends(self):
        session = self()

        for k, v in Legend.getACPRActivities().items():
            session.add(ACPR_authorized_activity(activity=k, name=v))
        for k, v in Legend.getACPRServices().items():
            session.add(ACPR_service(service=k, name=v))
        for k, v in Legend.getACPRInstruments().items():
            session.add(ACPR_instrument(instrument=k, name=v))
        for k, v in Legend.getCBServices().items():
            session.add(CB_service(service=k, name=v))
        for k, v in Legend.getCBInstruments().items():
            session.add(CB_instrument(instrument=k, name=v))

        session.commit()
        session.close()


class Legend(object):
    ACPR_activities = {
        1: 'Cautions réglementées',
        2: 'Compensation d\'instruments financiers',
        3: 'Tenue de compte-conservation',
        4: 'Contrepartie centrale'
    }

    ACPR_services = {
        1: 'Réception et transmission d\'ordres pour le compte de tiers',
        2: 'Exécution d\'ordres pour le compte de tiers',
        3: 'Négociation pour compte propre',
        4: 'Gestion de portefeuille pour le compte de tiers',
        5: 'Conseil en investissement',
        6: 'Prise ferme',
        7: 'Placement garanti',
        8: 'Placement non garanti',
        9: 'Exploitation d\'un système multilatéral de négociation'
    }

    ACPR_instruments = {
        1: 'Titres de capital émis par les sociétés par action',
        2: 'Titres de créance',
        3: 'Parts ou actions d\'organismes de placements collectifs',
        4: 'Instruments financiers à terme',
        5: 'Autres instruments financiers étrangers'
    }

    CB_services = {
        1: 'Réception et transmission d\'ordres pour le compte de tiers',
        2: 'Exécution d\'ordres pour le compte de tiers',
        3: 'Négociation pour compte propre',
        4: 'Gestion de portefeuille pour le compte de tiers',
        5: 'Conseil en investissement',
        6: 'Prise ferme / placement avec engagement ferme',
        7: 'Placement non garanti',
        8: 'Exploitation d\'un système multilatérale de négociation',
        9: 'Conservation et administration d\'IF pour le compte de clients, y compris la garde et les services connexes, comme la gestion de trésorerie de garanties',
        10: 'Octroi d\'un crédit ou d\'un prêt à un investisseur pour lui permettre d\'effectuer une transaction sur un ou plusieurs instruments financiers, dans laquelle intervient l\'entreprise qui octroie le crédit ou le prêt',
        11: 'Conseil aux entreprises en matière de structure du capital, de stratégie industrielle et de questions connexes - conseil et services en matière de fusions et de rachat d\'entreprises',
        12: 'Services de change lorsque ces services sont liés à la fourniture de services d\'investissement',
        13: 'Recherche en investissements et analyse financière ou toute autre forme de recommandation générale concernant les transactions sur instruments financiers',
        14: 'Services liés à la prise ferme',
        15: 'Les services et activités d\'investissement concernant le marché sous-jacent'
    }

    CB_instruments = {
        1: 'Valeurs mobilières',
        2: 'Instruments du marché monétaire',
        3: 'Parts d\'organismes de placement collectif',
        4: 'Instruments financiers à terme sur sous-jacent financier (c.f. Annexe 1 Section C de la directive MIF)',
        5: 'Instruments financiers à terme sur matières premières 1 (c.f. Annexe 1 Section C de la directive MIF)',
        6: 'Instruments financiers à terme sur matières premières 2 (c.f. Annexe 1 Section C de la directive MIF)',
        7: 'Instruments financiers à terme sur matières premières 3 (c.f. Annexe 1 Section C de la directive MIF)',
        8: 'Instruments financiers à terme dérivés de crédit (c.f. Annexe 1 Section C de la directive MIF)',
        9: 'Contrats financiers pour différences',
        10: 'Instruments financiers à terme sur sous-jacent immatériel (c.f. Annexe 1 Section C de la directive MIF)'
    }

    @staticmethod
    def getACPRActivities():
        return Legend.ACPR_activities

    @staticmethod
    def getACPRServices():
        return Legend.ACPR_services

    @staticmethod
    def getACPRInstruments():
        return Legend.ACPR_instruments

    @staticmethod
    def getCBServices():
        return Legend.CB_services

    @staticmethod
    def getCBInstruments():
        return Legend.CB_instruments
