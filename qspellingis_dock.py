# -*- coding: utf-8 -*-
"""
/***************************************************************************
QspellinGIS
                                 A QGIS plugin
 A spelling plugin with basic functionality from Go2NextFeature and
 with inclusion of spell checking code adapted from pyqt_spellchecker
 
 Requires pySpellChecker (Pyenchant optional) - the actual spelling libraries
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


"""

from builtins import str
from pathlib import Path
import os.path
import platform

from collections import OrderedDict

from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsMessageBar, QgsMapToolIdentifyFeature
from qgis.core import QgsProject, Qgis, QgsMapLayerProxyModel, QgsFieldProxyModel, edit, QgsFeature, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMapLayerType
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, Qt, QRect, QSize
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame, QFormLayout, QLabel, QLineEdit, QHBoxLayout, QTabWidget,\
    QScrollArea, QRadioButton, QButtonGroup, QCheckBox, QPushButton, QShortcut, QDockWidget, QSizePolicy, QSpacerItem, QGroupBox, QFileDialog
from qgis.PyQt.QtGui import QKeySequence, QCursor, QPixmap, QIcon

import operator


# spell check imports

from .pyqt_spellcheck.spellcheckwrapper import SpellCheckWrapper
from .pyqt_spellcheck.spelltextedit import SpellTextEdit
global enchantment
try:
    from enchant import Broker
    enchantment = "Enchant available"
except:
    if platform.system() !="Windows": 
        enchantment = "Enchant not installed"
    else:
        enchantment = ""
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qspellingis_dock.ui'))


