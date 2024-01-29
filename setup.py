import os

from setuptools import setup, find_packages


def read(f_name):
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()


setup(
    name='nwg-readme-browser',
    version='0.1.2',
    description='nwg-shell README browser',
    packages=find_packages(),
    include_package_data=True,
    package_data={},
    url='https://github.com/nwg-piotr/nwg-readme-browser',
    license='MIT',
    author='Piotr Miller',
    author_email='nwg.piotr@gmail.com',
    python_requires='>=3.6.0',
    install_requires=[],
    entry_points={
        'gui_scripts': [
            'nwg-readme-browser = nwg_readme_browser.main:main'
        ]
    }
)
