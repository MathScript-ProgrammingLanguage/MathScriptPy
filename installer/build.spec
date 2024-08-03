# -*- mode: python ; coding: utf-8 -*-

from PIL import Image
from shutil import copy2 as copy
from os import remove
from os.path import exists
import sys
from svg2png import svg2png

if not exists('logo.svg'):
    copy('../logo.svg', 'logo.svg')
if not exists('logo.png'):
    try:
        svg2png('logo.svg')
    except:
        pass
if not exists('logo.ico'):
    image = Image.open('logo.png')

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    resized_images = [image.resize(size, Image.BICUBIC) for size in sizes]

    resized_images[0].save('logo.ico', format='ICO', sizes=sizes, append_images=[img for img in resized_images[1:]])
if not exists('LICENSE'):
    copy('../LICENSE', 'LICENSE')

a = Analysis(
    ['main.py', 'env.py'],
    pathex=[],
    binaries=[],
    datas=[('LICENSE', '.'), ('logo.svg', '.'), ('logo.ico', '.'), ('logo.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MathScript Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./logo.ico'
)