# Copyright (c) 2018-2019 Manfred Moitzi
# License: MIT License
import os
import pytest
import ezdxf


@pytest.fixture(params=["AC1009", "AC1015"])
def dxfversion(request):
    return request.param


POINTS = [
    (323380.91750022338, 5184999.7255775109, 0.0),
    (323377.13033454702, 5184994.8609992303, 0.0),
    (323375.96284645743, 5184992.1182727059, 0.0),
    (323374.72169714782, 5184989.8344467692, 0.0),
    (323374.17676884111, 5184988.5392300664, 0.0),
    (323373.39893951337, 5184986.7871434148, 0.0),
    (323372.92717616714, 5184984.9566230336, 0.0),
    (323372.37727835565, 5184982.897411068, 0.0),
    (323371.90899244603, 5184981.601685036, 0.0),
    (323375.99291780719, 5184981.3014478451, 0.0),
    (323375.99841245974, 5184977.7365302956, 0.0),
    (323377.32736607571, 5184977.6150565967, 0.0),
    (323377.76792070246, 5184970.3801041171, 0.0),
    (323378.56378788338, 5184967.413698026, 0.0),
    (323379.38490772923, 5184964.9500029553, 0.0),
]


def test_entities_iterator(dxfversion, tmpdir):
    filename = tmpdir.join("polyline_{}.dxf".format(dxfversion))
    filename = str(filename)
    drawing = ezdxf.new(dxfversion)
    modelspace = drawing.modelspace()
    modelspace.add_polyline3d(POINTS)
    drawing.saveas(filename)

    assert os.path.exists(filename)

    dxf = ezdxf.readfile(filename)
    for entity in dxf.entities:
        if entity.dxftype() == "POLYLINE":  # iterator ok
            points = list(entity.points())
            assert len(points) == len(POINTS)
