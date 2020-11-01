
import setuptools


setuptools.setup(
    name='pyrobodesk',
    version='0.0.1',
    author='Dorin Clisu',
    author_email='dorin.clisu@gmail.com',
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    license='GNU-GPL-V3',
    description='Desktop GUI Automation Package',
    python_requires='>=3.4',
    install_requires=['pynput', 'pyperclip'],
)
