# Copyright (c) 2024, Manfred Moitzi
# License: MIT License
from __future__ import annotations
from typing import Sequence
import pytest

import math
from ezdxf import loopfinder
from ezdxf.entities import Circle, Arc, Ellipse, LWPolyline, Spline
from ezdxf.math import fit_points_to_cad_cv, Vec2


def test_circle_is_a_closed_entity():
    circle = Circle()
    circle.dxf.radius = 1

    assert loopfinder.is_closed_entity(circle) is True


def test_circle_of_radius_0_is_not_a_closed_entity():
    circle = Circle()
    circle.dxf.radius = 0

    assert loopfinder.is_closed_entity(circle) is False


@pytest.mark.parametrize("start,end", [(0, 180), (0, 0), (180, 180), (360, 360)])
def test_open_arc_is_not_a_closed_entity(start, end):
    arc = Arc()
    arc.dxf.radius = 1
    arc.dxf.start_angle = start
    arc.dxf.end_angle = end

    assert loopfinder.is_closed_entity(arc) is False


@pytest.mark.parametrize("start,end", [(0, 360), (360, 0), (180, -180)])
def test_closed_arc_is_a_closed_entity(start, end):
    arc = Arc()
    arc.dxf.radius = 1
    arc.dxf.start_angle = start
    arc.dxf.end_angle = end

    assert loopfinder.is_closed_entity(arc) is True


@pytest.mark.parametrize(
    "start,end", [(0, math.pi), (0, 0), (math.pi, math.pi), (math.tau, math.tau)]
)
def test_open_ellipse_is_not_a_closed_entity(start, end):
    ellipse = Ellipse()
    ellipse.dxf.major_axis = (1, 0)
    ellipse.dxf.ratio = 1
    ellipse.dxf.start_param = start
    ellipse.dxf.end_param = end

    assert loopfinder.is_closed_entity(ellipse) is False


@pytest.mark.parametrize(
    "start,end", [(0, math.tau), (math.tau, 0), (math.pi, -math.pi)]
)
def test_closed_ellipse_is_a_closed_entity(start, end):
    ellipse = Ellipse()
    ellipse.dxf.major_axis = (1, 0)
    ellipse.dxf.ratio = 1
    ellipse.dxf.start_param = start
    ellipse.dxf.end_param = end

    assert loopfinder.is_closed_entity(ellipse) is True


# Note: Ellipses with major_axis == (0, 0, 0) are not valid.
# They cannot be created by ezdxf and loading such ellipses raises an DXFStructureError.


def test_closed_lwpolyline_is_a_closed_entity():
    polyline = LWPolyline()
    polyline.closed = True
    polyline.append_points([(0, 0), (10, 0), (10, 10)])

    assert loopfinder.is_closed_entity(polyline) is True


def test_open_lwpolyline_is_not_a_closed_entity():
    polyline = LWPolyline()
    polyline.closed = False
    polyline.append_points([(0, 0), (10, 0), (10, 10)])

    assert loopfinder.is_closed_entity(polyline) is False


def test_explicit_closed_lwpolyline_is_a_closed_entity():
    polyline = LWPolyline()
    polyline.closed = False
    polyline.append_points([(0, 0), (10, 0), (10, 10), (0, 0)])

    assert loopfinder.is_closed_entity(polyline) is True


def test_closed_spline():
    ct = fit_points_to_cad_cv([(0, 0), (10, 0), (10, 10), (0, 0)])
    spline = Spline()
    spline.apply_construction_tool(ct)

    assert loopfinder.is_closed_entity(spline) is True


def test_open_spline():
    ct = fit_points_to_cad_cv([(0, 0), (10, 0), (10, 10), (0, 10)])
    spline = Spline()
    spline.apply_construction_tool(ct)

    assert loopfinder.is_closed_entity(spline) is False


def test_empty_spline():
    spline = Spline()

    assert loopfinder.is_closed_entity(spline) is False


