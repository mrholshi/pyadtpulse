import setuptools
import os

__version__ = '0.0.4'

here = os.path.dirname(os.path.abspath(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setuptools.setup(name='pyadtpulse',
      version = __version__,
      description = 'Library to interface with portal.adtpulse.com accounts',
      long_description = long_description,
      url = 'https://github.com/mrholshi/pyadtpulse',
      download_url = 'https://github.com/mrholshi/pyadtpulse/archive/' + __version__,
      author = 'Grant Hoelscher',
      author_email = 'mrholshi@gmail.com',
      license = 'MIT',
      packages = setuptools.find_packages(exclude=['docs', 'tests*']),
      include_package_data = True,
      install_requires = install_requires,
      dependency_links = dependency_links,
      zip_safe = True)
