"""The set up script of the inline_table module."""

from setuptools import setup


setup(name='inline_table',
      version='0.1.0',
      description='Embeded text tables in code',
      long_description=open('README.rst').read(),
      author='Kazuho Fujii',
      author_email='kazuho.fujii@gmail.com',
      url='http://github.com/fjkz/inline_table',
      license='MIT License',
      platforms='OS Independent',
      install_requires=[
          'docutils>0.13',
      ],
      classifiers=[
          'Development Status :: 1 - Planning',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.4',
          ],
      py_modules=['inline_table'],
      test_suite='test_inline_table.suite',
      )
