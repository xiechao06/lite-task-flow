from distutils.core import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand
import sys
import os.path

PACKAGE = "lite_task_flow"
NAME = "lite-task-flow"
DESCRIPTION = "a light weight task flow framework"
AUTHOR = "xiechao"
AUTHOR_EMAIL = "xiechao06@gmail.com"
URL = ""
VERSION = "0.9.0"
DOC = ""


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["test.py"]
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name=NAME,
    version=VERSION,
    long_description=__doc__,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open("requirements.txt").readlines(),
    zip_safe=False,
    tests_require=['pytest', 'mock'],
    cmdclass={'test': PyTest},
)
