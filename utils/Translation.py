from numpy import array

from factory.geometry_factory.geometry_factory import GeometryFactory


def translate_fiber(fiber, bbox, translation):
    anchors = fiber.get_anchors()
    t_anchors = []
    t_bbox = []
    for anchor in anchors:
        t_anchors.append((array(anchor) + array(translation)).tolist())
    if len(bbox) > 0:
        for pt in bbox:
            t_bbox.append((array(pt) + array(translation)).tolist())

    return t_bbox, GeometryFactory.create_fiber(
        fiber.get_radius(),
        fiber.get_symmetry(),
        fiber.get_sampling(),
        t_anchors
    )
