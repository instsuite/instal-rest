from distutils.core import setup, Extension
import instalrest
setup(
    name='instalrest',
    version=instalrest.__version__,
    packages=['instalrest',
              'instalrest.instalcelery',
              'instalrest.tests',
              'instalrest.v1'],
    url='http://instsuite.github.io/',
    license='GPLv3',
    author='InstAL team @ Univesity of Bath',
    author_email='',
    description='InstAL: Institutional Action Language Framework and Tools',
)
