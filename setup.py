import codecs
import os
from setuptools import setup, find_packages


def read(*parts):
    """文件读取"""
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts)).read()


def find_install_requires():
    """根据'requirements.txt'文件生成‘install_requires‘列表’’"""
    return [x.strip() for x in
            read('requirements.txt').splitlines()
            if x.strip() and not x.startswith('#')]
setup(
    name='cronmon',
    author="Bruce Ye",
    author_email="844928346@qq.com",
    description="Cron jobs monitoring.",
    url="https://cronmon.yoursite.io",
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    exclude_package_data={'':['.gitignore']},
    install_requires=find_install_requires(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3.0 (GNU GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Office/Business',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