class TestEdge:
    def test_init(self):
        edge = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), 1.0)
        assert edge.start == Vec2(0, 0)
        assert edge.end == Vec2(1, 0)
        assert edge.length == 1.0
        assert edge.reverse is False
        assert edge.payload is None

    def test_identity(self):
        edge0 = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), 1.0)
        edge1 = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), 1.0)
        assert edge0 == edge0
        assert edge0 != edge1, "each edge should have an unique identity"
        assert edge0 == edge0.copy(), "copies represent the same edge"
        assert edge0 == edge0.reversed(), "reversed copies represent the same edge"

    def test_copy(self):
        edge = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), 1.0)
        clone = edge.copy()
        assert edge == clone
        assert edge.id == clone.id
        assert edge.start == clone.start
        assert edge.end == clone.end
        assert edge.length == clone.length
        assert edge.reverse is clone.reverse
        assert edge.payload is clone.payload

    def test_reversed_copy(self):
        edge = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), 1.0)
        clone = edge.reversed()
        assert edge == clone
        assert edge.id == clone.id
        assert edge.start == clone.end
        assert edge.end == clone.start
        assert edge.length == clone.length
        assert edge.reverse is (not clone.reverse)
        assert edge.payload is clone.payload


class TestLoop:
    # +-C-+
    # |   |
    # D   B
    # |   |
    # +-A-+

    A = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0))
    B = loopfinder.Edge(Vec2(1, 0), Vec2(1, 1))
    C = loopfinder.Edge(Vec2(1, 1), Vec2(0, 1))
    D = loopfinder.Edge(Vec2(0, 1), Vec2(0, 0))

    def test_is_connected(self):
        loop = loopfinder.Loop((self.A,))
        assert loop.is_connected(self.B) is True

    def test_is_not_connected(self):
        loop = loopfinder.Loop((self.A,))
        assert loop.is_connected(self.C) is False
        assert (
            loop.is_connected(self.D) is False
        ), "should not check reverse connected edges"

    def test_is_closed_loop(self):
        loop = loopfinder.Loop((self.A, self.B, self.C, self.D))
        assert loop.is_closed_loop() is True

    def test_is_not_closed_loop(self):
        loop = loopfinder.Loop((self.A, self.B))
        assert loop.is_closed_loop() is False

    def test_connect_edge(self):
        loop = loopfinder.Loop((self.A,))
        loop2 = loop.connect(self.B)
        assert loop is not loop2
        assert loop.edges is not loop2.edges
        assert len(loop2.edges) == 2

    def test_key(self):
        loop1 = loopfinder.Loop((self.A, self.B, self.C))
        loop2 = loopfinder.Loop((self.B, self.C, self.A))  # rotated edges, same loop

        assert loop1.key() == loop2.key()


def collect_payload(edges: Sequence[loopfinder.Edge]) -> str:
    return ",".join([e.payload for e in edges])


class SimpleLoops:
    #   0   1   2
    # 1 +-C-+-G-+
    #   |   |   |
    #   D   B   F
    #   |   |   |
    # 0 +-A-+-E-+

    A = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), payload="A")
    B = loopfinder.Edge(Vec2(1, 0), Vec2(1, 1), payload="B")
    C = loopfinder.Edge(Vec2(1, 1), Vec2(0, 1), payload="C")
    D = loopfinder.Edge(Vec2(0, 1), Vec2(0, 0), payload="D")
    E = loopfinder.Edge(Vec2(1, 0), Vec2(2, 0), payload="E")
    F = loopfinder.Edge(Vec2(2, 0), Vec2(2, 1), payload="F")
    G = loopfinder.Edge(Vec2(2, 1), Vec2(1, 1), payload="G")


