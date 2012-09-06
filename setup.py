try:
    from setuptools import setup
    setup # quiet "redefinition of unused ..." warning from pyflakes
    # arguments that distutils doesn't understand
    setuptools_kwargs = {
        'install_requires': [
          'ply>=3.4',
          ],
        'provides': ['rajax'],
        'zip_safe': False
        }
except ImportError:
    from distutils.core import setup
    setuptools_kwargs = {}

setup(name='rajax',
      version=0.1,
      description=(
        'A regex compiler.'
      ),
      author='Steve Johnson',
      author_email='steve.johnson.public@gmail.com',
      url='https://github.com/cwru-compilers/regex_compiler',
      packages=['rajax'],
      platforms=['unix'],
      **setuptools_kwargs
)