class qspellingisDock(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    plugin_name = 'QspellinGIS'

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(qspellingisDock, self).__init__(parent)
        self.setupUi(self)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.iface = iface
        self.feats_od = OrderedDict()
        self.ft_pos = -1
        self.sel_ft_pos = -1
        self.sel_ft_ids = None
        self.tool = None

        self.setup()

    def closeEvent(self, event):
        self.currentLayer = None
        self.writeini()
        self.closingPlugin.emit()
        event.accept()

    def setup(self):
        self.setWindowTitle(qspellingisDock.plugin_name)
        self.canvas = self.iface.mapCanvas()
        #Connect form actions to signals
        pix=QPixmap(os.path.join(os.path.dirname(__file__), 'qspellingis.png')) 
        pix.scaledToWidth(120)
        self.labelLogo.setPixmap(pix)
        pix=QPixmap(os.path.join(os.path.dirname(__file__), 'refresh.png'))
        self.layerRefresh.setIcon(QIcon(pix))
        self.layerRefresh.setIconSize(QSize(24,24))
        self.homepath = str(Path.home())
        self.personal = os.path.join(Path.home(), 'qspellingis_pwl.txt')
        self.pwl_filename.setText(self.personal)
        self.setSpell.activated.connect(self.changeSpeller)
        self.layerRefresh.pressed.connect(self.populateLayers)
        self.lang.activated.connect(self.changeLanguage)
        self.pwl_select.pressed.connect(self.selectPWL)
        self.MapLayer.layerChanged.connect(self.update_textboxes)
        self.Tabs.currentChanged.connect(self.tabChanged)
        self.FieldOrderBy.fieldChanged.connect(self.cbo_attrib_activated) #Added
        self.chk_use_sel.toggled.connect(self.chk_use_sel_clicked)
        self.btn_first.pressed.connect(self.btn_first_pressed)
        self.btn_prev.pressed.connect(self.btn_prev_pressed)
        self.btn_next.pressed.connect(self.btn_next_pressed)
        self.btn_last.pressed.connect(self.btn_last_pressed)
        self.save_record.pressed.connect(self.save_record_pressed)
        self.cancel_record.pressed.connect(self.cancel_save)
        self.identify_feature.toggled.connect(self.identify_features)
        self.selected_feature = QgsFeature()
        QgsProject.instance().readProject.connect(self.onLoadProject)
        self.byod_Filename.setVisible(False)
        
        self.byod_file = ""
        
        self.setSpell.addItem("pyspellchecker")
        if not enchantment:
            self.feedback.setVisible(False)
        if platform.system() !="Windows" and enchantment == "Enchant available":
            self.setSpell.addItem("pyenchant")
        self.feedback.setText(enchantment)
        self.changeSpeller()
        self.readini()

        # Set controls
        self.chk_use_sel.setEnabled(False)
        self.FieldOrderBy.setEnabled(True) #added
        self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.canvasradio = QButtonGroup()
        self.canvasradio.addButton(self.rad_action_pan,1)
        self.canvasradio.addButton(self.rad_action_zoom,2)
        self.canvasradio.addButton(self.rad_action_identify,3)
        self.canvasradio.setExclusive(True)
        self.canvasradio.buttonClicked.connect(self.canvasChoice)
        self.moveCanvas = "pan" #default canvas action
        # Shortcut
        shortcut = QShortcut(QKeySequence(Qt.Key_F8), self.iface.mainWindow())
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(self.btn_next_pressed)
        self.populateLayers()
        
    def readini(self):
        if os.path.isfile(os.path.join(os.path.dirname(__file__),"qspellingis.ini")):
            with open(os.path.join(os.path.dirname(__file__),"qspellingis.ini"), 'r') as f:
                self.defaults = [line.strip() for line in f]
                if self.defaults:
                    self.setSpell.setCurrentText(self.defaults[0]) # spelling library
                    self.lang.setCurrentText(self.defaults[1]) #language
                    self.personal = self.defaults[2] # personal word list
                    pwlFilename = self.personal.split('/')
                    if "\\" in str(pwlFilename[-1]):
                        pwlFilename = str(pwlFilename[-1]).split('\\')
                    self.pwl_filename.setText(pwlFilename[-1])
                    self.pwl_filename.setToolTip(self.personal)
                    try:
                        self.byod_file = self.defaults[3] # Bring-your-own
                    except:
                        self.byod_file = ""
                    if self.byod_file:
                        self.byod_Filename.setVisible(True)
                        byod_name = self.byod_file.split('/')
                        if "\\" in str(byod_name[-1]):
                            byod_name = str(byod_name[-1]).split('\\')
                        self.byod_Filename.setText(byod_name[-1])
                        self.byod_Filename.setToolTip(self.byod_file)
                    self.spellIn = SpellCheckWrapper(self.setSpell.currentText(),self.lang.currentText(),self.getWords(),self.personal,self.byod_file)

    def writeini(self):
        with open(os.path.join(os.path.dirname(__file__),"qspellingis.ini"), 'w') as f:
            defaults = self.setSpell.currentText()+'\n'+ self.lang.currentText()+'\n'+ self.personal 
            if self.byod_file:
                defaults += '\n'+ self.byod_file         
            f.write(defaults)   
            
    def tabChanged(self):
        if self.Tabs.currentIndex() == 1:
            if self.MapLayer.currentLayer() and self.moveCanvas!="identify": 
                self.btn_first_pressed()
            elif self.MapLayer.currentLayer() and self.moveCanvas=="identify":
                self.identify_feature.setChecked(True)
                self.identify_features()
                
    def selectPWL(self):
        pwlFilename, fileType = QFileDialog.getOpenFileName(self, "Select your own Personal Word List location", self.homepath, "*.txt")
        if pwlFilename:
            self.personal = pwlFilename
            pwlFilename = self.personal.split('/')
            if "\\" in str(pwlFilename[-1]):
                pwlFilename = str(pwlFilename[-1]).split('\\')
            self.pwl_filename.setText(pwlFilename[-1])
            self.pwl_filename.setToolTip(self.personal)

    def byod(self):
        byodFilename, fileType = QFileDialog.getOpenFileName(self,'BYOD - gzipped word frequency list',self.homepath,"*.gz")
        if byodFilename:
            self.byod_file = str(byodFilename)
            self.byod_Filename.setVisible(True)
            return
            
    def getWords(self) -> list[str]:
        if os.path.isfile(self.personal):
            with open(self.personal, 'r') as f:
                self.word_list = [line.strip() for line in f]
            #print("PWL: ",self.word_list)

        else:
            with open(self.personal, 'a') as f: #create a new pwl if one doesn't exist
                f.write("qgis")
            self.word_list = ["qgis"]
        return self.word_list

    def changeSpeller(self):
        self.spellIn = SpellCheckWrapper(self.setSpell.currentText(),None,self.getWords(),self.personal,None)
        self.availableLanguages()
            
    def availableLanguages(self): 
            self.lang.clear()
            #self.lang.addItem("Select language")
            languages = self.spellIn.get_languages()

            for language in languages:
                self.lang.addItem(language)
            if self.setSpell.currentText() == "pyspellchecker":
                if "en-gb" not in languages: 
                    self.lang.addItem("en-gb")
                self.lang.addItem("Bring-your-own")
                
    def changeLanguage(self):        
        if self.lang.currentText() == "Bring-your-own":
            self.byod()
        elif self.lang.currentText() == "en-gb":
            self.byod_file = str(os.path.join(os.path.dirname(__file__),"pyqt_spellcheck","en-gb.json.gz"))

        else:
            self.byod_file = ""
        if self.byod_file:
            byod_name = self.byod_file.split('/')
            if "\\" in str(byod_name[-1]):
                byod_name = str(byod_name[-1]).split('\\')
            self.byod_Filename.setText(byod_name[-1])
        else:
            self.byod_Filename.setText("")
        self.byod_Filename.setToolTip(self.byod_file)
        #print(language, self.byod_file)
        
        self.spellIn = SpellCheckWrapper(self.setSpell.currentText(),self.lang.currentText(),self.getWords(),self.personal,self.byod_file)
        self.spellIn.load_words(self.word_list)
        #print(self.spellIn.spelldict.word_frequency.longest_word_length)
        self.update_textboxes()


        
    def onLoadProject(self):
        self.map_layers = QgsProject.instance()
        self.populateLayers()
        self.layer_label.setText('Layer: ')
        self.layer_label.setStyleSheet("background: None")

    def populateLayers(self):
        
        self.map_layers = QgsProject.instance().mapLayers().values()
        self.visible_layers = QgsProject.instance().layerTreeRoot()
        self.allow_list = [lyr.id() for lyr in self.map_layers if lyr.type() == QgsMapLayerType.VectorLayer and self.visible_layers.findLayer(lyr).isVisible()]
        #layers available: vector and currently visible on canvas. Then filter the combobox to exclude other layers
        self.except_list = [l for l in self.map_layers if l.id() not in self.allow_list]
        self.MapLayer.setExceptedLayerList(self.except_list)
        self.MapLayer.setAllowEmptyLayer(True)
        self.MapLayer.setCurrentIndex(0)
        self.feats_od.clear()
        feats_d = {}
        

    def update_textboxes(self):
    
        #When changing layer: on Spelling tab reset the layer fields - remove any existing from the previous layer
        for i in reversed(range(self.formLayout.count())): 
            widgetToRemove = self.formLayout.itemAt(i).widget()
            # remove it from the layout list
            self.formLayout.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)
        self.currentfeature = []
        self.currentLayer = self.MapLayer.currentLayer()
        if self.currentLayer:
            self.layer_label.setText('Layer: '+str(self.currentLayer.name()))
            #self.layer_label.setStyleSheet("background: DarkSeaGreen")
            self.FieldOrderBy.setLayer(self.currentLayer)
            self.widgetBox = QWidget()
            # get the list of selected layer's fields
            self.fields = [(field.name(), field.type()) for field in self.FieldOrderBy.fields()]
            # add QLabels and SpellTextEdit (text fields) / QLineEdits inside frame
            for row,(field_name, field_type) in enumerate(self.fields):
                # label keep width to minimum by adding spaces to allow wrap
                field_name = field_name.replace("."," ")
                field_name = field_name.replace("_"," ")
                fieldlabel = QLabel(field_name)
                fieldlabel.resize(40,20)
                fieldlabel.setWordWrap(True)
                fieldlabel.setToolTip(field_name)
                if field_type == 10:
                    self.currentfeature.append(SpellTextEdit(self.spellIn, self.widgetBox))
                else:
                    self.currentfeature.append(QLineEdit())
                self.formLayout.addRow(fieldlabel,self.currentfeature[-1])
                fields = self.MapLayer.currentLayer().fields()
                #do not enable fields from joined layers 
                if fields.fieldOrigin(row) == 2:# or field_type != 10:
                    self.currentfeature[row].setEnabled(False)            
                else:
                    self.currentfeature[row].setEnabled(True) 
            #print(self.currentfeature)
            self.widgetBox.setLayout(self.formLayout)
            self.scrollArea.setWidget(self.widgetBox)
            self.scrollArea.setWidgetResizable(True)
            #resize frame to the available space
            widgetheight = self.fra_main.frameGeometry().height()
            widgetwidth = self.fra_main.frameGeometry().width()
            self.Tabs.resize(widgetwidth - 15,widgetheight - 20)
            self.scrollArea.resize(widgetwidth - 15,widgetheight - 75)
            self.ft_pos = -1
            self.mapTool = None
            self.identify_feature.setChecked(False)
            self.cbo_attrib_activated()
        else:
            self.layer_label.setText('Please select a layer first')

    def identify_features(self):
        self.mapTool = None
        if self.identify_feature.isChecked():
            self.rad_action_identify.setChecked(True)
            self.moveCanvas = "identify"
            self.btn_first.setEnabled(False)
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_last.setEnabled(False)
            self.mapTool = QgsMapToolIdentifyFeature(self.canvas)
            self.mapTool.setLayer(self.MapLayer.currentLayer())
            self.cursor = QCursor()
            self.cursor.setShape(Qt.WhatsThisCursor)
            self.mapTool.setCursor(self.cursor)
            self.canvas.setMapTool(self.mapTool)
            self.mapTool.featureIdentified.connect(self.onFeatureIdentified)
        else:
            #reset the increment to start again - TODO: find a way of continuing from the last identified feature
            self.ft_pos = -1
            self.cbo_attrib_activated()
            self.selected_feature = QgsFeature()
           
            
    def onFeatureIdentified(self, feature):
       #check if the feature has been changed in Text boxes
        if self.selected_feature.id() >=0:
            for row,(field_name, field_type) in enumerate(self.fields):
                if field_type == 10:
                    prev_value = self.selected_feature.attribute(field_name) #get saved value for comparison
                    #print('selected', self.selected_feature.id(), prev_value, self.currentfeature[row].toPlainText())
                    if self.currentfeature[row].toPlainText() != str(prev_value):
                        self.currentfeature[row].setStyleSheet("background: red")
                        self.save_record.setStyleSheet("background: red")
                        return        
        self.save_record.setStyleSheet("background: None")
        self.selected_feature = feature
        ft = feature.id()
        self.CountFeatures.setText("%d of %d features" % (ft, len(self.feats_od)))
        # update the values in each text box
        for row,(field_name, field_type) in enumerate(self.fields):
            attrib_value = feature.attribute(field_name) 
            #print(attrib_value)
            if field_type == 10:
                self.currentfeature[row].setPlainText(str(attrib_value))
                self.currentfeature[row].setStyleSheet("background: None") 
            else:
                self.currentfeature[row].setText(str(attrib_value))
        

    def save_record_pressed(self):

        if self.identify_feature.isChecked():
            fid = self.selected_feature.id()
        else:
            fid = self.feats_od[self.ft_pos].id() # get the row number
        
        CurrentLayer = self.MapLayer.currentLayer()
        if CurrentLayer.isEditable() :
            for row,(field_name, field_type) in enumerate(self.fields):
                #update record in layer
                if field_type == 10:
                    CurrentLayer.changeAttributeValue(fid,row, self.currentfeature[row].toPlainText())
                    self.currentfeature[row].setStyleSheet("background: None") 
                    #print('is.editable', fid, self.currentfeature[row].toPlainText())
