from setuptools import setup, find_packages
import sys, os

version = '10'

setup(name='vkvideo',
      version=version,
      description="VK video lens",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Vladimir Iakovlev',
      author_email='nvbn.rm@gmail.com',
      url='https://github.com/nvbn/vklens',
      license='Apache',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
      ],
      entry_points={
        'console_scripts': [
          'vkvideo=vkvideo.auth:main',
          'vklens=vkvideo.lens:main',
          'vksettings=vkvideo.settings:main',
        ]
      },
      data_files=[
        ('share/icons/hicolor/64x64/apps', ['vkvideo.png']),
        ('share/pixmaps', ['vkvideo.png']),
        ('share/applications', ['vkvideo.desktop']),
        ('share/unity/lenses/vkvideo', ['vkvideo.lens']),
        ('share/dbus-1/services', ['vkvideo.service']),
        ('share/locale/ru/LC_MESSAGES', ['locale/ru/LC_MESSAGES/vklens.mo']),
      ],
)
