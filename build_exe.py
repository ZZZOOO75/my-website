# -*- coding: utf-8 -*-
import sys, os
PYB = r'C:\Users\l\Documents\deepseek-harness\default-workspace\pybuild'
APPDIR = r'C:\Users\l\Documents\deepseek-harness\default-workspace\weibull-tool'
sys.path.insert(0, PYB)
from PyInstaller.__main__ import run
args = [
    '--noconfirm', '--clean',
    '--onefile', '--windowed',
    '--name', 'WeibullTool',
    '--distpath', os.path.join(APPDIR, 'dist'),
    '--workpath', os.path.join(APPDIR, 'build'),
    '--specpath', APPDIR,
    os.path.join(APPDIR, 'app.py'),
]
print('运行 PyInstaller，参数:', args)
run(args)
print('完成，dist 目录:', os.path.join(APPDIR, 'dist'))
