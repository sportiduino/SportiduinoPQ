import sys
sys.path.append('..')
import os.path
import time
import datetime
import serial
import json
import xmltodict
import copy
from math import cos, asin, sqrt
from sportiduino import Sportiduino
from datetime import datetime, timedelta
from PyQt5 import uic, QtWidgets, QtPrintSupport, QtCore
from PyQt5.QtCore import QSizeF, QDateTime
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QApplication, QFileDialog

qtFile = 'design.ui'
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtFile)

class App(QtWidgets.QMainWindow, Ui_MainWindow):
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
        self.gps = {}
        self.printerName.setText(QPrinter().printerName())
        
        self.initTime = datetime.now()
        self.addText('{:%Y-%m-%d %H:%M:%S}'.format(self.initTime))

        now = QtCore.QDateTime.currentDateTime()
        self.dateTimeEdit.setDateTime(now)

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
        self.OpenGpx.clicked.connect(self.OpenGpx_clicked)

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

        force_start = None
        
        try:
            data = self.sportiduino.read_card(timeout = 0.5)
            self.sportiduino.beep_ok()
            
            if (self.ForceStart.checkState() != 0):
                forceStartTime = self.dateTimeEdit.dateTime().toMSecsSinceEpoch() // 1000
                py_date = datetime.fromtimestamp(forceStartTime)
                force_start = py_date
                
            self.readDataFormat(data, force_start = force_start)
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

    def readDataFormat(self,data, force_start = None):

        data = copy.deepcopy(data)

        totalDist = 0
        totalTime = 0
        readBuffer ='\nCard: {}'.format(data['card_number'])

        if force_start is not None:
            data['start'] = force_start

        if('start' in data):
            readBuffer +='\nStart: {}'.format(data['start'])
            
        if ('punches' in data):
            punches = data['punches']
            if ('start' in data):
                predT = data['start']
                isPredT = True
            elif (len(punches)>0):
                predT = punches[0][1]
                isPredT = True
            else:
                isPredT = False
            predNum = 240
            readBuffer +='\nN (CP) split, temp min/km'
            for punch in range(0, len(punches), 1):
                split = punches[punch][1].timestamp()-predT.timestamp()
                if (split > 0):
                    dist = 0
                    try:
                        dist = self.distance(str(punches[punch][0]),predNum)
                    except:
                        pass
                    if (dist == 0 or dist is None):
                        dist =''
                    else:
                        totalDist += dist
                        dist = '{0:4.1f}'.format((split/60)/dist)
                    readBuffer +='\n{}  ({})  {}  {}'.format(punch+1,\
                                                                punches[punch][0],\
                                                                punches[punch][1]-predT,\
                                                                dist)
                else:
                    readBuffer +='\n{}  ({})  error val'.format(punch,\
                                                                punches[punch][0])
                predT = punches[punch][1]
                predNum = punches[punch][0]
                    
        if('finish' in data and isPredT == True):
            split = data['finish'].timestamp()-predT.timestamp()
            if (split > 0):
                dist = 0
                try:
                    dist = self.distance(245,predNum)
                except:
                    pass
                if (dist == 0 or dist is None):
                    dist =''
                else:
                    totalDist += dist
                    dist = '{0:4.1f}'.format((split/60)/dist)
                readBuffer +='\nFinish:  {}  {}'.format(data['finish']-predT, dist)
            else:
                readBuffer +='\nFinish:  error val'
            
        if ('finish' in data and 'start' in data):
            if (data['finish'].timestamp()-data['start'].timestamp() > 0):
                readBuffer +='\nTime:  {}'.format(data['finish']-data['start'])
                totalTime = data['finish'].timestamp()-data['start'].timestamp()
            else:
                readBuffer +='\nTime:  error val'

        if (totalDist != 0):
            readBuffer += '\nDistance: {0:4.3f}km'.format(totalDist)
            if (totalTime != 0):
                readBuffer += '\nAverage temp: {0:4.1f}min/km'.format((totalTime/60)/totalDist)
           
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

        

    def OpenGpx_clicked(self):

        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
        try:
            gpxFile = open(fname)
            gpx_xml = gpxFile.read()
            gpx_dict = xmltodict.parse(gpx_xml)
            buffer = '\nGPX file have been loaded'
            points = gpx_dict['gpx']['wpt']
            for point in range(0, len(points), 1):
                coord = (points[point]['@lat'], points[point]['@lon'])
                name = points[point]['name'] 
                self.gps[name] = coord
                buffer += '\n{} {}'.format(name,coord)
            self.addText(buffer)
        except:
            self.addText('\nError')

    def distance(self,p1, p2):
        if (str(p1) in self.gps and str(p2) in self.gps):
            lat1 = float(self.gps[str(p1)][0])
            lon1 = float(self.gps[str(p1)][1])
            lat2 = float(self.gps[str(p2)][0])
            lon2 = float(self.gps[str(p2)][1])
            p = 0.017453292519943295
            a = 0.5 - cos((lat2 - lat1) * p)/2 + \
                cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
            return 12742 * asin(sqrt(a))
        else:
            return None
        
            
        
        
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
