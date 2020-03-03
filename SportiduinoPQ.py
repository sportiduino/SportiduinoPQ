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
from PyQt5.QtCore import QSizeF, QSettings
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import QTranslator
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import QCoreApplication
from six import int2byte

_translate = QCoreApplication.translate

class SportiduinoPqMainWindow(QtWidgets.QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("SportiduinoPQ v0.7.99")
        
        self.readData = []
        self.dumpData = []
        self.connected = False
        self.printer = QPrinter()
        self.ui.printerName.setText(self.printer.printerName())

        self._init_time = datetime.now()
        self._logger = self.Logger()
        self.log('{:%Y-%m-%d %H:%M:%S}'.format(self._init_time))
        
        availablePorts = []
        if platform.system() == 'Linux':
            availablePorts = [os.path.join('/dev', f) for f in os.listdir('/dev') if
                              re.match('ttyUSB.+', f)]
            availablePorts.sort()
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
        self.ui.SelectPrinter.clicked.connect(self.SelectPrinter_clicked)
        self.ui.Print.clicked.connect(self.Print_clicked)
        self.ui.btnApplyPwd.clicked.connect(self.ApplyPwd_clicked)
        self.ui.btnCreateInfoCard.clicked.connect(self.CreateInfo_clicked)
        self.ui.btnReadInfo.clicked.connect(self.ReadInfo_clicked)
        self.ui.btnUartRead.clicked.connect(self.SerialRead_clicked)
        self.ui.btnUartWrite.clicked.connect(self.SerialWrite_clicked)
        self.ui.btnClearText.clicked.connect(self.ClearText_clicked)
        self.ui.btnMsConfigRead.clicked.connect(self.read_ms_config)
        self.ui.btnMsConfigWrite.clicked.connect(self.write_ms_config)

        self.config = config
        geometry = self.config.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)
 
        bs_config = BaseStation.Config()
        for key, default_value in vars(bs_config).items():
            value_type = type(default_value)
            if isinstance(default_value, list):
                value_type = type(default_value[0])
            setattr(bs_config, key, self.config.value('settings/'+key, default_value, type=value_type))
        self._apply_settings(bs_config, datetime.now())

        self.ui.sbCurPwd1.setValue(bs_config.password[0])
        self.ui.sbCurPwd2.setValue(bs_config.password[1])
        self.ui.sbCurPwd3.setValue(bs_config.password[2])

        self.ui.sbNewPwd1.setValue(bs_config.password[0])
        self.ui.sbNewPwd2.setValue(bs_config.password[1])
        self.ui.sbNewPwd3.setValue(bs_config.password[2])

        #dumpFile = open(os.path.join('data','dumpData{:%Y%m%d%H%M%S}.json'.format(self._init_time)),'w')


    def closeEvent(self, event):
        self.config.setValue('geometry', self.saveGeometry())

        bs_config = self._get_config_from_ui()
        for key, value in vars(bs_config).items():
            self.config.setValue('settings/'+key, value)

        event.accept()


    def Connect_clicked(self):

        self.log("")
        
        if self.connected:
            self.sportiduino.disconnect()
            text = self.tr("Master station is disconnected")
            self.log(text)
            self.connected = False
            self.ui.Connect.setText(_translate("MainWindow", "Connect"))
        else:
            port = self.ui.choiseCom.currentText()
            try:
                if (port == QCoreApplication.translate("MainWindow", "auto")):
                    self.sportiduino = Sportiduino(debug=True)
                else:
                    self.sportiduino = Sportiduino(port,debug=True)

                curPass = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
                self.sportiduino.apply_pwd(curPass)

                #self.sportiduino.beep_ok()
                self.connected = True
                text = self.tr("Master station {} on port {} is connected").format(self.sportiduino.version, self.sportiduino.port)
                self.log(text)
                self.ui.Connect.setText(_translate("MainWindow", "Disconn."))

                self.read_ms_config()
                
            except BaseException as err:
                self._process_error(err)
                self.connected = False

    def ReadCard_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log(self.tr("Read a card"))
            
            card_type = self.sportiduino.read_card_type()
            raw_data = self.sportiduino.read_card_raw()
            
            data = Sportiduino.raw_data_to_card_data(raw_data)
            
            self._show_card_data(data, card_type)
            self._save_card_data_json(data)
            
        except BaseException as err:
            self._process_error(err)

    def InitCard_clicked(self):
        if not self._check_connection():
            return
        try:
            self.log(self.tr("Initialize the participant card"))

            card_num = 0
            text = self.ui.cardLine.text()
            if(text.isdigit()):
                card_num = int(text)

            if (card_num < Sportiduino.MIN_CARD_NUM or card_num > Sportiduino.MAX_CARD_NUM):
                raise Exception(self.tr("Incorrect card number"))

            code, data = self.sportiduino.init_card(card_num)
            if code == Sportiduino.RESP_OK :
                self.log(self.tr("The participant card N{} ({}) has been initialized successfully")
                    .format(card_num, Sportiduino.card_name(data[0])))
 
            if self.ui.AutoIncriment.isChecked():
                self.ui.cardLine.setText(card_num + 1)

        except BaseException as err:
            self._process_error(err)
            
    def SetNum_clicked(self):
        if not self._check_connection():
            return
        
        try:
            
            self.log(self.tr("Write the master card to set number of a base station"))
            num = self.ui.sbStationNum.value()
        
            if num < 1 or num > 255:
                raise Exception(self.tr("Not correct station number"))
            
            self.sportiduino.init_cp_number_card(num)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
                            
    def SetTime_clicked(self):
        if self._check_connection() == False :
            return

        try:
            
            self.log(self.tr("Write the master card to set clock of a base station. Put the card on a base station after third signal"))
            self.sportiduino.init_time_card(datetime.utcnow() + timedelta(seconds=3))
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def SetStart_clicked(self):
        if self._check_connection() == False :
            return
        
        try:
            
            self.log(self.tr("Write the master card to set a base station as the start station"))
            self.sportiduino.init_cp_number_card(Sportiduino.START_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.START_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def SetFinish_clicked(self):
        if not self._check_connection():
            return
        
        try:
            
            self.log(self.tr("Write the master card to set a base station as the finish station"))
            self.sportiduino.init_cp_number_card(Sportiduino.FINISH_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.FINISH_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def CheckSt_clicked(self):
        if not self._check_connection():
            return
        
        try:
            
            self.log(self.tr("Write the master card to set a base station as the check station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CHECK_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CHECK_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def ClearSt_clicked(self):
        if not self._check_connection():
            return
        
        try:
            
            self.log(self.tr("Write the master card to set a base station as the clear station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CLEAR_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CLEAR_STATION)
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def LogCard_clicked(self):
        if not self._check_connection():
            return
        
        try:
        
            self.log(self.tr("Write the master card to get log of a base station"))
            self.sportiduino.init_backupreader()
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
                
    def ReadLog_clicked(self):
        if not self._check_connection():
            return

        text = ""
        
        try:
            self.log(self.tr("Read the card contained log of a base station"))
            
            data = self.sportiduino.read_backup()
            
            if data is None:
                raise BaseException(self.tr("No log data available"))
            
            text = self.tr("Station N: {} ").format(data['cp']) + "\n"

            cards = data['cards']
            
            if len(cards) > 0:
                text += self.tr("Total punches {}").format(len(cards)) + "\n"
                text += self.tr("Cards:") + "\n"
                if isinstance(cards[0], int):
                    text += ', '.join(cards)
                else:
                    for pair in cards:
                        text += "{:>4} {}".format(*pair) + "\n"

                
            self.log(text)
                
            #self.dumpData.append(data)
            #dumpFile = open(os.path.join('data','dumpData{:%Y%m%d%H%M%S}.json'.format(self._init_time)),'w')
            #json.dump(self.dumpData, dumpFile)
            #dumpFile.close()

        except BaseException as err:
            self._process_error(err)

    def SleepCard_clicked(self):
        if not self._check_connection():
            return
        
        try:
            
            self.log(self.tr("Write the master card to sleep a base station"))
            self.sportiduino.init_sleepcard(self.ui.dtCompetion.dateTime().toUTC())
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)

    def PassCard_clicked(self):
        if not self._check_connection():
            return
        
        try:

            self.log(self.tr("Write the config master card"))

            
            bs_config = self._get_config_from_ui()
            bs_config.num = 0 # don't change station number by this master card
            self.sportiduino.init_config_card(bs_config.pack())
                
            self.ui.sbCurPwd3.setValue(self.ui.sbNewPwd3.value())
            self.ui.sbCurPwd2.setValue(self.ui.sbNewPwd2.value())
            self.ui.sbCurPwd1.setValue(self.ui.sbNewPwd1.value())
            
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
            
    def ApplyPwd_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log(self.tr("Apply the current password"))
            
            curPass = tuple(self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
            self.sportiduino.apply_pwd(curPass)
            self.log(self.tr("The password has been applied successfully"))

        except BaseException as err:
            self._process_error(err)
            
    def CreateInfo_clicked(self):
        if not self._check_connection():
            return
        
        try:
           
            self.log(self.tr("Write the master card to get a base station state"))
            self.sportiduino.init_state_card()
            self._master_card_ok()
            
        except BaseException as err:
            self._process_error(err)
        
    def ReadInfo_clicked(self):
        if not self._check_connection():
            return
        
        try:
            self.log(self.tr("Read the card contained a base station state"))
            bs_state = self.sportiduino.read_state_card()
            self._show_base_station_state(bs_state)
            
        except BaseException as err:
            self._process_error(err)
            
    def log(self, text):
        text += '\n'
        print(text)
        browserText = self.ui.textBrowser.toPlainText()
        browserText = browserText + text
        self.ui.textBrowser.setPlainText(browserText)
        # Scroll down
        self.ui.textBrowser.verticalScrollBar().setValue(self.ui.textBrowser.verticalScrollBar().maximum())

        self._logger(text)

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
            self.ui.textBrowser.document().print(self.printer)
        except BaseException as err:
            self._process_error(err)
        
    def SerialRead_clicked(self):
        try:
            self.log("\n" + self.tr( "Reads info about a base station by UART"))
            
            port = self.ui.cbUartPort.currentText()
            password = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())

            bs_state = BaseStation.read_info_by_serial(port, password)

            self._show_base_station_state(bs_state)
        
        except BaseException as err:
            self._process_error(err)
        

    def SerialWrite_clicked(self):
        try:
            self.log("\n" + self.tr("Writes settings and password to a base station by UART"))
            port = self.ui.cbUartPort.currentText()
            
            bs_config = self._get_config_from_ui()
            bs_config.num = self.ui.sbStationNumByUart.value()
            wakeuptime = self.ui.dtCompetion.dateTime().toUTC().toPyDateTime()

            password = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
            BaseStation.write_settings_by_serial(port, password, bs_config, wakeuptime)

            self.log(self.tr("Settings and password has been written successfully"))
        
        except BaseException as err:
            self._process_error(err)

            
    def ClearText_clicked(self):
        self.ui.textBrowser.setPlainText('')


    def read_ms_config(self):
        if not self._check_connection():
            return

        try:
            ms_config = self.sportiduino.read_settings()
            if ms_config.antenna_gain is not None:
                self.ui.cbMsAntennaGain.setCurrentIndex(ms_config.antenna_gain - 2)
        except BaseException as err:
            self._process_error(err)


    def write_ms_config(self):
        if not self._check_connection():
            return

        try:
            self.sportiduino.write_settings(self.ui.cbMsAntennaGain.currentIndex() + 2)
        except BaseException as err:
            self._process_error(err)


    def _show_card_data(self, data, card_type):
        if self.ui.AutoPrint.isChecked():
            self.ClearText_clicked()
                
        text = []
        card_name = Sportiduino.card_name(card_type)
        text.append(card_name)
        
        if data['master_card_flag'] == 0xFF:
            # show master card info
            master_type = int2byte(data['master_card_type'])
            
            if master_type == Sportiduino.MASTER_CARD_GET_INFO:
                text.append(self.tr("Master card to get info about a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_TIME:
                text.append(self.tr("Master card to set time of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_NUMBER:
                text.append(self.tr("Master card to set number of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SLEEP:
                text.append(self.tr("Master card to sleep a base station"))
            elif master_type == Sportiduino.MASTER_CARD_READ_DUMP:
                text.append(self.tr("Master card to get punches log of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_PASS:
                text.append(self.tr("Master card to write password and settings to a base station"))
            else:
                text.append(self.tr("Uninitialized card"))
            
        else:
            # show participant card info
            card_number = data['card_number']
            init_time = datetime.fromtimestamp(data['init_timestamp'])
            punches = data['punches']
            
            if data['init_timestamp'] != 0 and card_number >= Sportiduino.MIN_CARD_NUM and card_number <= Sportiduino.MAX_CARD_NUM:
                punches_count = 0
        
                text.append(self.tr("Participant card N{}").format(card_number))
                text.append(self.tr("Init time {}").format(init_time))
                text.append(self.tr("Punches (Check point - Time):"))
            
                for punch in punches:
                    punches_count += 1
                    
                    cp = punch[0]
                    cp_time = punch[1]
                            
                    if cp == Sportiduino.START_STATION:
                        cp = self.tr("Start")
                    if cp == Sportiduino.FINISH_STATION:
                        cp = self.tr("Finish")
                        
                    text.append("{} - {}".format(cp, cp_time))
                        
                if punches_count == 0:
                    text.append(self.tr( "No punches"))
                else:
                    text.append(self.tr( "Total punches {}").format(punches_count))
            else:
               text.append(self.tr("Uninitialized card"))
   
        self.log('\n'.join(text))
        
        if self.ui.AutoPrint.isChecked():
            self.Print_clicked()
            
    def _save_card_data_json(self,data):
        
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
            
        dataFile = open(os.path.join('data','readData{:%Y%m%d%H%M%S}.json'.format(self._init_time)),'w')
        json.dump(self.readData, dataFile)
        dataFile.close()
        
    def _apply_settings(self, bs_config, wakeuptime):
        self.ui.sbStationNum.setValue(bs_config.num)
        self.ui.sbStationNumByUart.setValue(bs_config.num)
        self.ui.dtCompetion.setDateTime(wakeuptime)            

        self.ui.cbActiveTime.setCurrentIndex(bs_config.active_mode_duration)

        self.ui.cbStartFinish.setChecked(bs_config.check_start_finish)
        self.ui.cbCheckInitTime.setChecked(bs_config.check_card_init_time)
        self.ui.cbFastPunch.setChecked(bs_config.fast_punch)

        self.ui.cbAntennaGain.setCurrentIndex(bs_config.antenna_gain - 2)
        
    def _get_config_from_ui(self):
        bs_config = BaseStation.Config()
        bs_config.active_mode_duration = self.ui.cbActiveTime.currentIndex()
        bs_config.check_start_finish = self.ui.cbStartFinish.isChecked()
        bs_config.check_card_init_time = self.ui.cbCheckInitTime.isChecked()
        bs_config.fast_punch = self.ui.cbFastPunch.isChecked()
        bs_config.antenna_gain = self.ui.cbAntennaGain.currentIndex() + 2
        bs_config.password = [self.ui.sbNewPwd1.value(), self.ui.sbNewPwd2.value(), self.ui.sbNewPwd3.value()]

        return bs_config
    
    def _show_base_station_state(self, bs_state):
        self.log(self.tr("Version: {}.{}.{}").format(bs_state.version.major, bs_state.version.minor, bs_state.version.patch))
         
        # apply settings to ui    
        self._apply_settings(bs_state.config, bs_state.wakeuptime)
       
        self.log(self.tr("Settings:"))

        text = self.tr("   Station N: {} ").format(bs_state.config.num)
        if(bs_state.config.num == Sportiduino.START_STATION):
            text += self.tr("(Start)")
        elif (bs_state.config.num == Sportiduino.FINISH_STATION):
            text += self.tr("(Finish)")
        elif (bs_state.config.num == Sportiduino.CHECK_STATION):
            text += self.tr("(Check)")
        elif (bs_state.config.num == Sportiduino.CLEAR_STATION):
            text += self.tr("(Clear)")
        self.log(text)

        self.log(self.tr("   Active time (h): {}").format(self.ui.cbActiveTime.currentText()))
        if bs_state.config.check_start_finish:
            self.log(self.tr("   Check start/finish flag"))
        if bs_state.config.check_card_init_time:
            self.log(self.tr("   Check card init time flag"))
        if bs_state.config.fast_punch:
            self.log(self.tr("   Fast punch flag"))
        self.log(self.tr("   Antenna Gain: {}").format(self.ui.cbAntennaGain.currentText()))
        
        voltageText = ''
        if bs_state.battery.voltage is not None:
            voltageText = self.tr( " ({:.2f} V)").format(bs_state.battery.voltage)

        if(bs_state.battery.isOk):
            self.log(self.tr("Battery: OK") + voltageText)
        else:
            self.log(self.tr("Battery: Low") + voltageText)
            
        if(bs_state.mode == BaseStation.MODE_ACTIVE):
            self.log(self.tr("Mode: Active"))
        elif(bs_state.mode == BaseStation.MODE_WAIT):
            self.log(self.tr("Mode: Wait"))
        elif(bs_state.mode == BaseStation.MODE_SLEEP):
            self.log(self.tr("Mode: Sleep"))
            
        text = self.tr( "Clock: {}").format(bs_state.timestamp)
        self.log(text)
        text = self.tr( "Alarm: {}").format(bs_state.wakeuptime)
        self.log(text)

        self.log(self.tr("Settings displayed by UI has been chaged to the base station settings"))
    
    def _process_error(self, err):
        self.log(self.tr("Error: {}").format(err))
        
    def _check_connection(self):
        self.log("")
        if not self.connected:
            self.log(self.tr("Master station is not connected"))
            return False
        return True
    
    def _master_card_ok(self):
        self.log(self.tr("The master card has been written successfully"))

    class Logger(object):
        def __init__(self):
            self._log_file = open(os.path.join('log','log{:%Y%m%d}.txt'.format(datetime.now())),'a')

        def __call__(self, text):
            self._log_file.write(text)
        
        def __del__(self):
            print("Close log file")
            self._log_file.close();


if __name__ == '__main__':
    
    os.makedirs('log', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    app = QtWidgets.QApplication(sys.argv)
    
    config = QSettings(os.path.join('data', 'config.ini'), QSettings.IniFormat)
    lang = config.value('language', QLocale.system().name())
    config.setValue('language', lang)

    translator = QTranslator()
    if lang != 'en':
        translator.load("sportiduinopq_" + lang, "./translation")
        if not app.installTranslator(translator):
            print('Can not install translation for language "{}"!'.format(lang))

    main_window = SportiduinoPqMainWindow(config)
    main_window.show()
    app.exec_()
