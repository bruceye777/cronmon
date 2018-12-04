import codecs
import os
from setuptools import setup


def read(*parts):
    """文件读取"""
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts)).read()


def find_install_requires():
    """根据'requirements.txt'文件生成‘install_requires‘列表’’"""
    return [x.strip() for x in
            read('requirements.txt').splitlines()
            if x.strip() and not x.startswith('#')]


def package_files(directory):
    """循环生成package_data文件列表"""
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

extra_files = package_files('cronmon')

setup(
    name='cronmonweb',
    author="Bruce Ye",
    author_email="844928346@qq.com",
    description="Cron jobs monitoring.",
    url="https://github.com/bruceye777/cronmon",
    version='0.1.0',
    packages=['.','cronmon'],
    package_data = {'.': ['cron.py','manage.py','migrate.py','cronmon.ini'],'cronmon':extra_files},
    zip_safe=False,
    exclude_package_data={'':['.gitignore']},
    install_requires=find_install_requires(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
        'Topic :: Office/Business',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
