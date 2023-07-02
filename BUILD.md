git clone https://github.com/pyinstaller/pyinstaller

cd pyinstaller, then cd bootloader

Run python3 ./waf distclean all to build the bootloader for your system.

Once the bootloader has been built, in the pyinstaller directory type in: pip install .

Use the command pyinstaller --noconfirm build.spec from cleoenvia/
