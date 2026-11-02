#!/usr/bin/env python3
"""CI helper: OS.raw and SYSTEMOS.dmg from the board IPSW, for make-virt-root.py.

Downloads are handled outside (curl). This script extracts the OS and Cryptex1,SystemOS
members through the UniXNU Ipsw machinery (sha256 pins of board.toml apply), expands the
UDIF OS image to a raw GPT+APFS disk (OS.raw) and copies the SystemOS cryptex member as is
(a raw APFS container already).
"""
import shutil
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'UniXNU' / 'scripts'))
from unixnu.ipsw import Ipsw  # noqa: E402
from unixnu import udif  # noqa: E402


class Ctx:
    def __init__(self):
        self.board = tomllib.load(open('device/board.toml', 'rb'))
        self.out_root = Path('out')

    @staticmethod
    def option_text(*names):
        return 'ipsw.ipsw'


def main():
    ipsw = Ipsw(Ctx())
    os_dmg = ipsw.disk_image('OS')
    systemos = ipsw.disk_image('Cryptex1,SystemOS')
    image = udif.Image(os_dmg)
    with open('OS.raw', 'wb') as raw:
        for block in image.blocks():
            raw.write(block)
    shutil.copyfile(systemos, 'SYSTEMOS.dmg')
    for name in ('OS.raw', 'SYSTEMOS.dmg'):
        path = Path(name)
        print(f'{name}: {path.stat().st_size} bytes')


if __name__ == '__main__':
    main()
