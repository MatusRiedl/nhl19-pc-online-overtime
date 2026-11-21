"""gpuinfo: the graphics card's RTX generation from its name, and what the Picture options it allows (0.99.0)."""
from overtime_roster.app import gpuinfo


def test_rtx_generation_from_the_name():
    assert gpuinfo.rtx_generation('NVIDIA GeForce RTX 5080') == 50
    assert gpuinfo.rtx_generation('NVIDIA GeForce RTX 4070 Laptop GPU') == 40
    assert gpuinfo.rtx_generation('NVIDIA GeForce RTX 3060 Ti') == 30
    assert gpuinfo.rtx_generation('NVIDIA GeForce RTX 2060 SUPER') == 20
    assert gpuinfo.rtx_generation('NVIDIA RTX A4000') == 20     # workstation names: the oldest that runs DLSS
    assert gpuinfo.rtx_generation('NVIDIA GeForce GTX 1080 Ti') == 0
    assert gpuinfo.rtx_generation('AMD Radeon RX 7900 XTX') == 0
    assert gpuinfo.rtx_generation('Intel(R) Arc(TM) A770 Graphics') == 0
    assert gpuinfo.rtx_generation('') == 0


def test_what_each_card_may_run():
    fifty = gpuinfo.info(['NVIDIA GeForce RTX 5080'])
    assert fifty == {'name': 'NVIDIA GeForce RTX 5080', 'rtx': 50, 'dlss': True, 'dlss5': True, 'dlss5_compat': False,
                     'framegen': True}
    thirty = gpuinfo.info(['NVIDIA GeForce RTX 3080'])
    assert thirty['dlss'] and thirty['dlss5'] and thirty['dlss5_compat'] and not thirty['framegen']
    amd = gpuinfo.info(['AMD Radeon RX 6800'])
    assert amd['rtx'] == 0 and not amd['dlss'] and not amd['dlss5'] and amd['name'] == 'AMD Radeon RX 6800'
    assert gpuinfo.info([]) == {'name': '', 'rtx': 0, 'dlss': False, 'dlss5': False, 'dlss5_compat': False,
                                'framegen': False}


def test_of_several_cards_the_newest_rtx_one():
    got = gpuinfo.info(['AMD Radeon(TM) Graphics', 'NVIDIA GeForce RTX 4090', 'NVIDIA GeForce RTX 2070'])
    assert got['name'] == 'NVIDIA GeForce RTX 4090' and got['rtx'] == 40


class FakeReg:
    """winreg's calls gpuinfo makes, over {subkey: DriverDesc}."""
    HKEY_LOCAL_MACHINE = 'HKLM'

    def __init__(self, adapters):
        self.adapters = adapters

    class Key:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def OpenKey(self, parent, sub):
        if parent == self.HKEY_LOCAL_MACHINE:
            assert sub == gpuinfo.CLASS_KEY
            return self.Key('root')
        if sub not in self.adapters:
            raise OSError('no such key')
        return self.Key(sub)

    def EnumKey(self, key, i):
        names = [*self.adapters, 'Properties']
        if i >= len(names):
            raise OSError('no more')
        return names[i]

    def QueryValueEx(self, key, value):
        got = self.adapters[key.name]
        if got is None:
            raise OSError('no value')
        return got, 1


def test_adapter_names_from_the_registry():
    reg = FakeReg({'0000': 'NVIDIA GeForce RTX 5080', '0001': 'Microsoft Basic Display Adapter', '0002': None,
                   '0003': 'NVIDIA GeForce RTX 5080'})
    assert gpuinfo.adapter_names(reg) == ['NVIDIA GeForce RTX 5080', 'Microsoft Basic Display Adapter']
