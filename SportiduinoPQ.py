import sys
sys.path.append('..')
import os.path
import time
import datetime
import serial
import json
import copy
import design
from sportiduino import Sportiduino
from datetime import datetime, timedelta
from PyQt5 import uic, QtWidgets, QtPrintSupport, QtCore, sip
from PyQt5.QtCore import QSizeF, QDateTime
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
        self.StatNum = '0'
        self.OldPass.setText('0')
        self.NewPass.setText('0')
        self.printerName.setText(QPrinter().printerName())
        
        self.initTime = datetime.now()
        self.addText('{:%Y-%m-%d %H:%M:%S}'.format(self.initTime))

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


        
    def Connec_clicked(self):

        if (self.connected == False):
            COM = 'COM' + self.choiseCom.currentText()
            try:
                if (COM == 'COMauto'):
                    self.sportiduino = Sportiduino(debug=True)
                else:
                    self.sportiduino = Sportiduino(COM,debug=True)

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
                self.addText ('\ninit card number {}'.format(num))
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
        
        text = self.StationLine.text()
        if(text.isdigit()):
            self.StatNum = text
        else:
            self.StatNum = '0'
            
        num = int(self.StatNum)
        if (num > 0 and num < 240):
            
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
            self.addText ('\nset start statnion')
        except:
            self.addText('\nError')

    def SetFinish_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(245)
            self.addText ('\nset finish statnion')
        except:
            self.addText('\nError')


    def CheckSt_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(248)
            self.addText ('\nset check statnion')
        except:
            self.addText('\nError')

    def ClearSt_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(249)
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
            self.sportiduino.init_sleepcard()
            self.addText ('\nset sleep card')
        except:
            self.addText('\nError')

    def PassCard_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return

        workTime = self.WorkTime.currentText()
        stFi = self.StartFinish.currentText()
        checkIT = self.CheckInitTime.currentText()
        cardCap = self.CardCap.currentText()
        autoDel = self.AutoDel.currentText()

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

        if (cardCap == "auto"):
            d = 0b00
        elif (cardCap == '32'):
            d = 0b01
        elif (cardCap == '64'):
            d = 0b10
        elif (cardCap == "120"):
            d = 0b11

        if (autoDel == 'off'):
            e = 0b0
        elif (autoDel == 'on'):
            e = 0b1

        setSt = a + ( b<<2) + (c<<3) + (d<<4) + (e<<6)
        
        if (self.OldPass.text().isdigit()):
            oldPass = int(self.OldPass.text())
            if (oldPass <0 or oldPass > 10000000):
                self.addText('\nnot correct old pass value')
                oldPass = -1
        else:
            self.addText('\nnot correct old pass value')
            oldPass = -1

        if (self.NewPass.text().isdigit()):
            newPass = int(self.NewPass.text())
            if (newPass <0 or newPass > 10000000):
                self.addText('\nnot correct new pass value')
                newPass = -1
        else:
            self.addText('\nnot correct new pass value')
            newPass = -1

        if (newPass!= -1 and oldPass!= -1):
            try:
                self.sportiduino.init_passwd_card(oldPass,newPass,setSt)
                self.addText ('\nset password - settings card')
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
        self.textBrowser.setPlainText(text)
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

        if ('finish' in data and 'start' in data):
            readBuffer += '\n{}'.format(data['finish']-data['start'])
           
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