#               allow integers and decimals to be updated - for future! Need additional checks when moving feature
#                elif field_type == 4:
#                    CurrentLayer.changeAttributeValue(fid,row, float(self.currentfeature[row].currentText()))
#                    self.currentfeature[row].setStyleSheet("background: None") 
#                elif field_type == 2:
#                    CurrentLayer.changeAttributeValue(fid,row, int(self.currentfeature[row].currentText()))
#                    self.currentfeature[row].setStyleSheet("background: None")                 
                else:
                    pass

        else:
            with edit(CurrentLayer):
                for row,(field_name, field_type) in enumerate(self.fields):
                    #update record in layer
                    if field_type == 10:
                        CurrentLayer.changeAttributeValue(fid,row, self.currentfeature[row].toPlainText())
                        self.currentfeature[row].setStyleSheet("background: None") 
                        #print('edit', fid, self.currentfeature[row].toPlainText())
                else:
                        pass
        self.selected_feature = CurrentLayer.getFeature(fid)
        self.save_record.setStyleSheet("background: DarkSeaGreen")
        self.btn_next.setStyleSheet("background: None")
        self.btn_prev.setStyleSheet("background: None")
#        self.cbo_attrib_activated()
             

    def cancel_save(self):


        #reset fields to their stored value
        for row,(field_name, field_type) in enumerate(self.fields):
            if self.identify_feature.isChecked():
                attrib_value = self.selected_feature.attribute(field_name) 
            else:
                attrib_value = self.feats_od[self.ft_pos].attribute(field_name) 
            #print(attrib_value)
            if field_type == 10:
                self.currentfeature[row].setPlainText(str(attrib_value))
                self.currentfeature[row].setStyleSheet("background: None") 
            else:
                self.currentfeature[row].setText(str(attrib_value))
        self.btn_next.setStyleSheet("background: None")
        self.btn_prev.setStyleSheet("background: None") 

        
    def canvasChoice(self):
        if self.canvasradio.checkedId() == 1:
            self.moveCanvas = "pan"
            self.identify_feature.setChecked(False)
            self.mapTool = None
        elif self.canvasradio.checkedId() == 2:
            self.moveCanvas = "zoom"
            self.identify_feature.setChecked(False)
            self.mapTool = None
        elif self.canvasradio.checkedId() == 3:
            self.moveCanvas = "identify"
            self.identify_feature.setChecked(True)
    

    def chk_use_sel_clicked(self):

        self.sel_ft_ids = self.MapLayer.currentLayer().selectedFeatureIds()
        if self.chk_use_sel.isChecked() and len(self.sel_ft_ids) < 1:
            self.iface.messageBar().pushMessage(
                qspellingisDock.plugin_name,
                'Please select at least one feature.',
                Qgis.Warning)  # TODO: softcode
            return

        self.ft_pos = -1
        self.sel_ft_pos = -1

        # Reset buttons
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)


    def lay_selection_changed(self):
        self.chk_use_sel.setChecked(False)

    def cbo_attrib_activated(self):

        if self.MapLayer.currentLayer() is None:
            return

        #Added check whether orderBy is empty
        if self.FieldOrderBy.currentField() is None:
            return

        self.feats_od.clear()

        feats_d = {}
        for feat in self.MapLayer.currentLayer().getFeatures():
            feats_d[feat] = feat.attribute(self.FieldOrderBy.currentField())
            #print(feats_d[feat])
        # Order features by chosen attribute
        feats_d_s = [(k, feats_d[k]) for k in sorted(feats_d, key=feats_d.get, reverse=False)]
        #print(feats_d_s)
        pos = 0
        for k, v in feats_d_s:
            self.feats_od[pos] = k
            pos += 1

        if self.ft_pos >= 0:
            self.btn_prev.setEnabled(True)
            self.cancel_save() 
        else:
            self.ft_pos = -1
            self.btn_prev.setEnabled(False)
        self.chk_use_sel.setEnabled(True)
        self.FieldOrderBy.setEnabled(True) 
        self.btn_next.setEnabled(True)
        self.btn_last.setEnabled(True)
        self.btn_first.setEnabled(True)
 
