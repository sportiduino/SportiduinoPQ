# SportiduinoPQ

![](https://github.com/sportiduino/SportiduinoPQ/workflows/Python%20package/badge.svg)

![Скриншот SportiduinoPQ](/images/main1.JPG)

[English](README.md)

Простая GUI программа для работы с системой электронной отметки для спортивного ориентирования [Sportiduino](https://github.com/sportiduino/sportiduino),
основанная на [Python модуле](https://github.com/sportiduino/sportiduinoPython) и PyQt5.

- [Руководство пользователя](https://github.com/sportiduino/sportiduino/blob/master/Doc/ru/UserManual.md)
- [Скачать](https://github.com/sportiduino/SportiduinoPQ/releases)


## Установка

Вы можете скачать портативную скомпилированную версию программы (exe файл) для Windows систем, установка не требуется.

Или программу можно запустить под Python3.
Для этого установите [Python](https://www.python.org/).
При установке не забудьте активировать опцию "Добавить PIP в PATH".
Установите необходимые зависимости из командной строки:

```commandline
pip install -r requirements.txt
```

Для генерации exe файла запустите:

```commandline
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data translation/*.qm;translation/ SportiduinoPQ.py
```

## Usage

### Linux

В эмуляторе терминала запустите:

```sh
./SportiduinoPQ.py
```

### Windows

Запустите `SportiduinoPQ.exe`

