# Copyright (c) 2023, Manfred Moitzi
# License: MIT License
# mypy: ignore_errors=True
from __future__ import annotations
import os
import time

from ezdxf.math import BoundingBox2d, Matrix44
from ezdxf.addons.xqt import QtWidgets, QtGui
from ezdxf.addons.drawing.qtviewer import CADGraphicsView
from ezdxf.addons.drawing.pyqt import PyQtPlaybackBackend
from ezdxf.addons import xplayer
from . import api

VIEWER_NAME = "HPGL/2 Viewer"


class HPGL2Widget(QtWidgets.QWidget):
    def __init__(self, view: CADGraphicsView) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        self.setLayout(layout)
        self._view = view
        self._view.closing.connect(self.close)
        self._player: api.Player | None = None
        self._reset_backend()

    def _reset_backend(self) -> None:
        self._backend = PyQtPlaybackBackend()

    @property
    def view(self) -> CADGraphicsView:
        return self._view

    @property
    def player(self) -> api.Player:
        return self._player.copy()

    def plot(self, data: bytes, reset_view: bool = True) -> None:
        self._reset_backend()
        self._player: api.Player = api.record_plotter_output(
            data, 0, 1.0, 1.0, api.MergeControl.AUTO
        )
        self._view.begin_loading()
        new_scene = QtWidgets.QGraphicsScene()
        self._backend.set_scene(new_scene)
        xplayer.hpgl2_to_drawing(self._player, self._backend)
        self._backend.finalize()
        self._view.end_loading(new_scene)
        self._view.buffer_scene_rect()
        if reset_view:
            self._view.fit_to_scene()


SPACING = 20


class HPGL2Viewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._cad = HPGL2Widget(CADGraphicsView())
        self._view = self._cad.view
        self._player: api.Player | None = None
        self._bbox: BoundingBox2d = BoundingBox2d()

        self.page_size_label = QtWidgets.QLabel("Page Size: 0x0mm")
        self.scaling_factor_line_edit = QtWidgets.QLineEdit("1")
        self.dpi_line_edit = QtWidgets.QLineEdit("72")
        self.png_size_label = QtWidgets.QLabel("PNG Size: 0x0px")

        self.scaling_factor_line_edit.editingFinished.connect(self.update_sidebar)
        self.dpi_line_edit.editingFinished.connect(self.update_sidebar)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        layout.addWidget(self._cad)
        sidebar = self.make_sidebar()
        layout.addWidget(sidebar)
        self.setWindowTitle(VIEWER_NAME)
        self.resize(1600, 900)
        self.show()

    def make_sidebar(self) -> QtWidgets.QWidget:
        sidebar = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setContentsMargins(SPACING // 2, 0, SPACING // 2, 0)
        sidebar.setLayout(v_layout)

        policy = QtWidgets.QSizePolicy()
        policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Fixed)
        sidebar.setSizePolicy(policy)

        open_button = QtWidgets.QPushButton("Open HPGL/2 File")
        open_button.clicked.connect(self.select_plot_file)
        v_layout.addWidget(open_button)
        v_layout.addWidget(self.page_size_label)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(QtWidgets.QLabel("Scaling Factor:"))
        h_layout.addWidget(self.scaling_factor_line_edit)
        v_layout.addLayout(h_layout)

        v_layout.addSpacing(SPACING)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(QtWidgets.QLabel("DPI (PNG only):"))
        h_layout.addWidget(self.dpi_line_edit)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.png_size_label)

        export_png_button = QtWidgets.QPushButton("Export PNG")
        export_png_button.clicked.connect(self.export_png)
        export_png_button.setDisabled(True)
        v_layout.addWidget(export_png_button)

        export_svg_button = QtWidgets.QPushButton("Export SVG")
        export_svg_button.clicked.connect(self.export_svg)
        v_layout.addWidget(export_svg_button)

        export_pdf_button = QtWidgets.QPushButton("Export PDF")
        export_pdf_button.clicked.connect(self.export_pdf)
        export_pdf_button.setDisabled(True)
        v_layout.addWidget(export_pdf_button)

        export_dxf_button = QtWidgets.QPushButton("Export DXF")
        export_dxf_button.clicked.connect(self.export_dxf)
        export_dxf_button.setDisabled(True)
        v_layout.addWidget(export_dxf_button)

        v_layout.addSpacing(SPACING)

        reset_button = QtWidgets.QPushButton("Reset")
        reset_button.clicked.connect(self.reset_values)
        v_layout.addWidget(reset_button)
        return sidebar

    def load_plot_file(self, path: str | os.PathLike) -> None:
        try:
            with open(path, "rb") as fp:
                data = fp.read()
            self.set_plot_data(data, path)
        except IOError as e:
            QtWidgets.QMessageBox.critical(self, "Loading Error", str(e))

    def select_plot_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption="Select HPGL/2 Plot File",
            filter="Plot Files (*.plt)",
        )
        if path:
            self.load_plot_file(path)

    def set_plot_data(self, data: bytes, filename: str) -> None:
        try:
            self._cad.plot(data)
        except api.Hpgl2Error:
            # TODO: show MessageBox
            msg = f"cannot load HPGL/2 file: {filename}"
            print(msg)
            return
        self._player = self._cad.player
        self._bbox = self._player.bbox()
        self.update_sidebar()
        self.setWindowTitle(f"{VIEWER_NAME} - " + str(filename))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self._view.fit_to_scene()

    def get_scale(self) -> float:
        try:
            return float(self.scaling_factor_line_edit.text())
        except ValueError:
            return 1.0

    def get_page_size(self) -> tuple[int, int]:
        factor = self.get_scale()
        x = 0
        y = 0
        if self._bbox.has_data:
            size = self._bbox.size
            # 40 plot units = 1mm
            x = round(size.x / 40 * factor)
            y = round(size.y / 40 * factor)
        return x, y

    def get_pixel_size(self) -> tuple[int, int]:
        try:
            dpi = int(self.dpi_line_edit.text())
        except ValueError:
            dpi = 72
        x, y = self.get_page_size()
        return round(x / 25.4 * dpi), round(y / 25.4 * dpi)

    def update_sidebar(self):
        x, y = self.get_page_size()
        self.page_size_label.setText(f"Page Size: {x}x{y}mm")
        px, py = self.get_pixel_size()
        self.png_size_label.setText(f"PNG Size: {px}x{py}px")

    def reset_values(self):
        self.scaling_factor_line_edit.setText("1")
        self.dpi_line_edit.setText("72")
        self.update_sidebar()

    def export_svg(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="Save SVG File",
            filter="SVG Files (*.svg)",
        )
        if not path:
            return
        try:
            t0 = time.perf_counter()
            with open(path, "wt") as fp:
                fp.write(self.make_svg_string())
            print(f"successful SVG export in {time.perf_counter()-t0:.2f} seconds")
        except IOError as e:
            # TODO: show MessageBox
            print(str(e))

    def make_svg_string(self) -> str:
        player = self._player.copy()
        scale = self.get_scale()
        m = Matrix44.scale(scale, scale, 1)
        player.transform(m)
        svg_backend = api.SVGBackend(player.bbox())
        player.replay(svg_backend)
        del player
        return svg_backend.get_string()

    def export_pdf(self) -> None:
        print("export HPGL/2 plot file as PDF")

    def export_png(self) -> None:
        print("export HPGL/2 plot file as PNG")

    def export_dxf(self) -> None:
        print("export HPGL/2 plot file as DXF")