# Navigation - set the increment for moving through the list
  
    def btn_first_pressed(self):

        start_point = -(self.ft_pos)
        self.move_ft(start_point)
   
    def btn_prev_pressed(self):

        self.move_ft(-1)

    def btn_next_pressed(self):

        self.move_ft(1)

    def btn_last_pressed(self):

        end_point = len(self.feats_od) - self.ft_pos
        self.move_ft(end_point)


    def move_ft(self, increment): # change feature by iterating or on canvas select

        if self.ft_pos > -1:
            #check if any attributes have been changed in Text boxes before trying to load another feature
            for row,(field_name, field_type) in enumerate(self.fields):
                if field_type == 10:
                    prev_value = self.feats_od[self.ft_pos].attribute(field_name) 
                    if self.currentfeature[row].toPlainText() != str(prev_value):
                        self.currentfeature[row].setStyleSheet("background: red")
                        self.btn_next.setStyleSheet("background: red")
                        self.btn_prev.setStyleSheet("background: red")
                        return
        self.ft_pos += increment

        self.ft_pos = max(self.ft_pos, 0)
        self.sel_ft_pos = max(self.ft_pos, 0)
        self.ft_pos = min(self.ft_pos, len(self.feats_od) - 1)
        self.sel_ft_pos = min(self.ft_pos, len(self.feats_od) - 1)

        if self.chk_use_sel.isChecked():

            while not self.feats_od[self.ft_pos].id() in self.sel_ft_ids:
                self.ft_pos += increment
                if self.ft_pos >= len(self.feats_od) - 1 or self.ft_pos <= 0:
                    self.ft_pos -= increment
                    return

            self.sel_ft_pos += increment
            if self.sel_ft_pos == len(self.sel_ft_ids): # i.e. at the end
                self.btn_next.setEnabled(False)
            if self.sel_ft_pos == 0: # i.e. at the start
                self.btn_prev.setEnabled(False)
