#!/usr/bin/python3

import os
import argparse
from bs4 import BeautifulSoup
from BaseDeclarations import RegafiDBSession
from Company import Company


SAVE_DIR = 'RawResults'


def main(args):
    DBSession = RegafiDBSession(reset=args.force_rebuild)

    session = DBSession()
    for filename in os.listdir(SAVE_DIR):
        cib = filename.split('.')[0]
        # Do not process agents
        if int(cib) > 100000:
            continue

        with open(SAVE_DIR + '/' + filename, 'r') as f:
            mainDiv = BeautifulSoup(f.read(), "lxml")

        company = Company.makeFromMainDiv(mainDiv, cib)
        if company is not None:
            company.save(session)
    session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
                                     'This software rebuilds the Regafi database and '
                                     'so that you can exploit it more conveniently, '
                                     'performing searches on several criteria instead of '
                                     'just being able to look for specific institutions.')
    parser.add_argument('-f', '--force-rebuild', action='store_true',\
                        help='Force to rebuild all the database from scratch.')

    args = parser.parse_args()
    main(args)