class TestLoopFinderSimple(SimpleLoops):
    def test_unique_available_edges_required(self):
        finder = loopfinder.LoopFinder()
        with pytest.raises(ValueError):
            finder.search(self.A, available=(self.B, self.B, self.B))

    def test_start_edge_not_in_available_edges(self):
        finder = loopfinder.LoopFinder()
        with pytest.raises(ValueError):
            finder.search(self.A, available=(self.A, self.C, self.D))

    def test_loop_A_B_C_D(self):
        finder = loopfinder.LoopFinder()
        finder.search(self.A, (self.B, self.C, self.D))
        solutions = list(finder)
        assert len(solutions) == 1
        assert collect_payload(solutions[0]) == "A,B,C,D"

    def test_loop_D_A_B_C(self):
        finder = loopfinder.LoopFinder()
        finder.search(self.D, (self.A, self.B, self.C))
        solutions = list(finder)
        assert len(solutions) == 1
        assert collect_payload(solutions[0]) == "D,A,B,C"

    def test_loop_A_to_D_unique_solutions(self):
        finder = loopfinder.LoopFinder()
        finder.search(self.A, (self.B, self.C, self.D))
        # rotated edges, same loop
        finder.search(self.D, (self.A, self.B, self.C))
        solutions = list(finder)
        assert len(solutions) == 1

    def test_loops_A_to_G(self):
        finder = loopfinder.LoopFinder()
        finder.search(self.A, (self.B, self.C, self.D, self.E, self.F, self.G))
        solutions = list(finder)
        assert len(solutions) == 2
        assert collect_payload(solutions[0]) == "A,B,C,D"
        assert collect_payload(solutions[1]) == "A,E,F,G,C,D"

    def test_stop_at_first_solution(self):
        finder = loopfinder.LoopFinder(first=True)
        finder.search(self.A, (self.B, self.C, self.D, self.E, self.F, self.G))
        solutions = list(finder)
        assert len(solutions) == 1


class TestAPIFunction(SimpleLoops):
    def test_find_all_loop(self):
        solutions = loopfinder.find_all_loops(
            (self.A, self.B, self.C, self.D, self.E, self.F, self.G)
        )
        assert len(solutions) == 3
        solution_strings = [collect_payload(s) for s in solutions]
        assert "A,B,C,D" in solution_strings
        assert "B,G,F,E" in solution_strings
        assert "A,E,F,G,C,D" in solution_strings

    def test_find_first_loop(self):
        solution = loopfinder.find_first_loop(
            (self.A, self.B, self.C, self.D, self.E, self.F, self.G)
        )
        assert len(solution) >= 4  # any loop is a valid solution

    def test_find_shortest_loop(self):
        solution = loopfinder.find_shortest_loop(
            (self.A, self.B, self.C, self.D, self.E, self.F, self.G)
        )
        assert len(solution) == 4
        assert collect_payload(solution) == "A,B,C,D"

    def test_find_longest_loop(self):
        solution = loopfinder.find_longest_loop(
            (self.A, self.B, self.C, self.D, self.E, self.F, self.G)
        )
        assert len(solution) == 6
        assert collect_payload(solution) == "A,E,F,G,C,D"


class TestFindAllDisconnectedLoops:
    #   0   1   2   3
    # 1 +-C-+   +-G-+
    #   |   |   |   |
    #   D   B   H   F
    #   |   |   |   |
    # 0 +-A-+   +-E-+

    A = loopfinder.Edge(Vec2(0, 0), Vec2(1, 0), payload="A")
    B = loopfinder.Edge(Vec2(1, 0), Vec2(1, 1), payload="B")
    C = loopfinder.Edge(Vec2(1, 1), Vec2(0, 1), payload="C")
    D = loopfinder.Edge(Vec2(0, 1), Vec2(0, 0), payload="D")
    E = loopfinder.Edge(Vec2(2, 0), Vec2(3, 0), payload="E")
    F = loopfinder.Edge(Vec2(3, 0), Vec2(3, 1), payload="F")
    G = loopfinder.Edge(Vec2(3, 1), Vec2(2, 1), payload="G")
    H = loopfinder.Edge(Vec2(2, 1), Vec2(2, 0), payload="H")

    def test_find_all_loops(self):
        solutions = loopfinder.find_all_loops(
            (self.A, self.B, self.C, self.D, self.E, self.F, self.G, self.H)
        )
        assert len(solutions) == 2
        solution_strings = [collect_payload(s) for s in solutions]
        assert "A,B,C,D" in solution_strings
        assert "E,F,G,H" in solution_strings

    def test_find_all_shuffled_loops(self):
        solutions = loopfinder.find_all_loops(
            (self.H, self.B, self.F, self.D, self.E, self.C, self.G, self.A)
        )
        assert len(solutions) == 2
        solution_strings = [collect_payload(s) for s in solutions]
        assert "B,C,D,A" in solution_strings
        assert "H,E,F,G" in solution_strings


if __name__ == "__main__":
    pytest.main([__file__])