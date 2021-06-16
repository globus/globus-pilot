import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join('pilot', 'version.py')) as f:
    exec(f.read(), version_ns)

with open('README.rst') as f:
    long_description = f.read()

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)

setup(
    name='globus-pilot',
    description='A CLI tool for cataloging pilot 1 data',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/globusonline/pilot1-tools/tree/master',
    maintainer='globus',
    maintainer_email='support@globus.org',
    version=version_ns['__version__'],
    packages=find_packages(),
    package_data={
      '': ['*.json'],
    },
    requires=[],
    entry_points='''
    [console_scripts]
    pilot=pilot.commands.main:cli
''',
    install_requires=install_requires,
    dependency_links=[],
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
