from bs4 import BeautifulSoup
import urllib.request
import csv
import re
import sys


FIRM_LIST_FILE = 'regafi_export.csv'
FR_CIB_COLUMN_NAME = 'Code Banque (CIB) ou N° d\'enregistrement'
SAVE_DIR = 'RawResults'

WEBSITE = 'https://www.regafi.fr'
MAIN_CIB_SEARCH_URI = '/spip.php?page=results&type=advanced&id_secteur=&lang=fr&denomination=&siren=&cib=%s&bic=&nom=&siren_agent=&num=&cat=0&retrait=0'
MAIN_IN_SEARCH_URI = '/spip.php?page=results&type=advanced&id_secteur=&lang=fr&denomination=&siren=&cib=&bic=&nom=&siren_agent=&num%s=&cat=0&retrait=0'
FR_TABLE_SUMMARY = 'Résultat de votre recherche'
RESULTS_DIV_CLASSNAME = ['main', 'main_evol']


def getAllCIBs(firm_list_file):
    """ Beware: multiple entries for one given CIB behave not very well. The latest (in the list)
        overwrites the other(s?). I guess (hope...) that information about activities is the same
        for all entries."""

    with open(firm_list_file, 'r', newline='', encoding='latin-1') as f:
        # I am not very happy with this solution because it requires to keep the source file open
        # during the whole process. However, I doubt creating a cache would be more elegant...
        csvreader = csv.reader(f, delimiter=';')

        # Find index of CIB field, and incidentally move to the first content line
        line = next(csvreader)
        while len(line) == 0:
            line = next(csvreader)
        try:
            index = line.index(FR_CIB_COLUMN_NAME)
        except:
            print('An error occurred during the parsing of %s' % firm_list_file, file=sys.stderr)
            exit(-1)

        # To resume from a specific point
        while True:
            try:
                if next(csvreader)[index].split('"')[1] == '797894888':
                    break
            except IndexError: # some exempted have no identifier
                continue

        # Generate CIBs list
        try:
            while True:
                try:
                    yield next(csvreader)[index].split('"')[1]          # '=("CIB")' in csv file
                except IndexError: # some exempted have no identifier
                    continue
        except StopIteration:
            return


def downloadCIB(cib):
    """ A global request on investment firms gives access only to their CIB. To query for their authorizations, we need
        their internal id (or even better, the URI of the request) that can be retrieved through an advanced search
        using the CIB of the firm. Hence the two step process ...
        :return Search Results DIV tag, or None
    """
    def findSearchResultsDiv(tag):
        return tag.name == 'div' and tag.has_attr('class') and tag['class'] == RESULTS_DIV_CLASSNAME


    try:
        searchURIWithID = retrieveSearchURIWithID(cib)
    except:
        print('Unable to retrieve searchURI for CIB %s' % cib, file=sys.stderr)
        return None

    soup = BeautifulSoup(urllib.request.urlopen(WEBSITE + searchURIWithID).read(), "lxml")
    return soup.find(findSearchResultsDiv)


def retrieveSearchURIWithID(cib):
    """ Parsing strategy:
            * find the table (no condition on the node type needed) with attribute summary='Search results
            * in this node find a hyperlink markup with href referring to a non-empty id
    """
    def findSearchResultsTable(tag):
        return tag.has_attr('summary') and tag['summary'] == FR_TABLE_SUMMARY

    def findSearchURIWithID(tag):
        return tag.name == 'a' and re.match('.*;id=\d+.*$', tag.__str__())

    if int(cib) < 100000: # real CIB
        searchURL = WEBSITE + MAIN_CIB_SEARCH_URI % cib
    else:
        searchURL = WEBSITE + MAIN_IN_SEARCH_URI % cib

    soup = BeautifulSoup(urllib.request.urlopen(searchURL).read(), "lxml")
    searchURIWithID = soup.find(findSearchResultsTable).find(findSearchURIWithID)['href']
    return searchURIWithID


def processCIB(cib):
    searchResultsDiv = downloadCIB(cib)
    if searchResultsDiv is None:
        print("Error while processing CIB %s, skipping" % cib, file=sys.stderr)
    else:
        with open(SAVE_DIR + '/' + cib + '.div', 'w') as f:
            f.write(searchResultsDiv.prettify())


def main():
    print("Starting...")
    for cib in getAllCIBs(FIRM_LIST_FILE):
        #Beware: cib may contain a registering number instead
        print("Processing CIB %s..." % cib)
        processCIB(cib)


if __name__ == '__main__':
    main()