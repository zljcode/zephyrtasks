# -*- mode: python ; coding: utf-8 -*-
import os

_venv = os.path.join(SPECPATH, '.venv', 'Lib', 'site-packages', 'PyQt5')
_qt5_bin = os.path.join(_venv, 'Qt5', 'bin')
_qt5_plugins = os.path.join(_venv, 'Qt5', 'plugins', 'platforms')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[
        (os.path.join(_qt5_bin, 'msvcp140.dll'), '.'),
        (os.path.join(_qt5_bin, 'msvcp140_1.dll'), '.'),
        (os.path.join(_qt5_bin, 'msvcp140_2.dll'), '.'),
        (os.path.join(_qt5_bin, 'vcruntime140.dll'), '.'),
        (os.path.join(_qt5_bin, 'vcruntime140_1.dll'), '.'),
        (os.path.join(_qt5_bin, 'concrt140.dll'), '.'),
        (os.path.join(_qt5_bin, 'libEGL.dll'), '.'),
        (os.path.join(_qt5_bin, 'libGLESv2.dll'), '.'),
        (os.path.join(_qt5_bin, 'd3dcompiler_47.dll'), '.'),
    ],
    datas=[(_qt5_plugins, r'PyQt5\Qt5\plugins\platforms')],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip'],
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
    name='zephyrtodo',
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
    icon=['resources\\logo_proper.ico'],
)
