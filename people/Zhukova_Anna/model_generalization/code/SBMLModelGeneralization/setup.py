__author__ = 'anna'

from setuptools import setup, find_packages
from sys import version

if version < '2.2.3':
    from distutils.dist import DistributionMetadata

    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None


setup(name='SBMLModelGeneralization',
      description='SBML model generalization utilities.',
      long_description=open('README.txt').read(),
      author='Anna Zhukova',
      author_email='anna.zhukova@inria.fr',
      url='https://team.inria.fr/magnome/software/',
      version='1.0',
      packages=find_packages(exclude=['sbml_generalization/runner/', 'sbml_generalization/runner/path2models']),
      package_data={'': ['sbml_generalization/data/', 'sbml_generalization/data/*.obo']},
      include_package_data=True,
      license='LICENSE.txt',
      platform=['MacOS', 'Linux', 'Windows'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'License :: CeCILL',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Topic :: Systems Biology',
          'Topic :: Software Development',
      ],
      requires=['libsbml', 'sympy', 'libsbgnpy', 'openpyxl']
)