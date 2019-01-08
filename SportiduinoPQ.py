import sys
sys.path.append('..')
import os.path
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

class App(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.log =''
        self.readData = []
        self.dumpData = []
        self.connected = False
        self.CardNum = '0'
        self.printerName.setText(QPrinter().printerName())
        
        self.initTime = datetime.now()
        self.addText('{:%Y-%m-%d %H:%M:%S}'.format(self.initTime))
        
        dt = QDateTime.currentDateTime()
        tm = QTime(dt.time().hour(), dt.time().minute(), 0)
        dt.setTime(tm)
        self.dtCompetion.setDateTime(dt)

        self.Connec.clicked.connect(self.Connec_clicked)
        self.ReadCard.clicked.connect(self.ReadCard_clicked)
        self.InitCard.clicked.connect(self.InitCard_clicked)
        self.SetTime.clicked.connect(self.SetTime_clicked)
        self.SetNum.clicked.connect(self.SetNum_clicked)
        self.SetStart.clicked.connect(self.SetStart_clicked)
        self.SetFinish.clicked.connect(self.SetFinish_clicked)
        self.CheckSt.clicked.connect(self.CheckSt_clicked)
        self.ClearSt.clicked.connect(self.ClearSt_clicked)
        self.LogCard.clicked.connect(self.LogCard_clicked)
        self.ReadLog.clicked.connect(self.ReadLog_clicked)
        self.SleepCard.clicked.connect(self.SleepCard_clicked)
        self.PassCard.clicked.connect(self.PassCard_clicked)
        self.SaveSet.clicked.connect(self.SaveSet_clicked)
        self.LoadSet.clicked.connect(self.LoadSet_clicked)
        self.SelectPrinter.clicked.connect(self.SelectPrinter_clicked)
        self.Print.clicked.connect(self.Print_clicked)
        self.btnApplyPwd.clicked.connect(self.ApplyPwd_clicked)
        self.btnCreateInfoCard.clicked.connect(self.CreateInfo_clicked)
        self.btnReadInfo.clicked.connect(self.ReadInfo_clicked)
        self.btnUartRead.clicked.connect(self.SerialRead_clicked)
        self.btnUartWrite.clicked.connect(self.SerialWrite_clicked)
        self.btnClearText.clicked.connect(self.ClearText_clicked)

        
    def Connec_clicked(self):

        if (self.connected == False):
            COM = 'COM' + self.choiseCom.currentText()
            try:
                if (COM == 'COMauto'):
                    self.sportiduino = Sportiduino(debug=True)
                else:
                    self.sportiduino = Sportiduino(COM,debug=True)

                self.sbCurPwd1.setValue((self.sportiduino.password & 0xFF0000) >> 16)
                self.sbCurPwd2.setValue((self.sportiduino.password & 0x00FF00) >> 8) 
                self.sbCurPwd3.setValue(self.sportiduino.password & 0x0000FF)
                
                self.showSettings(self.sportiduino.settings)
                idx = (self.sportiduino.antennaGain >> 4) - 2
                self.cbAntennaGain.setCurrentIndex(idx)
                
                self.sportiduino.beep_ok()
                self.connected = True
                self.addText('\nmaster station is connected')
                
            except:
                self.addText('\nError')
                self.connected = False
                

        else:
            self.sportiduino.disconnect()
            self.addText('\nmaster station is disconnected')
            self.connected = False
            

    def ReadCard_clicked(self):
        
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        try:
            self.textBrowser.setPlainText('')
            data = self.sportiduino.read_card(timeout = 0.5)
            self.sportiduino.beep_ok()
            
            self.readDataFormat(data)
            self.saveDataJson(data)
            
        except:
            self.sportiduino.beep_error()
            self.addText('\nError')

        
            
    def InitCard_clicked(self):

        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        text = self.cardLine.text()
        if(text.isdigit()):
            self.CardNum = text
        else:
            self.CardNum = '0'

        num = int(self.CardNum)
        if (num > 0 and num < 65000):
            
            try:
                self.sportiduino.init_card(num)
                self.addText ('\n\ninit card number {}'.format(num))
                if (self.AutoIncriment.checkState() != 0):
                    self.AutoIn = True
                    self.CardNum = str(num + 1)
                    self.cardLine.setText(self.CardNum)
            except:
                self.addText('\nError')
               
        else:
            self.addText("\nnot correct value")
            
    def SetNum_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
            
        num = self.sbStationNum.value()
        
        if (num > 0 and num <= 255):
            
            try:
                self.sportiduino.init_cp_number_card(num)
                self.addText ('\nset CP number {}'.format(num))
            except:
                self.addText('\nError')
              
        else:
            self.addText("\nnot correct value")
                            
    def SetTime_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        try:
            self.sportiduino.init_time_card(datetime.utcnow() + timedelta(seconds=3))
            self.addText ('\nset time')
        except:
            self.addText('\nError')
            sportiduino.beep_error()

    def SetStart_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(240)
            self.sbStationNum.setValue(240)
            self.addText ('\nset start statnion')
        except:
            self.addText('\nError')

    def SetFinish_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(245)
            self.sbStationNum.setValue(245)
            self.addText ('\nset finish statnion')
        except:
            self.addText('\nError')


    def CheckSt_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(248)
            self.sbStationNum.setValue(248)
            self.addText ('\nset check statnion')
        except:
            self.addText('\nError')

    def ClearSt_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(249)
            self.sbStationNum.setValue(249)
            self.addText ('\nset clear statnion')
        except:
            self.addText('\nError')

    def LogCard_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_backupreader()
            self.addText ('\nset dump card')
        except:
            self.addText('\nError')
                
    def ReadLog_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        readBuffer = ''
        try:
            data = self.sportiduino.read_backup()
            self.sportiduino.beep_ok()
            try:
                readBuffer += '\nread dump from CP: {}'.format(data['cp'])
            except:
                pass
            try:
                cards = data['cards']
                readBuffer += '\ntotal punches: {}\n'.format(len(cards))
                for i in range(0,len(cards),1):
                    readBuffer += '{},'.format(cards[i])
            except:
                pass

            self.dumpData.append(data)
            dumpFile = open(os.path.join('data','dumpData{:%Y%m%d%H%M%S}.json'.format(self.initTime)),'w')
            json.dump(self.dumpData, dumpFile)
            dumpFile.close()
            self.addText(readBuffer)
        except:
            self.addText('\nError')

    def SleepCard_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_sleepcard(self.dtCompetion.dateTime().toUTC())
            self.addText ('\nset sleep card')
        except Exception:
            traceback.print_exc()

    def PassCard_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        setSt = self.getSettingsFromUI()

        oldPass = self.sbOldPwd1.value()<<16 | self.sbOldPwd2.value()<<8 | self.sbOldPwd3.value()
        if (oldPass <0 or oldPass > 0xffffff):
            self.addText('\nnot correct old pass value')
            oldPass = -1

        newPass = self.sbNewPwd1.value()<<16 | self.sbNewPwd2.value()<<8 | self.sbNewPwd3.value()
        if (newPass <0 or newPass > 0xffffff):
            self.addText('\nnot correct new pass value')
            newPass = -1
            
        gain = (self.cbAntennaGain.currentIndex() + 2) << 4
        
        if (newPass!= -1 and oldPass!= -1):
            try:
                self.sportiduino.init_passwd_card(oldPass,newPass,setSt,gain)
                self.addText ('\nset password - settings card')
                
                self.sbCurPwd3.setValue(self.sbNewPwd3.value())
                self.sbCurPwd2.setValue(self.sbNewPwd2.value())
                self.sbCurPwd1.setValue(self.sbNewPwd1.value())
            except:
                self.addText('\nError')
            
    def LoadSet_clicked(self):
        
        try:
            sets = open(os.path.join('data','settings.txt'))
            self.WorkTime.setCurrentText(sets.readline().rstrip())
            self.StartFinish.setCurrentText(sets.readline().rstrip())
            self.CheckInitTime.setCurrentText(sets.readline().rstrip())
            self.CardCap.setCurrentText(sets.readline().rstrip())
            self.AutoDel.setCurrentText(sets.readline().rstrip())
            self.NewPass.setText(sets.readline().rstrip())
            self.OldPass.setText(sets.readline().rstrip())
            self.addText('\nload settings')
        except:
            self.addText('\nsettings are missing')

    def SaveSet_clicked(self):
                
        sets = open(os.path.join('data','settings.txt'),'w')
        sets.write(self.WorkTime.currentText()+'\n')
        sets.write(self.StartFinish.currentText()+'\n')
        sets.write(self.CheckInitTime.currentText()+'\n')
        sets.write(self.CardCap.currentText()+'\n')
        sets.write(self.AutoDel.currentText()+'\n')
        sets.write(self.NewPass.text()+'\n')
        sets.write(self.OldPass.text())
        self.addText('\nsave settings')

    def addText(self,text):

        logFile = open(os.path.join('log','logFile{:%Y%m%d%H%M%S}.txt'.format(self.initTime)),'a')
        print(text)
        self.textBrowser.setPlainText(self.textBrowser.toPlainText() + text)
        logFile.write(text)
        logFile.close()

    def SelectPrinter_clicked(self):
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            printer = dialog.printer()
            self.printerName.setText(QPrinter().printerName())
            
    def Print_clicked(self):
        self.printer = QPrinter()
        
        self.printer.setFullPage(True)
        self.printer.setPageMargins(3,3,3,3,QPrinter.Millimeter)
        page_size = QSizeF()
        page_size.setHeight(self.printer.height())
        page_size.setWidth(self.printer.width())
        self.textBrowser.document().setPageSize(page_size)
        self.textBrowser.document().setDocumentMargin(0.0)
        self.textBrowser.document().print_(self.printer)
        
    def ApplyPwd_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        curPass = self.sbCurPwd1.value()<<16 | self.sbCurPwd2.value()<<8 | self.sbCurPwd3.value()
        
        try:
            self.sportiduino.apply_pwd(curPass)
            self.addText ('\npassword has been applied')

        except:
            self.addText('\nError')
            
    def CreateInfo_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_info_card()
            self.addText ('\n\nGetInfo Card has been created')
        except:
            self.addText('\nError')
        
    def ReadInfo_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.addText('\n\nReads Info Card')
            bs = self.sportiduino.read_info_card()
            self.showBaseStationInfo(bs)
        except:
            self.addText('\nError')
    
    def SerialRead_clicked(self):
        try:
            self.addText('\n\nReads info about a base station by UART')
            port = 'COM' + self.cbUartPort.currentText()
            
            bs = BaseStation()
            bs.readInfoBySerial(port, self.sbCurPwd1.value(), self.sbCurPwd2.value(), self.sbCurPwd3.value())

            self.showBaseStationInfo(bs)
        except:
            traceback.print_exc()
            self.addText('\nError')
        

    def SerialWrite_clicked(self):
        
        try:
            self.addText('\n\nWrites settings to a base station by UART')
            port = 'COM' + self.cbUartPort.currentText()
            
            oldPwd1 = self.sbOldPwd1.value()
            oldPwd2 = self.sbOldPwd2.value()
            oldPwd3 = self.sbOldPwd3.value()
            
            newPwd1 = self.sbNewPwd1.value()
            newPwd2 = self.sbNewPwd2.value()
            newPwd3 = self.sbNewPwd3.value()
            
            num = self.sbStationNumByUart.value()
            sets = self.getSettingsFromUI()
            wakeup = self.dtCompetion.dateTime().toUTC().toPyDateTime()
            gain = (self.cbAntennaGain.currentIndex() + 2) << 4
            
            bs = BaseStation()
            bs.writeSettingsBySerial(port, oldPwd1, oldPwd2, oldPwd3, 
                                     newPwd1, newPwd2, newPwd3, num, sets, wakeup, gain)
        except:
            traceback.print_exc()
            self.addText('\nError')
            
    def ClearText_clicked(self):
        self.textBrowser.setPlainText('')

    def readDataFormat(self,data):
        data = copy.deepcopy(data)

        readBuffer ='\nCard: {}'.format(data['card_number'])
        print(data)

        if('start' in data):
            readBuffer +='\nStart: {}'.format(data['start'])
            
        if ('punches' in data):
            punches = data['punches']

            readBuffer +='\nCP - time'
            for punch in range(0, len(punches), 1):
                readBuffer += '\n{} - {:%H:%M:%S}'.format(punches[punch][0],punches[punch][1])
                    
        if('finish' in data):
            readBuffer +='\nFinish:  {}'.format(data['finish'])
   
        self.addText(readBuffer)
        if (self.AutoPrint.checkState()!= 0):
            self.Print_clicked()
            
    def saveDataJson(self,data):
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
            
        del data['page6']
        del data['page7']

        self.readData.append(data)
            
        dataFile = open(os.path.join('data','readData{:%Y%m%d%H%M%S}.json'.format(self.initTime)),'w')
        json.dump(self.readData, dataFile)
        dataFile.close()     
        
    def showSettings(self, settings):
        set1 = settings & 0x3
        self.WorkTime.setCurrentIndex(set1)
        
        set2 = (settings & 0x4) >> 0x2
        self.StartFinish.setCurrentIndex(set2)
        
        set3 = (settings & 0x8) >> 0x3
        self.CheckInitTime.setCurrentIndex(set3)
        
        set4 = (settings & 0x10) >> 0x4
        self.AutoDel.setCurrentIndex(set4)
        
        set5 = (settings & 0x20) >> 0x5
        self.cbFastMark.setCurrentIndex(set5)
        
    def getSettingsFromUI(self):
        workTime = self.WorkTime.currentText()
        stFi = self.StartFinish.currentText()
        checkIT = self.CheckInitTime.currentText()
        autoDel = self.AutoDel.currentText()
        fastMark = self.cbFastMark.currentText()

        if (workTime == '6 hour'):
            a = 0b00
        elif (workTime == '24 hour'):
            a = 0b01
        elif (workTime == 'not work'):
            a = 0b10
        elif (workTime == 'all time'):
            a = 0b11

        if (stFi == "off"):
            b = 0b0
        elif (stFi == 'on'):
            b = 0b1

        if (checkIT == 'off'):
            c = 0b0
        elif (checkIT == 'on'):
            c = 0b1

        if (autoDel == 'off'):
            d = 0b0
        elif (autoDel == 'on'):
            d = 0b1
            
        if (fastMark == 'off'):
            e = 0b0
        elif (fastMark == 'on'):
            e = 0b1

        setSt = a + ( b<<2) + (c<<3) + (d<<4) + (e<<5)
        
        return setSt
    
    def showBaseStationInfo(self, bs):
        self.addText('\nVersion: ' + str(bs.version))
        self.addText('\nStation Num: ' + str(bs.num))
        
        if(bs.num == BaseStation.START_STATION_NUM):
            self.addText('(Start)')
        elif (bs.num == BaseStation.FINISH_STATION_NUM):
            self.addText('(Finish)')
        elif (bs.num == BaseStation.CHECK_STATION_NUM):
            self.addText('(Check)')
        elif (bs.num == BaseStation.CLEAR_STATION_NUM):
            self.addText('(Clear)')
            
        self.sbStationNum.setValue(bs.num)
        self.sbStationNumByUart.setValue(bs.num)
            
        self.showSettings(bs.settings)
        self.addText('\nSettings: ' + bin(bs.settings).lstrip('-0b').zfill(8))
        
        if(bs.batteryOk):
            self.addText('\nBattery: Ok')
        else:
            self.addText('\nBattery: Low')
            
        if(bs.mode == BaseStation.MODE_ACTIVE):
            self.addText('\nMode: Active')
        elif(bs.mode == BaseStation.MODE_WAIT):
            self.addText('\nMode: Wait')
        elif(bs.mode == BaseStation.MODE_SLEEP):
            self.addText('\nMode: Sleep')
            
        self.addText('\nDate&Time: ' + datetime.fromtimestamp(bs.timestamp).strftime("%d-%m-%Y %H:%M:%S"))
        self.addText('\nWake Up: ' + datetime.fromtimestamp(bs.wakeup).strftime("%d-%m-%Y %H:%M:%S"))
        
        self.dtCompetion.setDateTime(datetime.fromtimestamp(bs.wakeup))
        
        idx = (bs.antennaGain >> 4) - 2;
        self.cbAntennaGain.setCurrentIndex(idx)
        self.addText('\nAntenna Gain: ' + self.cbAntennaGain.currentText())
        
if __name__ == '__main__':
    
    try:
        os.mkdir('log')
        os.mkdir('data')
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    app.exec_()
