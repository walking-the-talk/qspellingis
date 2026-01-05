# -*- coding: utf-8 -*-
"""
/***************************************************************************
QspellinGIS
                                 A QGIS plugin
 A spelling plugin with basic functionality from Go2NextFeature and
 with inclusion of spell checking code adapted from pyqt_spellchecker
 
 Requires PyEnchant and pySpellChecker - the actual libraries
                             -------------------
        begin                : 2024-07-14
        git sha              : $Format:%H$
        copyright            : (C) 2025 Walking-the-Talk
        email                : chris.york@walking-the-talk.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

"""
/***************************************************************************
 Modified from Go2NextFeature (C) 2016 by Alberto De Luca for Tabacco Editrice
 Modified version of pyqt_SpellCheck is included under MIT licence 
 (see relevant submodule)

 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load qspellingis class from file qspellingis.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .qspellingis import qspellingis
    return qspellingis(iface)
