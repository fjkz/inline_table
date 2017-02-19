"""The set up script of the inline_table module."""

from setuptools import setup

# The long description is copied from README.rst
# from line 4 to the previous line of the Installation section.
with open('README.rst', 'r') as f:
    src_lines = f.readlines()
copy_lines = []
for line in src_lines[4:]:
    if line == 'Installation\n':
        break
    copy_lines.append(line)
long_description = ''.join(copy_lines)

classifiers=[
    'Development Status :: 1 - Planning',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
]

setup(name='inline_table',
      version='0.0',
      description='Library for embedding text tables into source-code',
      long_description=long_description,
      author='Kazuho Fujii',
      author_email='kazuho.fujii@gmail.com',
      url='http://github.com/fjkz/inline_table',
      license='MIT License',
      platforms='OS Independent',
      install_requires=[
          'docutils>0.13',
      ],
      classifiers=classifiers,
      py_modules=['inline_table'],
      )
