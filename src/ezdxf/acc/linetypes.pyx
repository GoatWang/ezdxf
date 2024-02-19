# cython: language_level=3
# distutils: language = c++
# Copyright (c) 2022-2024, Manfred Moitzi
# License: MIT License
from typing import Iterator, TYPE_CHECKING, Sequence
import cython
from .vector cimport Vec3, v3_isclose, v3_sub, v3_add, v3_mul, v3_magnitude

if TYPE_CHECKING:
    from ezdxf.math import UVec

LineSegment = tuple[Vec3, Vec3]

cdef extern from "constants.h":
    const double ABS_TOL
    const double REL_TOL
    const int MAX_DASH_ITEMS

cdef class _LineTypeRenderer:
    cdef double[MAX_DASH_ITEMS] _dashes
    cdef int _dash_count
    cdef readonly bint is_solid
    cdef bint _is_dash
    cdef int _current_dash
    cdef double _current_dash_length

    def __init__(self, dashes: Sequence[float]):
        cdef list _dashes = list(dashes)
        cdef int i

        self._dash_count = min(len(_dashes), MAX_DASH_ITEMS)
        for i in range(self._dash_count):
            self._dashes[i] = _dashes[i]

        self.is_solid = True
        self._is_dash = False
        self._current_dash = 0
        self._current_dash_length = 0.0

        if self._dash_count > 1:
            self.is_solid = False
            self._current_dash_length = self._dashes[0]
            self._is_dash = True

    def line_segment(self, start: UVec, end: UVec) -> Iterator[LineSegment]:
        cdef Vec3 v3_start = Vec3(start)
        cdef Vec3 v3_end = Vec3(end)
        cdef Vec3 segment_vec, segment_dir
        cdef double segment_length, dash_length
        cdef list dashes = []

        if self.is_solid or v3_isclose(v3_start, v3_end, REL_TOL, ABS_TOL):
            yield v3_start, v3_end
            return

        segment_vec = v3_sub(v3_end, v3_start)
        segment_length = v3_magnitude(segment_vec)
        with cython.cdivision:
            segment_dir = v3_mul(segment_vec, 1.0 / segment_length)  # normalize

        self._render_dashes(segment_length, dashes)
        for dash_length in dashes:
            v3_end = v3_add(v3_start, v3_mul(segment_dir, abs(dash_length)))
            if dash_length > 0:
                yield v3_start, v3_end
            v3_start = v3_end

    cdef _render_dashes(self, double length, list dashes):
        if length <= self._current_dash_length:
            self._current_dash_length -= length
            dashes.append(length if self._is_dash else -length)
            if self._current_dash_length < ABS_TOL:
                self._cycle_dashes()
        else:
            # Avoid deep recursions!
            while length > self._current_dash_length:
                length -= self._current_dash_length
                self._render_dashes(self._current_dash_length, dashes)
            if length > 0.0:
                self._render_dashes(length, dashes)

    cdef _cycle_dashes(self):
        with cython.cdivision:
            self._current_dash = (self._current_dash + 1) % self._dash_count
        self._current_dash_length = self._dashes[self._current_dash]
        self._is_dash = not self._is_dash
