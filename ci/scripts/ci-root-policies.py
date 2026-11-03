#!/usr/bin/env python3
"""CI helper: OS.raw and SYSTEMOS.dmg from the board IPSW, for make-virt-root.py.

Extracts the OS and Cryptex1,SystemOS members through the UniXNU Ipsw machinery
(the sha256 pins of board.toml apply), then expands the UDIF OS image to the raw
disk with scripts/udif-expand.py (the canonical expansion the root policies are
checked against: sha256 e5634d04..., 6077580800 bytes; hdiutil convert produced
a different image) and copies the SystemOS cryptex member as is (it is already
a raw APFS container).
"""
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'UniXNU' / 'scripts'))
from unixnu.ipsw import Ipsw  # noqa: E402

OS_RAW_SHA256 = 'e5634d04a8ac35f024845f583394e0a35deb26a04cb0c00286a8674e25a9a4f2'
OS_RAW_BYTES = 6077580800


class Ctx:
    def __init__(self):
        self.board = tomllib.load(open('device/board.toml', 'rb'))
        self.out_root = Path('out')

    @staticmethod
    def option_text(*names):
        return 'ipsw.ipsw'


def main():
    ipsw = Ipsw(Ctx())
    os_dmg = ipsw.extract('OS')
    systemos = ipsw.extract('Cryptex1,SystemOS')
    # scripts/udif-expand.py loads liblzfse through ctypes.util.find_library, which does not
    # see Homebrew's keg on the macOS runner: rewrite its loader line with the brew paths.
    source = Path('scripts/udif-expand.py').read_text()
    needle = "library = ctypes.util.find_library('lzfse') or 'liblzfse.so'"
    if needle not in source:
        raise SystemExit('scripts/udif-expand.py no longer has the expected lzfse loader line')
    loader = ("library = next((p for p in ('/opt/homebrew/lib/liblzfse.dylib', '/usr/local/lib/liblzfse.dylib',"
              " '/opt/homebrew/opt/lzfse/lib/liblzfse.dylib') if Path(p).exists()), 'liblzfse.so')")
    patched = Path('udif-expand-ci.py')
    patched.write_text(source.replace(needle, loader))
    subprocess.run([sys.executable, str(patched), str(os_dmg), 'OS.raw', '--sha256', OS_RAW_SHA256], check=True)
    size = Path('OS.raw').stat().st_size
    if size != OS_RAW_BYTES:
        raise SystemExit(f'OS.raw is {size} bytes, expected {OS_RAW_BYTES}')
    shutil.copyfile(systemos, 'SYSTEMOS.dmg')
    for name in ('OS.raw', 'SYSTEMOS.dmg'):
        print(f'{name}: {Path(name).stat().st_size} bytes')


if __name__ == '__main__':
    main()
