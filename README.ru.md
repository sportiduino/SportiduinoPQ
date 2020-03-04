# SportiduinoPQ

![Скриншот SportiduinoPQ](/images/main1.JPG)

[English](README.md)

Простая GUI программа для работы с системой электронной отметки для спортивного ориентирования [Sportiduino](https://github.com/sportiduino/sportiduino),
основанная на [Python модуле](https://github.com/sportiduino/sportiduinoPython) и PyQt5.


- [Руководство пользователя](https://github.com/sportiduino/sportiduino/blob/master/Doc/en/UserManual.md)
- [Скачать](https://github.com/sportiduino/SportiduinoPQ/releases)


## Установка

Вы можете скачать портативную скомпилированную версию программы (exe файл) для Windows систем, установка не требуется.

Или программу можно запустить под Python3.
Для этого установите [Python](https://www.python.org/) и установите все зависимости из командной строки:

```commandline
pip install pyserial pyqt5 six sip
```

При установке Python не забудьте активировать опцию "Добавить PIP в PATH".

Для генерации exe файла запустите:

```commandline
pip install pyinstaller
pyinstaller --onefile --noconsole SportiduinoPQ.py
```


