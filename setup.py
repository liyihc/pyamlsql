from setuptools import setup, find_packages

# pyinstaller
# 可参考https://github.com/pyinstaller/pyinstaller-hooks-contrib
# 其实就是entrypoint，在哪里定义都行
setup(
    name="pyamlsql",
    version="0.1.1",
    description="",
    packages=find_packages(),
    python_requires=">=3.6, <4",
    install_requires=[ ]
)
