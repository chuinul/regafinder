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


import logging


def enable(level=logging.ERROR):
    logger.consoleHandler.setLevel(level)
    logger.disabled = False


def disable():
    logger.disabled = False


def _prepare():
    consoleHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler('rega.log')
    fileHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s (%(name)s)')
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)
    logger.disabled = True


logger = logging.getLogger('regalog')
_prepare()
