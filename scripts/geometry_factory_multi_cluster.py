#!/usr/bin/env python3

import argparse
import pathlib
from math import pi
from tempfile import mkdtemp

from simulator.factory import GeometryFactory, Plane

resolution = [10, 10, 10]
spacing = [2, 2, 2]

spheres_center = [[-2, 7, 10], [2, -1, 11]]
sphere_radius = 5

n_point_per_centroid = 5
bundle_radius = 4
bundle_symmetry = 1
bundle_n_fibers1, bundle_n_fibers2 = 1000, 4000
bundle_limits = [[0, 1], [0, 1], [0, 1]]
bundle_center = [0, 0, 0]
world_center = [5, 5, 5]

base_anchors = [
    [0.5, -0.3, 0.5],
    [0.5, -0.2, 0.5],
    [0.5, -0.1, 0.5],
    [0.5, 0, 0.5],
    [0.5, 0.1, 0.5],
    [0.5, 0.2, 0.5],
    [0.5, 0.3, 0.5],
    [0.5, 0.4, 0.5],
    [0.5, 0.5, 0.5],
    [0.5, 0.6, 0.5],
    [0.5, 0.7, 0.5],
    [0.5, 0.8, 0.5],
    [0.5, 0.9, 0.5],
    [0.5, 1.1, 0.5],
    [0.5, 1.2, 0.5],
    [0.5, 1.3, 0.5],
    [0.5, 1.4, 0.5],
]


def run_multi_clusters(output_folder: pathlib.Path, output_naming: str):
    geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

    bundle1 = GeometryFactory.create_bundle(
        bundle_radius, bundle_symmetry, n_point_per_centroid, base_anchors
    )
    _, bundle2 = GeometryFactory.rotate_bundle(
        bundle1, [0.5, 0.5, 0.5], pi / 6.0, Plane.YZ
    )

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(
            3, bundle_n_fibers1, 1, bundle_center, bundle_limits
        ),
        [bundle1, bundle2],
        world_center,
    )

    geometry_handler.add_cluster(cluster)

    cluster = GeometryFactory.create_cluster(
        GeometryFactory.create_cluster_meta(
            3, bundle_n_fibers2, 1, bundle_center, bundle_limits
        ),
        [bundle1, bundle2],
        world_center,
    )

    geometry_handler.add_cluster(cluster)

    sphere_1 = GeometryFactory.create_sphere(sphere_radius, spheres_center[0])
    sphere_2 = GeometryFactory.create_sphere(sphere_radius, spheres_center[1])

    geometry_handler.add_sphere(sphere_1)
    geometry_handler.add_sphere(sphere_2)

    return geometry_handler.generate_json_configuration_files(
        output_naming, output_folder
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Geometry Multi Clusters Example Script")
    parser.add_argument(
        "--out", type=pathlib.Path, help="Output directory for the files"
    )

    args = parser.parse_args()
    if args.out:
        dest: pathlib.Path = args.out
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest = pathlib.Path(mkdtemp(prefix="geo_factory_mc"))

    print("Script execution results are in : {}".format(dest))
    run_multi_clusters(dest, "multi_clusters")
