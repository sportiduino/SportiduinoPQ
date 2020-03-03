#!/bin/bash

pylupdate5 -verbose sportiduinopq.pro
python3 -m PyQt5.uic.pyuic -x design.ui -o design.py

