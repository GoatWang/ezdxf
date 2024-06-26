import ezdxf

# hatch with true color requires DXF R2004 or later
doc = ezdxf.new("R2004")
msp = doc.modelspace()

# important: major axis >= minor axis (ratio <= 1.)
msp.add_ellipse((0, 0), major_axis=(0, 10), ratio=0.5)

hatch = msp.add_hatch()  # use default ACI fill color
hatch.rgb = (211, 40, 215)

# every boundary path is a 2D element
edge_path = hatch.paths.add_edge_path()
# each edge path can contain line arc, ellipse and spline elements
# important: major axis >= minor axis (ratio <= 1.)
edge_path.add_ellipse((0, 0), major_axis=(0, 10), ratio=0.5)

doc.saveas("solid_rgb_hatch.dxf")
