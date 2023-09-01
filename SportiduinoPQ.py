#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
#    Copyright 2018 Alexander Volikov
#    Copyright 2018-2019 Anton Sysoev
#    Copyright 2019-2022 Semyon Yakimov <sdyakimov@gmail.com>
#
#    This file is part of SportiduinoPQ
#
#    SportiduinoPQ is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    SportiduinoPQ is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with SportiduinoPQ.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os.path
import platform
import re
import time
import json
import csv
import design
import functools

from sportiduino import Sportiduino, SportiduinoTimeout
from basestation import BaseStation
from datetime import datetime, timedelta, timezone
from PyQt5 import QtCore, QtWidgets, QtPrintSupport
from PyQt5.QtCore import QSizeF, QSettings
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QTranslator
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QTimeZone
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QStyle
from six import int2byte

_translate = QCoreApplication.translate

sportiduinopq_version_string = "v0.12.0"


class SportiduinoPqMainWindow(QtWidgets.QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("SportiduinoPQ {}".format(sportiduinopq_version_string))

        pixmapi = QStyle.SP_BrowserReload
        icon = self.style().standardIcon(pixmapi)
        self.ui.refreshPortsButton1.setIcon(icon)
        self.ui.refreshPortsButton2.setIcon(icon)

        self.config = config
        geometry = self.config.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)

        self.connected = False

        self.printer = QPrinter()
        printer_name = config.value('printer/name', self.printer.printerName())
        self.printer.setPrinterName(printer_name)
        outputfilename = config.value('printer/outputfilename', self.printer.outputFileName())
        self.printer.setOutputFileName(outputfilename)
        self.ui.printerName.setText(self.printer.printerName())

        init_time = datetime.now()
        self.cards_data_filename = os.path.join('data', 'cards{:%Y%m%d}.csv'.format(init_time))
        if not os.path.exists(self.cards_data_filename):
            with open(self.cards_data_filename, 'w') as cards_data_file:
                cards_data_file.write('No.;Read at;Card no.;;;;;;;;;;;;;;;;Clear time;;;Check time;;;Start time;;;Finish time;No. of punches;;1.CP;;1.Time;2.CP;;2.Time;3.CP;;3.Time\n')
        self.cards_data = []

        self._logger = self.Logger()
        self.log('{:%Y-%m-%d %H:%M:%S}'.format(init_time))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_card)

        self.refreshPorts()

        bs_config = BaseStation.Config()
        for key, default_value in vars(bs_config).items():
            value_type = type(default_value)
            if isinstance(default_value, list):
                value_type = type(default_value[0])
            setattr(bs_config, key, self.config.value('settings/'+key, default_value, type=value_type))
        self._apply_settings(bs_config, datetime.now())

        self.ui.sbCurPwd1.setValue(bs_config.password[0])
        self.ui.sbNewPwd1.setValue(bs_config.password[0])
        self.ui.sbCurPwd2.setValue(bs_config.password[1])
        self.ui.sbNewPwd2.setValue(bs_config.password[1])
        self.ui.sbCurPwd3.setValue(bs_config.password[2])
        self.ui.sbNewPwd3.setValue(bs_config.password[2])

        ianaIds = QTimeZone.availableTimeZoneIds()
        all_timezones = sorted({QTimeZone(id).offsetFromUtc(datetime.now()) for id in ianaIds})
        tzlocaloffset = time.localtime().tm_gmtoff
        tzlocalname = None
        for dt in all_timezones:
            tz = timezone(timedelta(seconds=dt))
            tzname = self.getTzName(tz)
            if dt == tzlocaloffset:
                tzlocalname = tzname
            self.ui.cbTimeZone.addItem(tzname, dt)
        if tzlocalname is not None:
            self.ui.cbTimeZone.setCurrentText(tzlocalname)
        else:
            self.ui.cbTimeZone.setCurrentText(timezone(offset=timedelta(0)).tzname(None))

        self.ui.cbAutoRead.stateChanged.connect(self.cbAutoRead_stateChanged)

    def closeEvent(self, event):
        self.config.setValue('geometry', self.saveGeometry())
        self.config.setValue('printer/name', self.printer.printerName())
        self.config.setValue('printer/outputfilename', self.printer.outputFileName())

        bs_config = self._get_config_from_ui()
        for key, value in vars(bs_config).items():
            self.config.setValue('settings/'+key, value)

        event.accept()

    @staticmethod
    def getTzName(tz):
        tzname = tz.tzname(None)
        if tzname == 'UTC':
            tzname = '00:00'
        else:
            tzname = tzname.replace('UTC', '')
        return tzname

    def block_gui(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.setCursor(QtCore.Qt.WaitCursor)
            #self.ui.centralwidget.setEnabled(False)
            #QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
            func(self, *args, **kwargs)
            self.unsetCursor()
            #self.ui.centralwidget.setEnabled(True)
        return wrapper

    def refreshPorts(self):
        availablePorts = []
        if platform.system() == 'Linux':
            availablePorts = [os.path.join('/dev', f) for f in os.listdir('/dev') if
                              re.match('ttyUSB.+|ttyACM.+', f)]
            availablePorts.sort()
        elif platform.system() == 'Windows':
            availablePorts = ['COM' + str(i) for i in range(32)]
        self.ui.cbChoiseCom.clear()
        self.ui.cbChoiseCom.addItem("auto")
        self.ui.cbChoiseCom.addItems(availablePorts)
        self.ui.cbUartPort.clear()
        self.ui.cbUartPort.addItems(availablePorts)

    @QtCore.pyqtSlot()
    @block_gui
    def on_refreshPortsButton1_clicked(self):
        self.refreshPorts()

    @QtCore.pyqtSlot()
    @block_gui
    def on_refreshPortsButton2_clicked(self):
        self.refreshPorts()

    @QtCore.pyqtSlot()
    @block_gui
    def on_connectButton_clicked(self):
        if self.connected:
            self.ui.cbAutoRead.setChecked(False)
            self.sportiduino.disconnect()
            self.log('\n' + self.tr("Master station is disconnected"))
            self.connected = False
            self.ui.connectButton.setText(_translate("MainWindow", "Connect"))
        else:
            port = self.ui.cbChoiseCom.currentText()
            try:
                if (port == QCoreApplication.translate("MainWindow", "auto")):
                    self.sportiduino = Sportiduino(debug=True, translator=QCoreApplication.translate)
                else:
                    self.sportiduino = Sportiduino(port, debug=True)

                curPass = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
                self._apply_pwd(curPass)

                #self.sportiduino.beep_ok()
                self.log('\n' + self.tr("Master station {} on port {} is connected").format(self.sportiduino.version, self.sportiduino.port))
                self.ui.connectButton.setText(_translate("MainWindow", "Disconn."))
                self.connected = True

                self.read_ms_config()

            except Exception as err:
                self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_readCardButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log("\n" + self.tr("Read a card"))

            card_type = self.sportiduino.read_card_type()
            try:
                data = self.sportiduino.read_card(timeout=0.2)
            except SportiduinoTimeout:
                data = Sportiduino.raw_data_to_card_data(self.sportiduino.read_card_raw())
            else:
                self.sportiduino.beep_ok()

            self._show_card_data(data, card_type)
            self._save_card_data_to_csv(data)

        except Exception as err:
            self._process_error(err)

    def poll_card(self):
        if not self._check_connection():
            return

        try:
            if self.sportiduino.poll_card():
                card_number = self.sportiduino.card_data['card_number']
                self.sportiduino.beep_ok()
                if card_number != self.prev_card_number:
                    self._show_card_data(self.sportiduino.card_data)
                    self._save_card_data_to_csv(self.sportiduino.card_data)
                    self.prev_card_number = card_number
            else:
                self.prev_card_number = -1

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_initCardButton_clicked(self):
        if not self._check_connection():
            return
        try:
            self.log("\n" + self.tr("Initialize the participant card"))

            card_num = self.ui.sbCardNumber.value()

            if (card_num < Sportiduino.MIN_CARD_NUM or card_num > Sportiduino.MAX_CARD_NUM):
                raise Exception(self.tr("Incorrect card number"))

            enable_fast_punch = False
            if self.ui.cbFastPunchCard.isChecked():
                enable_fast_punch = True
            code, data = self.sportiduino.init_card(card_num, fast_punch=enable_fast_punch)
            if code == Sportiduino.RESP_OK:
                self.log(self.tr("The participant card No {} ({}) has been initialized successfully")
                        .format(card_num, Sportiduino.card_name(data[0])))
                if self.ui.cbAutoIncriment.isChecked():
                    self.ui.sbCardNumber.setValue(card_num + 1)

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_setNumButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set number of a base station"))
            num = self.ui.sbStationNum.value()

            if num < 1 or num > 255:
                raise Exception(self.tr("Not correct station number"))

            self.sportiduino.init_cp_number_card(num)
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_setTimeButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set clock of a base station. Put the card on a base station after third signal"))
            self.sportiduino.init_time_card(datetime.utcnow() + timedelta(seconds=3))
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_setStartButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set a base station as the start station"))
            self.sportiduino.init_cp_number_card(Sportiduino.START_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.START_STATION)
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_setFinishButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set a base station as the finish station"))
            self.sportiduino.init_cp_number_card(Sportiduino.FINISH_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.FINISH_STATION)
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_checkStButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set a base station as the check station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CHECK_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CHECK_STATION)
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_clearStButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to set a base station as the clear station"))
            self.sportiduino.init_cp_number_card(Sportiduino.CLEAR_STATION)
            self.ui.sbStationNum.setValue(Sportiduino.CLEAR_STATION)
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_logCardButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to get log of a base station"))
            self.sportiduino.init_backupreader()
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_readLogButton_clicked(self):
        if not self._check_connection():
            return

        text = ""

        try:
            self.log("\n" + self.tr("Read the card contained log of a base station"))

            data = self.sportiduino.read_backup()

            if data is None:
                raise Exception(self.tr("No log data available"))

            text = self.tr("Station No: {} ").format(data['cp']) + "\n"

            cards = data['cards']

            text += self.tr("Total punches {}").format(len(cards)) + "\n"
            if len(cards) > 0:
                text += self.tr("Cards:") + "\n"
                if isinstance(cards[0], int):
                    text += ', '.join([str(c) for c in cards])
                else:
                    for pair in cards:
                        text += "{:>5} {}".format(*pair) + "\n"
                with open(os.path.join('data', 'station{}_{:%Y%m%d%H%M%S}.csv'.format(data['cp'], datetime.now())), 'w', newline='') as station_backupfile:
                    station_backupfile_writer = csv.writer(station_backupfile, delimiter=',')
                    if isinstance(cards[0], int):
                        station_backupfile_writer.writerow(cards)
                    else:
                        station_backupfile_writer.writerows(cards)

            self.log(text)

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_sleepCardButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to sleep a base station"))
            self.sportiduino.init_sleepcard(self._get_competion_datetime())
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_configCardButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log("\n" + self.tr("Write the config master card"))

            bs_config = self._get_config_from_ui()
            bs_config.num = 0    # don't change station number by this master card
            self.sportiduino.init_config_card(bs_config.pack())

            self.ui.sbCurPwd3.setValue(self.ui.sbNewPwd3.value())
            self.ui.sbCurPwd2.setValue(self.ui.sbNewPwd2.value())
            self.ui.sbCurPwd1.setValue(self.ui.sbNewPwd1.value())

            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_passwordCardButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log("\n" + self.tr("Write the password master card"))

            new_password = (self.ui.sbNewPwd1.value(), self.ui.sbNewPwd2.value(), self.ui.sbNewPwd3.value())
            self.sportiduino.init_password_card(new_password)

            self.ui.sbCurPwd3.setValue(self.ui.sbNewPwd3.value())
            self.ui.sbCurPwd2.setValue(self.ui.sbNewPwd2.value())
            self.ui.sbCurPwd1.setValue(self.ui.sbNewPwd1.value())

            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_applyPwdButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log("\n" + self.tr("Apply the current password"))

            curPass = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
            self._apply_pwd(curPass)
            self.log(self.tr("The password has been applied successfully"))

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_createInfoCardButton_clicked(self):
        if not self._check_connection():
            return

        try:

            self.log("\n" + self.tr("Write the master card to get a base station state"))
            self.sportiduino.init_state_card()
            self._master_card_ok()

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_readInfoButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.log("\n" + self.tr("Read the card contained a base station state"))

            self._read_state_card()

        except Exception as err:
            self._process_error(err)

    def log(self, text):
        print(text)
        self.ui.logText.append(text)
        # Scroll down
        self.ui.logText.verticalScrollBar().setValue(self.ui.logText.verticalScrollBar().maximum())

        self._logger(text)

    @QtCore.pyqtSlot()
    def on_selectPrinterButton_clicked(self):
        dialog = QtPrintSupport.QPrintDialog(self.printer)
        dialog.setWindowTitle(self.tr("Printer Selection"))
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.printer = dialog.printer()
            self.ui.printerName.setText(self.printer.printerName())

    @QtCore.pyqtSlot()
    def on_printButton_clicked(self):
        try:
            #self.printer.setPageMargins(3,3,3,3,QPrinter.Millimeter)

            page_size = QSizeF()
            page_size.setHeight(self.printer.height())
            page_size.setWidth(self.printer.width())

            text_document = self.ui.logText.document().clone()
            text_document.setPageSize(page_size)
            text_document.setDocumentMargin(0.0)
            text_document.print(self.printer)
        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_serialReadButton_clicked(self):
        try:
            self.log("\n" + self.tr("Reads info about a base station by UART"))

            port = self.ui.cbUartPort.currentText()
            password = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())

            bs_state = BaseStation.read_info_by_serial(port, password)

            self._show_base_station_state(bs_state)

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_serialWriteButton_clicked(self):
        try:
            self.log("\n" + self.tr("Writes settings and password to a base station by UART"))
            port = self.ui.cbUartPort.currentText()

            bs_config = self._get_config_from_ui()
            bs_config.num = self.ui.sbStationNumByUart.value()
            wakeuptime = self._get_competion_datetime().toPyDateTime()

            password = (self.ui.sbCurPwd1.value(), self.ui.sbCurPwd2.value(), self.ui.sbCurPwd3.value())
            BaseStation.write_settings_by_serial(port, password, bs_config, wakeuptime)

            self.log(self.tr("Settings and password has been written successfully"))

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    @block_gui
    def on_eraseLogButton_clicked(self):
        try:
            if QMessageBox.question(self, self.tr('Erase log'), self.tr('Are you sure you want to erase the base station log permanently?')) != QMessageBox.Yes:
                return
            self.log("\n" + self.tr("Erase log of a base station by UART"))
            port = self.ui.cbUartPort.currentText()
            BaseStation.erase_log_by_serial(port)
            self.log(self.tr("Log has been erased successfully"))

        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    def on_clearTextButton_clicked(self):
        self.ui.logText.clear()

    def read_ms_config(self):
        ms_config = self.sportiduino.read_settings()
        if ms_config.antenna_gain is not None:
            self.ui.cbMsAntennaGain.setCurrentIndex(ms_config.antenna_gain - 2)
        if ms_config.timezone is not None:
            tz = timezone(ms_config.timezone)
            self.ui.cbTimeZone.setCurrentText(self.getTzName(tz))

    @QtCore.pyqtSlot()
    @block_gui
    def on_msConfigReadButton_clicked(self):
        if not self._check_connection():
            return

        try:
            self.read_ms_config()
            self.sportiduino.beep_ok()
        except Exception as err:
            self._process_error(err)

    @QtCore.pyqtSlot()
    def cbAutoRead_stateChanged(self):
        if self.ui.cbAutoRead.isChecked():
            if not self._check_connection():
                return
            self.prev_card_number = -1
            self.log("\n" + self.tr("Start polling cards"))
            self.timer.start(1000)
        else:
            self.log("\n" + self.tr("Stop polling cards"))
            self.timer.stop()
        self.ui.readCardButton.setEnabled(not self.ui.cbAutoRead.isChecked())
        self.ui.initCardButton.setEnabled(not self.ui.cbAutoRead.isChecked())
        self.ui.tab_2.setEnabled(not self.ui.cbAutoRead.isChecked())
        self.ui.tab_3.setEnabled(not self.ui.cbAutoRead.isChecked())
        self.ui.tab_4.setEnabled(not self.ui.cbAutoRead.isChecked())

    @QtCore.pyqtSlot()
    @block_gui
    def on_msConfigWriteButton_clicked(self):
        if not self._check_connection():
            return

        try:
            tz = timedelta(seconds=self.ui.cbTimeZone.currentData())
            self.sportiduino.write_settings(self.ui.cbMsAntennaGain.currentIndex() + 2, tz)
        except Exception as err:
            self._process_error(err)


    def _show_card_data(self, data, card_type=None):
        if self.ui.cbAutoPrint.isChecked():
            self.on_clearTextButton_clicked()

        text = []
        if card_type is not None:
            card_name = Sportiduino.card_name(card_type)
            text.append(card_name)

        if 'master_card_flag' in data:
            # show master card info
            master_type = int2byte(data['master_card_type'])

            if master_type == Sportiduino.MASTER_CARD_GET_STATE:
                text.append(self.tr("Master card to get info about a base station"))
                self.log('\n'.join(text))
                text = []
                self._read_state_card(data['rawdata'])
            elif master_type == Sportiduino.MASTER_CARD_SET_TIME:
                text.append(self.tr("Master card to set time of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_NUMBER:
                text.append(self.tr("Master card to set number of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SLEEP:
                text.append(self.tr("Master card to sleep a base station"))
            elif master_type == Sportiduino.MASTER_CARD_READ_BACKUP:
                text.append(self.tr("Master card to get punches log of a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_CONFIG:
                text.append(self.tr("Master card to write settings to a base station"))
            elif master_type == Sportiduino.MASTER_CARD_SET_PASSWORD:
                text.append(self.tr("Master card to write password to a base station"))
            else:
                text.append(self.tr("Uninitialized card"))
            self.log('\n'.join(text))
            return

        # show participant card info
        card_number = data['card_number']
        init_time = -1
        if 'init_timestamp' in data:
            init_time = (data['init_timestamp'])

        if init_time != 0 and card_number >= Sportiduino.MIN_CARD_NUM and card_number <= Sportiduino.MAX_CARD_NUM:
            punches_count = 0

            text.append(self.tr("Participant card No {}").format(card_number))
            if init_time > 0:
                text.append(self.tr("Init time {}").format(datetime.fromtimestamp(init_time)))

            text.append(self.tr("Punches (Check point - Time):"))
            punch_str = "{:>5} - {}"
            if 'start' in data:
                text.append(punch_str.format(self.tr("Start"), data["start"]))

            punches = data['punches']
            for punch in punches:
                punches_count += 1

                cp = punch[0]
                cp_time = punch[1]

                text.append(punch_str.format(cp, cp_time))

            if 'finish' in data:
                text.append(punch_str.format(self.tr("Finish"), data["finish"]))

            if punches_count == 0:
                text.append(self.tr("No punches"))
            else:
                text.append(self.tr("Total punches {}").format(punches_count))
        else:
            text.append(self.tr("Uninitialized card"))

        self.log('\n'.join(text))

        if self.ui.cbAutoPrint.isChecked():
            self.on_printButton_clicked()

    def _save_card_data_to_file(self, data):
        if 'master_card_flag' in data:
            return

        card_number = data['card_number']

        if card_number < Sportiduino.MIN_CARD_NUM or card_number > Sportiduino.MAX_CARD_NUM:
            return

        if 'start' in data:
            data['start'] = int(data['start'].timestamp())

        if 'finish' in data:
            data['finish'] = int(data['finish'].timestamp())

        if 'punches' in data:
            punches = data['punches']
            bufferPunch = []
            for punch in punches:
                kort = (punch[0], int(punch[1].timestamp()))
                bufferPunch.append(kort)
            data['punches'] = bufferPunch

        if 'master_card_flag' in data:
            del data['master_card_flag']
        if 'master_card_type' in data:
            del data['master_card_type']
        if 'init_timestamp' in data:
            del data['init_timestamp']
        del data['page6']
        del data['page7']

        self.cards_data.append(data)

        with open(self.cards_data_filename, 'w') as cards_data_file:
            json.dump(self.cards_data, cards_data_file)

    def _save_card_data_to_csv(self, data):
        if 'master_card_flag' in data:
            return

        with open(self.cards_data_filename, 'a') as cards_data_file:
            csv_writer = csv.writer(cards_data_file, delimiter=';')
            row_data = [0, datetime.now().strftime('%H:%M:%S'), data['card_number']]
            for i in range(27):
                row_data.append(None)
            if 'start' in data:
                row_data[24] = data['start'].strftime('%H:%M:%S')
            if 'finish' in data:
                row_data[27] = data['finish'].strftime('%H:%M:%S')
            punches_count = 0
            for punch in data['punches']:
                punches_count += 1
                cp = punch[0]
                cp_time = punch[1]
                row_data.append(cp)
                row_data.append(None)
                row_data.append(cp_time.strftime('%H:%M:%S'))
            row_data[28] = punches_count

            csv_writer.writerow(row_data)

    def _apply_settings(self, bs_config, wakeuptime):
        self.ui.sbStationNum.setValue(bs_config.num)
        self.ui.sbStationNumByUart.setValue(bs_config.num)
        self.ui.dtCompetion.setDateTime(wakeuptime)

        self.ui.cbActiveTime.setCurrentIndex(bs_config.active_mode_duration)

        self.ui.cbStartAsCheck.setChecked(bs_config.start_as_check)
        self.ui.cbCheckInitTime.setChecked(bs_config.check_card_init_time)
        self.ui.cbAutosleep.setChecked(bs_config.autosleep)
        self.ui.cbFastPunchConfig.setChecked(bs_config.enable_fast_punch)

        self.ui.cbAntennaGain.setCurrentIndex(bs_config.antenna_gain - 2)

    def _get_config_from_ui(self):
        bs_config = BaseStation.Config()
        bs_config.active_mode_duration = self.ui.cbActiveTime.currentIndex()
        bs_config.start_as_check = self.ui.cbStartAsCheck.isChecked()
        bs_config.check_card_init_time = self.ui.cbCheckInitTime.isChecked()
        bs_config.autosleep = self.ui.cbAutosleep.isChecked()
        bs_config.enable_fast_punch = self.ui.cbFastPunchConfig.isChecked()
        bs_config.antenna_gain = self.ui.cbAntennaGain.currentIndex() + 2
        bs_config.password = [self.ui.sbNewPwd1.value(), self.ui.sbNewPwd2.value(), self.ui.sbNewPwd3.value()]

        return bs_config

    def _get_competion_datetime(self):
        dt = self.ui.dtCompetion.dateTime().toUTC()
        return dt.addSecs(-dt.time().second())

    def _show_base_station_state(self, bs_state):
        self.log(self.tr("Version: {}").format(bs_state.version))

        # apply settings to ui
        self._apply_settings(bs_state.config, bs_state.wakeuptime if bs_state.wakeuptime > datetime.now() else datetime.now())

        self.log(self.tr("Settings:"))

        text = self.tr("   Station No: {} ").format(bs_state.config.num)
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
        if bs_state.config.start_as_check:
            self.log(self.tr("   Check start/finish flag"))
        if bs_state.config.check_card_init_time:
            self.log(self.tr("   Check card init time flag"))
        if bs_state.config.autosleep:
            self.log(self.tr("   Autosleep flag"))

        if bs_state.config.enable_fast_punch:
            self.log(self.tr("   Fast punch flag"))
        self.log(self.tr("   Antenna Gain: {}").format(self.ui.cbAntennaGain.currentText()))

        voltageText = ''
        if bs_state.battery.voltage is not None:
            voltageText = self.tr(" ({:.2f} V)").format(bs_state.battery.voltage)

        if(bs_state.battery.isOk):
            self.log(self.tr("Battery: OK") + voltageText)
        else:
            self.log("<b>" + self.tr("Battery: Low") + voltageText + "</b>")

        if(bs_state.mode == BaseStation.MODE_ACTIVE):
            self.log(self.tr("Mode: Active"))
        elif(bs_state.mode == BaseStation.MODE_WAIT):
            self.log(self.tr("Mode: Wait"))
        elif(bs_state.mode == BaseStation.MODE_SLEEP):
            self.log(self.tr("Mode: Sleep"))

        text = self.tr("Clock: {}").format(bs_state.timestamp)
        if bs_state.timestamp < (datetime.now() - timedelta(minutes=1)) \
                or bs_state.timestamp > (datetime.now() + timedelta(minutes=1)):
            text = "<b>" + text + "</b>"
        self.log(text)
        text = self.tr("Alarm: {}").format(bs_state.wakeuptime)
        self.log(text)

        self.log(self.tr("Settings displayed by UI has been chaged to the base station settings"))

    def _read_state_card(self, data=None):
        state = self.sportiduino.read_state_card(data)

        bs_state = BaseStation.State()
        bs_state.version = Sportiduino.Version(*state['version'])
        bs_state.config = BaseStation.Config.unpack(state['config'])

        bs_state.battery = BaseStation.Battery(state['battery'])
        bs_state.mode = state['mode']

        bs_state.timestamp = state['timestamp']
        bs_state.wakeuptime = state['wakeuptime']

        self._show_base_station_state(bs_state)

    def _process_error(self, err):
        self.log(self.tr("Error: {}").format(err))

    def _check_connection(self):
        if not self.connected:
            self.log(self.tr("Master station is not connected"))
            return False
        return True

    def _master_card_ok(self):
        self.log(self.tr("The master card has been written successfully"))

    def _apply_pwd(self, curPass):
        self.sportiduino.apply_pwd(curPass)

        self.ui.sbNewPwd1.setValue(curPass[0])
        self.ui.sbNewPwd2.setValue(curPass[1])
        self.ui.sbNewPwd3.setValue(curPass[2])

    class Logger(object):
        def __init__(self):
            self._log_file = open(os.path.join('log', 'log{:%Y%m%d}.txt'.format(datetime.now())), 'a')

        def __call__(self, text):
            self._log_file.write(text + '\n')

        def __del__(self):
            print("Close log file")
            self._log_file.close()


if __name__ == '__main__':
    os.makedirs('log', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    app = QtWidgets.QApplication(sys.argv)

    translation_dir = './translation'
    if hasattr(sys, '_MEIPASS'):
        print('Running in a PyInstaller bundle')
        translation_dir = sys._MEIPASS + '/translation'

    config = QSettings(os.path.join('data', 'config.ini'), QSettings.IniFormat)
    lang = config.value('language', QLocale.system().name())
    config.setValue('language', lang)

    translator = QTranslator()
    if lang != 'en':
        translator.load("sportiduinopq_" + lang, translation_dir)
        if not app.installTranslator(translator):
            print('Can not install translation for language "{}"!'.format(lang))

    main_window = SportiduinoPqMainWindow(config)
    main_window.show()
    app.exec_()
