# sportiduinoPQ

### версия 0.6.1

В [последнем релизе](https://github.com/alexandervolikov/SportiduinoPQ/releases) можно скачать программу с exe файлом для Windows систем, установка не требуется 

Для запуска из под Python последней версии нужно установить [python](https://www.python.org/). Поставить галочки - добавить PIP в PATH и установить все зависимости из командной строки:

```commandline
pip install pyserial pyqt5 xmltodict six sip
```

exe сгенерирован с помощью pyinstaller:

```commandline
pip install pyinstaller
pyinstaller --onefile --noconsole SportiduinoPQ.py
```

[English](https://github.com/alexandervolikov/SportiduinoPQ/blob/master/README.md)

В данном репозитории ведется разработка базового GUI программного обеспечения основанного на [python модуле](https://github.com/alexandervolikov/sportiduinoPython) и PyQt для работы с системой электронной отметки для спортивного ориентирования Sportiduino: https://github.com/alexandervolikov/sportIDuino

Инструкция находится в руководстве пользователя https://github.com/alexandervolikov/sportiduino

![](https://raw.githubusercontent.com/alexandervolikov/SportiduinoPQ/master/image/main1.JPG)