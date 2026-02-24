# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
使用方法:
    pip install pyinstaller
    pyinstaller build.spec
"""

import sys

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('xq_icon.png', '.')],
    hiddenimports=['scraper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='知识星球爬取工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app 打包
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='知识星球爬取工具.app',
        icon='xq_icon.icns',
        bundle_identifier='com.zsxq.scraper',
        info_plist={
            'CFBundleName': '知识星球爬取工具',
            'CFBundleDisplayName': '知识星球爬取工具',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
