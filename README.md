﻿# sportiduinoPQ

### version 0.6.0

In the [last release](https://github.com/alexandervolikov/SportiduinoPQ/releases), you can download the program with the exe file for Windows systems, the installation is not required. 

Or run the lates program under python. For that you should install [python](https://www.python.org/). Writhe path to pip in PATH (instruction easy serching in web) and then install all requirements by command:

```commandline
pip install pyserial pyqt5 xmltodict six sip
```

exe generated by pyinstaller:

```commandline
pip install pyinstaller
pyinstaller --onefile --noconsole SportiduinoPQ.py
```

[Русский язык](https://github.com/alexandervolikov/SportiduinoPQ/blob/master/README.ru.md)

This repository is dedicated to developing simple GUI software based on [python module](https://github.com/alexandervolikov/sportiduinoPython) and PyQt for working with the electronic marking system for orienteering [Sportiduino](
https://github.com/alexandervolikov/sportIDuino)

Manual available in user manual at https://github.com/alexandervolikov/sportiduino

![](https://raw.githubusercontent.com/alexandervolikov/SportiduinoPQ/master/image/main1.JPG)