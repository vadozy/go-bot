from setuptools import setup
from setuptools import find_packages

setup(name='dlgo',
      version='0.1',
      description='Go Bot with neural network',
      url='https://github.com/vadozy/DeepLearning-Game-of-Go.git',
      install_requires=['tensorflow', 'keras', 'h5py', 'six'],
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
