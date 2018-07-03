import sys
sys.path.append('..')
from sportiduino import Sportiduino
import time
from datetime import datetime, timedelta
import serial
import os.path



from PyQt5 import QtWidgets

import design

class App(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        
        self.connected = False
        self.Connec.clicked.connect(self.Connec_clicked)

        self.OldPass.setText('0')
        self.NewPass.setText('0')
        
        self.ReadCard.clicked.connect(self.ReadCard_clicked)

        self.InitCard.clicked.connect(self.InitCard_clicked)
        self.CardNum = '0'     
        self.AutoIncriment.stateChanged.connect(self.changeAuto)
        self.AutoIn = False

        self.SetTime.clicked.connect(self.SetTime_clicked)

        self.SetNum.clicked.connect(self.SetNum_clicked)
        self.StatNum = '0'

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

        self.log =''

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
            print(data)
            self.addText('\nthe card number: '+str(data['card_number']))
            try:
                self.addText('\nstart time: '+str(data['start']))
            except:
                pass

            try:
                self.addText('\nfinish time: '+str(data['finish']))
                self.addText('\ntotal time: '+str(data['finish']-data['start']))
            except:
                pass

            try:
                punches = data['punches']
                self.addText('\npunches: '+str(len(punches))+', CP - time:')
                for punch in punches:
                    self.addText('\n'+str(punch[0])+' '+str(punch[1]))
            except:
                pass

            
            
            
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
            except:
                self.addText('\nError')

            if (self.AutoIn == True):
                self.CardNum = str(num + 1)
                self.cardLine.setText(self.CardNum)
                            
        else:
            self.addText("\nnot correct value")
            
    def changeAuto(self,state):
        
        if (self.AutoIncriment.checkState() != 0):
            self.AutoIn = True
        else:
            self.AutoIn = False   

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

    def ClearSt_clicked(self):
        if (self.connected == False):
            self.addText('\nmaster station is not connected')
            return
        
        try:
            self.sportiduino.init_cp_number_card(249)
            self.addText ('\nset clear station')
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
        
        try:
            data = self.sportiduino.read_backup()
            self.sportiduino.beep_ok()
            try:
                self.addText('\nread dump from CP: {}'.format(str(data['cp'])))
            except:
                pass
            try:
                cards = data['cards']
                self.addText('\ntotal punches: {}\n'.format(str(len(cards))))
                for i in range(0,len(cards),1):
                    self.addText(str(cards[i])+',')
            except:
                pass
            
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
        try:
            os.mkdir('data')
        except Exception:
            pass
        
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
        print(text)
        self.log += text
        self.textBrowser.setPlainText(self.log)
        self.textBrowser.verticalScrollBar().setValue(self.textBrowser.verticalScrollBar().maximum())
        logFile.write(text)

        
if __name__ == '__main__':
    
    buffer = 1
    time=datetime.today()
    timeLog=[]
    timeLog.append(time.year)
    timeLog.append(time.month)
    timeLog.append(time.day)
    timeLog.append(time.hour)
    timeLog.append(time.minute)
    timeLog.append(time.second)

    try:
        os.mkdir('log')
    except Exception:
        pass

    logFile = open(os.path.join('log','logfile{}.txt'.format(timeLog)),'w',buffer)

    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    app.exec_()
    logFile.close()
