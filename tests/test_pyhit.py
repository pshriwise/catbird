import pytest

pytest.importorskip('pyhit')

from catbird import AppManager

def test_pyhit_node(request):
    json_file = request.fspath.dirpath() / 'openmc.json'
    app = AppManager.from_json(json_file)

    omc = app['problems']['OpenMCCellAverageProblem']()

    node = omc.to_node()

    assert node.name == 'OpenMCCellAverageProblem'