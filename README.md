# SportiduinoPQ

![](https://github.com/sportiduino/SportiduinoPQ/workflows/Python%20package/badge.svg)

![SportiduinoPQ Screenshot](/images/main1.JPG)

[Русский язык](README.ru.md)

Simple GUI software based on [Python module](https://github.com/sportiduino/sportiduinoPython) 
and PyQt5 for working with [Sportiduino](https://github.com/sportiduino/sportiduino) the electronic timing system for orienteering.

- [Manual](https://github.com/sportiduino/sportiduino/blob/master/Doc/en/UserManual.md)
- [Downloads](https://github.com/sportiduino/SportiduinoPQ/releases)


## Installation

You can download portable precompiled version of the program (exe file) for Windows systems,
the installation is not required. 

Or run the program under Python3.
For that you should install [Python](https://www.python.org/) and then install all requirements by command:

```commandline
pip install -r requirements.txt
```

For generating exe file run:

```commandline
pip install pyinstaller
pyinstaller --onefile --noconsole SportiduinoPQ.py
```

## Usage

### Linux

In terminal emulator run:

```sh
./SportiduinoPQ.py
```

### Windows

Run `SportiduinoPQ.exe`

