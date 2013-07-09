__author__ = 'anna'

from distutils.core import setup
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

setup(name='model_generalization',
      description='SBML Model Generalization Utilities',
      author='Anna Zhukova',
      author_email='anna.zhukova@inria.fr',
      url='https://team.inria.fr/magnome/software/',
      version='1.0',
      packages=['generalization', 'main', 'utils'],
      data_files=[('.', ['Licence_CeCILL_V2-en.txt']), ('data', ['data/chebi.obo'])],
      license='Licence_CeCILL_V2-en.txt',
      platform=['MacOS','Linux', 'Windows'],
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
      long_description=open('README.txt').read(),
      install_requires=["libsbml >= 5.0.0"],
      requires=['libsbml']
      )