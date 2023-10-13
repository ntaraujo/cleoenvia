# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.toc_conversion import Tree
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis

block_cipher = None

a = Analysis(
    ["src/main.py"],
    pathex=["src/"],
    binaries=[],
    hiddenimports=["Gooey", "pandas", "Pillow", "pywin32", "selenium", "appdirs", "webdriver-manager"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas += Tree('src', prefix='.', excludes=['main.py'])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Cleo Envia",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='src/gooey-images/program_icon.ico',
)
