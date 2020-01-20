#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('..')
import os.path
import platform
import re
import time
import datetime
import serial
import json
import copy
import design
import traceback

from serial import Serial
from sportiduino import Sportiduino, BaseStation
from datetime import datetime, timedelta
from PyQt5 import uic, QtWidgets, QtPrintSupport, QtCore, sip
from PyQt5.QtCore import QSizeF, QDateTime, QTime
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import QTranslator
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import QCoreApplication
from six import int2byte, byte2int, iterbytes, print_, PY3

_translate = QCoreApplication.translate

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("SportiduinoPQ v0.7.1")
        
        self.log =''
        self.readData = []
        self.dumpData = []
        self.connected = False
        self.CardNum = '0'
        self.printer = QPrinter()
        self.ui.printerName.setText(self.printer.printerName())
        
        self.initTime = datetime.now()
        self.addText('{:%Y-%m-%d %H:%M:%S}'.format(self.initTime))
        
        dt = QDateTime.currentDateTime()
        tm = QTime(dt.time().hour(), dt.time().minute(), 0)
        dt.setTime(tm)
        self.ui.dtCompetion.setDateTime(dt)

        availablePorts = []
        if platform.system() == 'Linux':
            availablePorts = [os.path.join('/dev', f) for f in os.listdir('/dev') if
                              re.match('ttyUSB.+', f)]
        elif platform.system() == 'Windows':
            availablePorts = ['COM' + str(i) for i in range(32)]
        self.ui.choiseCom.addItems(availablePorts)
        self.ui.cbUartPort.addItems(availablePorts)

        self.ui.Connect.clicked.connect(self.Connect_clicked)
        self.ui.ReadCard.clicked.connect(self.ReadCard_clicked)
        self.ui.InitCard.clicked.connect(self.InitCard_clicked)
        self.ui.SetTime.clicked.connect(self.SetTime_clicked)
        self.ui.SetNum.clicked.connect(self.SetNum_clicked)
        self.ui.SetStart.clicked.connect(self.SetStart_clicked)
        self.ui.SetFinish.clicked.connect(self.SetFinish_clicked)
        self.ui.CheckSt.clicked.connect(self.CheckSt_clicked)
        self.ui.ClearSt.clicked.connect(self.ClearSt_clicked)
        self.ui.LogCard.clicked.connect(self.LogCard_clicked)
        self.ui.ReadLog.clicked.connect(self.ReadLog_clicked)
        self.ui.SleepCard.clicked.connect(self.SleepCard_clicked)
        self.ui.PassCard.clicked.connect(self.PassCard_clicked)
        self.ui.SaveSet.clicked.connect(self.SaveSet_clicked)
        self.ui.LoadSet.clicked.connect(self.LoadSet_clicked)
        self.ui.SelectPrinter.clicked.connect(self.SelectPrinter_clicked)
        self.ui.Print.clicked.connect(self.Print_clicked)
        self.ui.btnApplyPwd.clicked.connect(self.ApplyPwd_clicked)
        self.ui.btnCreateInfoCard.clicked.connect(self.CreateInfo_clicked)
        self.ui.btnReadInfo.clicked.connect(self.ReadInfo_clicked)
        self.ui.btnUartRead.clicked.connect(self.SerialRead_clicked)
        self.ui.btnUartWrite.clicked.connect(self.SerialWrite_clicked)
        self.ui.btnClearText.clicked.connect(self.ClearText_clicked)

    def Connect_clicked(self):

        self.addText("")
        
        if self.connected:
            self.sportiduino.disconnect()
            text = _translate("sportiduinopq","Master station is disconnected")
            self.addText(text)
            self.connected = False
            self.ui.Connect.setText(_translate("MainWindow", "Connect"))
        else:
            port = self.ui.choiseCom.currentText()
            try:
                if (port == _translate("MainWindow", "auto")):
                    self.sportiduino = Sportiduino(debug=True)
                else:
                    self.sportiduino = Sportiduino(port,debug=True)

                #settings = self.sportiduino.read_settings()
                #self.ui.sbCurPwd1.setValue(settings['password'][0])
                #self.ui.sbCurPwd2.setValue(settings['password'][1]) 
                #self.ui.sbCurPwd3.setValue(settings['password'][2])
                #
                #self.showSettings(settings['bits'])
                #idx = (settings['antennaGain'] >> 4) - 2
                #self.ui.cbAntennaGain.setCurrentIndex(idx)
                
                self.sportiduino.beep_ok()
                self.connected = True
                text = _translate("sportiduinopq","Master station {} on port {} is connected").format(self.sportiduino.version, self.sportiduino.port)
                self.addText(text)
                self.ui.Connect.setText(_translate("MainWindow", "Disconn."))
                
            except BaseException as err:
                self._process_error(err)
                self.connected = False

    def ReadCard_clicked(self):
        if self._check_connection() == False:
            return

        try:
            self.addText(_translate("sportiduinopq","Read a card"))
            
            card_type = self.sportiduino.read_card_type()
            raw_data = self.sportiduino.read_card_raw()
            
            data = Sportiduino.raw_data_to_card_data(raw_data)
            
            self.showCardData(data, card_type)
            self.saveCardDataJson(data)
            
        except BaseException as err:
            self._process_error(err)

    def InitCard_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Initialize the participant card"))
        
            text = self.ui.cardLine.text()
        
            if(text.isdigit()):
                self.CardNum = text
            else:
                self.CardNum = '0'

            num = int(self.CardNum)
        
            if (num < Sportiduino.MIN_CARD_NUM or num > Sportiduino.MAX_CARD_NUM):
                raise BaseException(_translate("sportiduinopq","Not correct card number"))
            
            code, data = self.sportiduino.init_card(num)
            
            if (self.ui.AutoIncriment.checkState() != 0):
                self.AutoIn = True
                self.CardNum = str(num + 1)
                self.ui.cardLine.setText(self.CardNum)
            
            if code == Sportiduino.RESP_OK :
                self.addText(_translate("sportiduinopq","The participant card N{} ({}) has been initialized successfully")
                    .format(num, Sportiduino.card_name(data[0])))
            
        except BaseException as err:
            self._process_error(err)
            
    def SetNum_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set number of a base station"))
            num = self.ui.sbStationNum.value()
        
            if num == 0 or num > 255:
                raise BaseException(_translate("sportiduinopq","Not correct station number"))
            
            self.sportiduino.init_cp_number_card(num)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
                            
    def SetTime_clicked(self):
        if self._check_connection() == False :
            return

        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set clock of a base station. Put the card on a base station after second signal"))
            self.sportiduino.init_time_card(datetime.utcnow() + timedelta(seconds=3))
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def SetStart_clicked(self):
        if self._check_connection() == False :
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set a base station as the start station"))
            self.sportiduino.init_cp_number_card(Sportiduino.START_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.START_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def SetFinish_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set a base station as the finish station"))
            self.sportiduino.init_cp_number_card(Sportiduino.FINISH_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.FINISH_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def CheckSt_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set a base station as the check station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CHECK_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CHECK_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def ClearSt_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to set a base station as the clear station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CLEAR_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CLEAR_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def LogCard_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
        
            self.addText(_translate("sportiduinopq","Write the master card to get log of a base station"))
            self.sportiduino.init_backupreader()
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
                
    def ReadLog_clicked(self):
        if self._check_connection() == False:
            return

        text = ""
        
        try:
            self.addText(_translate("sportiduinopq","Read the card contained log of a base station"))
            
            data = self.sportiduino.read_backup()
            
            if data['cp'] == 0:
                raise BaseException(_translate("sportiduinopq","No log data available"))
            
            text = _translate("sportiduinopq","Station N: {} ").format(data['cp']) + "\n"

            cards = data['cards']
            
            text += _translate("sportiduinopq","Total punches {}").format(len(cards)) + "\n"
            
            text += _translate("sportiduinopq","Cards:") + " "
                        
            for i in range(0, len(cards), 1):
                if i > 0:
                    text += ", "
                text += "{}".format(cards[i])
                
            self.addText(text)
                
            self.dumpData.append(data)
            dumpFile = open(os.path.join('data','dumpData{:%Y%m%d%H%M%S}.json'.format(self.initTime)),'w')
            json.dump(self.dumpData, dumpFile)
            dumpFile.close()

        except BaseException as err:
            self._process_error(err)

    def SleepCard_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Write the master card to sleep a base station"))
            self.sportiduino.init_sleepcard(self.ui.dtCompetion.dateTime().toUTC())
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def PassCard_clicked(self):
        if self._check_connection() == False:
            return
        
        try:

            self.addText(_translate("sportiduinopq","Write the master card to write new password and settings to a base station"))
            setSt = self.getSettingsFromUI()

            oldPass = self.ui.sbOldPwd1.value()<<16 | self.ui.sbOldPwd2.value()<<8 | self.ui.sbOldPwd3.value()
            newPass = self.ui.sbNewPwd1.value()<<16 | self.ui.sbNewPwd2.value()<<8 | self.ui.sbNewPwd3.value()
            
            gain = (self.ui.cbAntennaGain.currentIndex() + 2) << 4
        
            self.sportiduino.init_passwd_card(oldPass,newPass,setSt,gain)
                
            self.ui.sbCurPwd3.setValue(self.ui.sbNewPwd3.value())
            self.ui.sbCurPwd2.setValue(self.ui.sbNewPwd2.value())
            self.ui.sbCurPwd1.setValue(self.ui.sbNewPwd1.value())
            
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
            
    def ApplyPwd_clicked(self):
        if self._check_connection() == False:
            return

        curPass = self.ui.sbCurPwd1.value()<<16 | self.ui.sbCurPwd2.value()<<8 | self.ui.sbCurPwd3.value()
        
        try:
            self.addText(_translate("sportiduinopq","Apply the current password"))
            
            self.sportiduino.apply_pwd(curPass)
            self.addText(_translate("sportiduinopq","The password has been applied successfully"))

        except BaseException as err:
            self._process_error(err)
            
    def CreateInfo_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
           
            self.addText(_translate("sportiduinopq","Write the master card to get info about a base station"))
            self.sportiduino.init_info_card()
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
        
    def ReadInfo_clicked(self):
        if self._check_connection() == False:
            return
        
        try:
            
            self.addText(_translate("sportiduinopq","Read the card contained info about a base station"))
            bs = self.sportiduino.read_info_card()
            self.showBaseStationInfo(bs)
            
        except BaseException as err:
            self._process_error(err)
            
    def LoadSet_clicked(self):
        
        self.addText("\n" + _translate("sportiduinopq","Load settings from file /data/settings.json"))
        
        try:  
            
            file = open(os.path.join('data','settings.json'),'r')
            
            obj = json.load(file);
            
            file.close()
            
            settings = obj['settings']
            gain = obj['gain']
            pwd1 = obj['pwd1'] 
            pwd2 = obj['pwd2']
            pwd3 = obj['pwd3']
            
            self.showSettings(settings)
            
            self.ui.cbAntennaGain.setCurrentIndex(gain)
            
            self.ui.sbCurPwd1.setValue(pwd1)
            self.ui.sbCurPwd2.setValue(pwd2)
            self.ui.sbCurPwd3.setValue(pwd3)
            self.ui.sbOldPwd1.setValue(pwd1)
            self.ui.sbOldPwd2.setValue(pwd2)
            self.ui.sbOldPwd3.setValue(pwd3)
            
            self.addText(_translate("sportiduinopq","Settings has been loaded successfully"))
            self.addText(_translate("sportiduinopq","Click 'Apply Pwd' on #Settings1 tab"))
        
        except BaseException as err:
            self._process_error(err)

    def SaveSet_clicked(self):    
        self.addText("\n" + _translate("sportiduinopq","Save settings to file /data/settings.json"))  
        
        try:  
            
            settings = self.getSettingsFromUI()
            gain = self.ui.cbAntennaGain.currentIndex()
            
            obj = {}
            obj['settings'] = settings
            obj['gain'] = gain
            obj['pwd1'] = self.ui.sbCurPwd1.value() 
            obj['pwd2'] = self.ui.sbCurPwd2.value()
            obj['pwd3'] = self.ui.sbCurPwd3.value()
            
            file = open(os.path.join('data','settings.json'),'w')
            json.dump(obj, file)
            file.close()
            
            self.addText(_translate("sportiduinopq","Settings has been saved successfully"))
        
        except BaseException as err:
            self._process_error(err)

    def addText(self,text):
        text += '\n'
        logFile = open(os.path.join('log','logFile{:%Y%m%d%H%M%S}.txt'.format(self.initTime)),'a')
        print(text)
        browserText = self.ui.textBrowser.toPlainText()
        browserText = browserText + text
        self.ui.textBrowser.setPlainText(browserText)
        # Scroll down
        self.ui.textBrowser.verticalScrollBar().setValue(self.ui.textBrowser.verticalScrollBar().maximum())
        logFile.write(text)
        logFile.close()

    def SelectPrinter_clicked(self):
        dialog = QtPrintSupport.QPrintDialog(self.printer)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.printer = dialog.printer()
            self.ui.printerName.setText(self.printer.printerName())
            
    def Print_clicked(self):
        try:
            self.printer.setFullPage(True)
            self.printer.setPageMargins(3,3,3,3,QPrinter.Millimeter)
            page_size = QSizeF()
            page_size.setHeight(self.printer.height())
            page_size.setWidth(self.printer.width())
            self.ui.textBrowser.document().setPageSize(page_size)
            self.ui.textBrowser.document().setDocumentMargin(0.0)
            self.ui.textBrowser.document().print_(self.printer)
        except BaseException as err:
            self._process_error(err)
        
    def SerialRead_clicked(self):
        try:
        
            self.addText("\n" + _translate("sportiduinopq", "Reads info about a base station by UART"))
            
            port = self.ui.cbUartPort.currentText()
            
            bs = BaseStation()
            bs.readInfoBySerial(port, self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())

            self.showBaseStationInfo(bs)
        
        except BaseException as err:
            self._process_error(err)
        

    def SerialWrite_clicked(self):
        
        try:
            
            self.addText("\n" + _translate("sportiduinopq","Writes settings and password to a base station by UART"))
            port = self.ui.cbUartPort.currentText()
            
            oldPwd1 = self.ui.sbOldPwd1.value()
            oldPwd2 = self.ui.sbOldPwd2.value()
            oldPwd3 = self.ui.sbOldPwd3.value()
            
            newPwd1 = self.ui.sbNewPwd1.value()
            newPwd2 = self.ui.sbNewPwd2.value()
            newPwd3 = self.ui.sbNewPwd3.value()
            
            num = self.ui.sbStationNumByUart.value()
            sets = self.getSettingsFromUI()
            wakeup = self.ui.dtCompetion.dateTime().toUTC().toPyDateTime()
            gain = (self.ui.cbAntennaGain.currentIndex() + 2) << 4
            
            bs = BaseStation()
            bs.writeSettingsBySerial(port, oldPwd1, oldPwd2, oldPwd3, 
                                     newPwd1, newPwd2, newPwd3, num, sets, wakeup, gain)
            
            self.addText(_translate("sportiduinopq","Settings and password has been written successfully"))
        
        except BaseException as err:
            self._process_error(err)
            
    def ClearText_clicked(self):
        self.ui.textBrowser.setPlainText('')
    
    def showCardData(self, data, card_type):
        if (self.ui.AutoPrint.checkState() != 0):
            self.ClearText_clicked()
                
        text = []
        card_name = Sportiduino.card_name(card_type)
        text.append(card_name)
        
        if data['master_card_flag'] == 0xFF:
            # show master card info
            master_type = int2byte(data['master_card_type'])
            
            if master_type == Sportiduino.MASTER_CARD_GET_INFO:
                text.append(_translate("sportiduinopq","Master card to get info about a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_TIME:
                text.append(_translate("sportiduinopq","Master card to set time of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_NUMBER:
                text.append(_translate("sportiduinopq","Master card to set number of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SLEEP:
                text.append(_translate("sportiduinopq","Master card to sleep a base station"))
            elif master_type == Sportiduino.MASTER_CARD_READ_DUMP:
                text.append(_translate("sportiduinopq","Master card to get punches log of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_PASS:
                text.append(_translate("sportiduinopq","Master card to write password and settings to a base station"))
            else:
                text.append(_translate("sportiduinopq","Uninitialized card"))
            
        else:
            # show participant card info
            card_number = data['card_number']
            init_time = datetime.fromtimestamp(data['init_timestamp'])
            punches = data['punches']
            
            if data['init_timestamp'] != 0 and card_number >= Sportiduino.MIN_CARD_NUM and card_number <= Sportiduino.MAX_CARD_NUM:
                punches_count = 0
        
                text.append(_translate("sportiduinopq","Participant card N{}").format(card_number))
                text.append(_translate("sportiduinopq","Init time {}").format(init_time))
                text.append(_translate("sportiduinopq","Punches (Check point - Time):"))
            
                for punch in punches:
                    punches_count += 1
                    
                    cp = punch[0]
                    cp_time = punch[1]
                            
                    if cp == Sportiduino.START_STATION:
                        cp = _translate("sportiduinopq","Start")
                    if cp == Sportiduino.FINISH_STATION:
                        cp = _translate("sportiduinopq","Finish")
                        
                    text.append("{} - {}".format(cp, cp_time))
                        
                if punches_count == 0:
                    text.append(_translate("sportiduinopq", "No punches"))
                else:
                    text.append(_translate("sportiduinopq", "Total punches {}").format(punches_count))
            else:
               text.append(_translate("sportiduinopq","Uninitialized card"))
   
        self.addText('\n'.join(text))
        
        if (self.ui.AutoPrint.checkState() != 0):
            self.Print_clicked()
            
    def saveCardDataJson(self,data):
        
        if data['master_card_flag'] == 255:
            return
        
        card_number = data['card_number']
        
        if card_number < Sportiduino.MIN_CARD_NUM or card_number > Sportiduino.MAX_CARD_NUM:
            return
        
        if('start' in data):
            data['start'] = int(data['start'].timestamp())
            
        if('finish' in data):
            data['finish'] = int(data['finish'].timestamp())

        if ('punches' in data):
            punches = data['punches']
            bufferPunch = []
            for punch in punches:
                kort = (punch[0], int(punch[1].timestamp()))
                bufferPunch.append(kort)
            data['punches']=bufferPunch
            
        del data['master_card_flag']
        del data['master_card_type']
        del data['init_timestamp']
        del data['page6']
        del data['page7']

        self.readData.append(data)
            
        dataFile = open(os.path.join('data','readData{:%Y%m%d%H%M%S}.json'.format(self.initTime)),'w')
        json.dump(self.readData, dataFile)
        dataFile.close()
        
    def showSettings(self, settings):
        set1 = settings & 0x3
        self.ui.WorkTime.setCurrentIndex(set1)
        
        set2 = (settings & 0x4) >> 0x2
        self.ui.StartFinish.setCurrentIndex(set2)
        
        set3 = (settings & 0x8) >> 0x3
        self.ui.CheckInitTime.setCurrentIndex(set3)
        
        set4 = (settings & 0x10) >> 0x4
        self.ui.AutoDel.setCurrentIndex(set4)
        
        set5 = (settings & 0x20) >> 0x5
        self.ui.cbFastMark.setCurrentIndex(set5)
        
    def getSettingsFromUI(self):
        workTime = self.ui.WorkTime.currentIndex()
        stFi = self.ui.StartFinish.currentIndex()
        checkIT = self.ui.CheckInitTime.currentIndex()
        autoDel = self.ui.AutoDel.currentIndex()
        fastMark = self.ui.cbFastMark.currentIndex()

        if (workTime == 0):
            a = 0b00
        elif (workTime == 1):
            a = 0b01
        elif (workTime == 2):
            a = 0b10
        elif (workTime == 3):
            a = 0b11

        if (stFi == 0):
            b = 0b0
        elif (stFi == 1):
            b = 0b1

        if (checkIT == 0):
            c = 0b0
        elif (checkIT == 1):
            c = 0b1

        if (autoDel == 0):
            d = 0b0
        elif (autoDel == 1):
            d = 0b1
            
        if (fastMark == 0):
            e = 0b0
        elif (fastMark == 1):
            e = 0b1

        setSt = a + ( b<<2) + (c<<3) + (d<<4) + (e<<5)
        
        return setSt
    
    def showBaseStationInfo(self, bs):
        self.addText(_translate("sportiduinopq","Version: {}.{}.{}").format(bs.hwVers(), bs.fwMajorVers(), bs.fwMinorVers()))
        
        text = _translate("sportiduinopq","Station N: {} ").format(bs.num)

        if(bs.num == BaseStation.START_STATION_NUM):
            text += _translate("sportiduinopq","(Start)")
        elif (bs.num == BaseStation.FINISH_STATION_NUM):
            text += _translate("sportiduinopq","(Finish)")
        elif (bs.num == BaseStation.CHECK_STATION_NUM):
            text += _translate("sportiduinopq","(Check)")
        elif (bs.num == BaseStation.CLEAR_STATION_NUM):
            text += _translate("sportiduinopq","(Clear)")
            
        self.addText(text)
        
        text = _translate("sportiduinopq","Settings: {}").format(bin(bs.settings).lstrip('-0b').zfill(8))
        self.addText(text)
        
        if(bs.batteryOk):
            self.addText(_translate("sportiduinopq","Battery: OK"))
        else:
            self.addText(_translate("sportiduinopq","Battery: Low"))
            
        if(bs.mode == BaseStation.MODE_ACTIVE):
            self.addText(_translate("sportiduinopq","Mode: Active"))
        elif(bs.mode == BaseStation.MODE_WAIT):
            self.addText(_translate("sportiduinopq","Mode: Wait"))
        elif(bs.mode == BaseStation.MODE_SLEEP):
            self.addText(_translate("sportiduinopq","Mode: Sleep"))
            
        text = _translate("sportiduinopq", "Clock: {}").format(datetime.fromtimestamp(bs.timestamp))
        self.addText(text)
        text = _translate("sportiduinopq", "Alarm: {}").format(datetime.fromtimestamp(bs.wakeup))
        self.addText(text)

        idx = (bs.antennaGain >> 4) - 2;
        self.ui.cbAntennaGain.setCurrentIndex(idx)
        self.addText(_translate("sportiduinopq","Antenna Gain: {}").format(self.ui.cbAntennaGain.currentText()))
        
        # apply settings to ui    
        self.ui.sbStationNum.setValue(bs.num)
        self.ui.sbStationNumByUart.setValue(bs.num)
        self.ui.dtCompetion.setDateTime(datetime.fromtimestamp(bs.wakeup))            
        self.showSettings(bs.settings)
        
        self.addText(_translate("sportiduinopq","Settings displayed by UI has been chaged to the base station settings"))
    
    def _process_error(self, err):
        self.addText(_translate("sportiduinopq","Error: {}").format(err))
        
    def _check_connection(self):
        self.addText("")
        if not self.connected:
            self.addText(_translate("sportiduinopq","Master station is not connected"))
            return False
        return True
    
    def _master_card_ok(self):
        self.addText(_translate("sportiduinopq","The master card has been written successfully"))
        
if __name__ == '__main__':
    
    try:
        os.mkdir('log')
        os.mkdir('data')
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)
    
    translator = QTranslator()
    translator.load("sportiduinopq_" + QLocale.system().name(), "./translation")
    if not app.installTranslator(translator):
        print("Can not install translation!")

    window = App()
    window.show()
    app.exec_()