# move the map canvas (zoom or pan) to the current feature
        if 0 <= self.ft_pos < len(self.feats_od): #i.e. not at either end
            try:
                renderer = self.iface.mapCanvas().mapSettings()
                geom = self.feats_od[self.ft_pos].geometry()

                if geom is None:
                    self.iface.messageBar().pushInfo(
                        qspellingisDock.plugin_name,
                        'The geometry of the feature is null: can neither zoom nor pan to it.')  # TODO: softcode

                else:

                    if self.moveCanvas == "pan":
                        self.iface.mapCanvas().setCenter(renderer.layerToMapCoordinates(
                            self.currentLayer,
                            geom.centroid().asPoint()))

                    elif self.moveCanvas == "zoom":
                        self.iface.mapCanvas().setExtent(renderer.layerToMapCoordinates(
                            self.currentLayer,
                            geom.boundingBox()))
                        self.iface.mapCanvas().zoomByFactor(1.1)
                    else:
                        pass

                self.iface.mapCanvas().refresh()
            except:
                pass
            fields = [(field.name(), field.type()) for field in self.MapLayer.currentLayer().fields()]

            # update the values in each text box
            for row,(field_name, field_type) in enumerate(self.fields):
                attrib_value = self.feats_od[self.ft_pos].attribute(field_name) 
                #print(attrib_value)
                if field_type == 10:
                    self.currentfeature[row].setPlainText(str(attrib_value))
                    self.currentfeature[row].setStyleSheet("background: None") 
                else:
                    self.currentfeature[row].setText(str(attrib_value))

        if self.ft_pos >= len(self.feats_od) - 1:
            self.btn_next.setEnabled(False)
        else:
            self.btn_next.setEnabled(True)

        if len(self.feats_od) > 1 and self.ft_pos > 0:
            self.btn_prev.setEnabled(True)
        else:
            self.btn_prev.setEnabled(False)   
        self.save_record.setStyleSheet("background: None")
        self.CountFeatures.setText("%d of %d features" % (self.ft_pos+1, len(self.feats_od)))

