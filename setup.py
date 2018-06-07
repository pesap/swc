"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject """

# Always prefer setuptools over distutils
import os
from setuptools import find_packages, setup, Command

from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))

about = {}

with open(os.path.join(here, "swc", "__version__.py")) as f:
    exec (f.read(), about)

required = [
    'requests',
    'pandas',
    'click',
    'python-dotenv'
]

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='swc',  # Required
    version=about['__version__'],
    description='A sample Python project',  # Required
    author='pesap',  # Optional
    author_email='pesapsanchez@gmail.com',  # Optional
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/example-project",
    install_requires=required,
    include_package_data=True,
    packages=find_packages(include=['swc', 'swc.*'],
                           exclude=['tests']),
    keywords='sam solar simulation nsrdb',  # Optional
    entry_points={
        'console_scripts': ['swc = swc:main']
    },
)
