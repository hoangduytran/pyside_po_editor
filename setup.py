# setup.py
from setuptools import setup

APP = ['main.py']
DATA_FILES = ['Info.plist']    # your custom Info.plist
OPTIONS = {
    'argv_emulation': True,
    'alias': True,
    'plist': {
        'CFBundleName':             'POEditor',
        'CFBundleDisplayName':      'POEditor',
        'CFBundleIdentifier':       'com.hoangduytran.POEditor',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion':          '1',
        'NSHighResolutionCapable':  True,
    },
    'packages': ['polib','requests','PySide6'],
    'strip':       True,
    'compressed':  True,
    'excludes': [
        # stdlib and test frameworks
        'tkinter', 'unittest', 'test', 'pydoc',

        # Windows‐only bits
        'win32com', 'win32com.shell', 'com', 'com.sun.jna',

        # optional HTTP crypto layers (we use requests + stdlib)
        'cryptography', 'OpenSSL', 'simplejson', 'zstandard',

        # pkg_resources vendored modules
        'pkg_resources._vendor',

        # PySide6 modules *not* used by your app
        'PySide6.QtAsync',        # asyncio support
        'PySide6.QtQml',           'PySide6.QtQuick',
        'PySide6.QtMultimedia',    'PySide6.QtWebEngine',
        'PySide6.QtWebChannel',    'PySide6.QtWebSockets',
        'PySide6.QtCharts',        'PySide6.QtChart',
        'PySide6.QtXml',           'PySide6.QtXmlPatterns',
        'PySide6.QtNetwork',       # requests uses urllib3, not QtNetwork
        'PySide6.QtBluetooth',     'PySide6.QtConcurrent',
        'PySide6.QtDesigner',      'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',  'PySide6.QtPurchasing',
        'PySide6.QtRemoteObjects', 'PySide6.QtSensors',
        'PySide6.QtSerialPort',    'PySide6.QtSql',
        'PySide6.QtSvg',           'PySide6.QtTest',
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
