import os
from distutils.core import setup

setup(name='mimoza',
      description='Mimoza: zoomable visualization of metabolic models.',
      long_description=open('README.md').read(),
      author='Anna Zhukova',
      author_email='zhutchok@gmail.com',
      url='https://gitlab.inria.fr/mimoza',
      version='0.1',
      packages=['mimoza'],
      package_data={'sbml_vis': [os.path.join('..', 'README.md'),
                                 os.path.join('..', 'mimoza.py'),
                                 os.path.join('..', '*.html')]},
      include_package_data=True,
      platform=['MacOS', 'Linux', 'Windows'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      download_url='https://gitlab.inria.fr/mimoza/archive/0.1.zip',
      install_requires=['mod_sbml>=0.2.3', 'sbml_generalization>=0.1.1', 'python-libsbml-experimental',
                        'sbml_vis>=0.1.3']
      )
