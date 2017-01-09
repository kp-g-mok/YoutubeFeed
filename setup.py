import sys
import requests.certs
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = {'packages': [],
                'excludes': [],
                'includes': ['atexit',
                             'cx_Freeze',
                             'googleapiclient',
                             'httplib2',
                             'oauth2client',
                             'pyasn1',
                             'pyasn1_modules',
                             'rsa',
                             'six',
                             'uritemplate',
                             'urllib3'],
                'include_files': ['README.md',
                                  'client_secret.json',
                                  'main.ui',
                                  'settings.json',
                                  'subscription_manager.xml',
                                  (requests.certs.where(), 'cacert.pem')]
                }

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('gui_main.py', base=base, targetName='YoutubeFeed.exe')
]

setup(name='YoutubeFeed',
      version='1.0',
      description='Find new videos on your favourite Youtube channels since last time you checked.',
      options={'build_exe': buildOptions},
      executables=executables)
