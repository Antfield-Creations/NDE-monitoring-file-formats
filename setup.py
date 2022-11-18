#!/usr/bin/env python

from configparser import ConfigParser
from distutils.core import setup

config = ConfigParser()
config.read('Pipfile')
dependencies = [dep.replace("\"", "") for dep in config['packages'].keys()]
print(dependencies)

setup(
      name='bass_diffusion',
      version='0.1.0',
      description='Python implementation of the Bass diffusion model',
      author="Rein van 't Veer",
      author_email='rein@vantveer.me',
      url='https://github.com/Antfield-Creations/NDE-monitoring-file-formats',
      install_requires=dependencies,
      packages=['bass_diffusion', 'nde_analysis'],
      package_dir={
            'bass_diffusion': './models',
            'nde_analysis': './analysis',
      }
)
