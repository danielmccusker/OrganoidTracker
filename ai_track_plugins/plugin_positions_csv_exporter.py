import os
from typing import Tuple, Dict, Any, Iterable, List

from ai_track.core import UserError
from ai_track.core.experiment import Experiment

from ai_track.core.links import Links
from ai_track.core.marker import Marker
from ai_track.core.position import Position
from ai_track.core.position_collection import PositionCollection
from ai_track.core.resolution import ImageResolution
from ai_track.gui import dialog
from ai_track.gui.threading import Task
from ai_track.gui.window import Window
from ai_track.linking_analysis import linking_markers


def get_menu_items(window: Window) -> Dict[str, Any]:
    return {
        "File//Export-Export positions//CSV, as μm coordinates...": lambda: _export_positions_as_csv(window, metadata=False),
        "File//Export-Export positions//CSV, as μm coordinates with metadata...": lambda: _export_positions_as_csv(window, metadata=True),
    }


def _export_positions_as_csv(window: Window, *, metadata: bool):
    experiment = window.get_experiment()
    if not experiment.positions.has_positions():
        raise UserError("No positions are found", "No annotated positions are found. Cannot export anything.")

    folder = dialog.prompt_save_file("Select a directory", [("Folder", "*")])
    if folder is None:
        return
    os.mkdir(folder)
    if metadata:
        cell_types = list(window.get_gui_experiment().get_registered_markers(Position))
        window.get_scheduler().add_task(_AsyncExporter(experiment, cell_types, folder))
    else:
        _write_positions_to_csv(experiment, folder)
        _export_help_file(folder)
        dialog.popup_message("Positions", "Exported all positions, as well as a help file with instructions on how to"
                             " visualize the points in Paraview.")


def _export_help_file(folder: str):
    text = """
Instructions for importing in Paraview
======================================

1. Open Paraview and load the CSV files.
2. Press the green Apply button on the left. A table should appear.
3. Add a TableToPoints filter (Filters > Alphabetical). In the filter properties, set the coords (x, y, z) correctly.
4. Press the green Apply button on the left.
5. Make the filter visible by pressing the eye next to the filter in the Pipeline Browser.
6. Click somewhere in the 3D viewer to select the viewer.
7. In the filter properties, set the filter to be rendered using Points.
8. Set a Point Size of say 40 and set the checkmark next to "Render Points As Spheres"

You will now end up with a nice 3D view of the detected points. To save a movie, use File > Export animation.
"""
    file_name = os.path.join(folder, "How to import to Paraview.txt")
    with open(file_name, "w") as file_handle:
        file_handle.write(text)


def _export_cell_types_file(folder: str, cell_types: List[Marker]):
    """Writes all known cell types and their ids to a file."""
    if len(cell_types) == 0:
        return
    file_name = os.path.join(folder, "Known cell types.txt")
    with open(file_name, "w") as file_handle:
        file_handle.write("Known cell types:\n")
        file_handle.write("=================\n")
        for cell_type in cell_types:
            file_handle.write("* " + cell_type.display_name + " = " + str(hash(cell_type.save_name)))


def _write_positions_to_csv(experiment: Experiment, folder: str):
    resolution = experiment.images.resolution()
    positions = experiment.positions

    file_prefix = experiment.name.get_save_name() + ".csv."
    for time_point in positions.time_points():
        file_name = os.path.join(folder, file_prefix + str(time_point.time_point_number()))
        with open(file_name, "w") as file_handle:
            file_handle.write("x,y,z\n")
            for position in positions.of_time_point(time_point):
                vector = position.to_vector_um(resolution)
                file_handle.write(f"{vector.x},{vector.y},{vector.z}\n")


class _AsyncExporter(Task):
    _positions: PositionCollection
    _links: Links
    _resolution: ImageResolution
    _folder: str
    _save_name: str
    _cell_types: List[Marker]

    def __init__(self, experiment: Experiment, cell_types: List[Marker], folder: str):
        self._positions = experiment.positions.copy()
        self._links = experiment.links.copy()
        self._resolution = experiment.images.resolution()
        self._folder = folder
        self._save_name = experiment.name.get_save_name()
        self._cell_types = cell_types

    def compute(self) -> Any:
        _write_positions_and_metadata_to_csv(self._positions, self._links, self._resolution, self._folder, self._save_name)
        _export_help_file(self._folder)
        _export_cell_types_file(self._folder, self._cell_types)
        return "done"  # We're not using the result

    def on_finished(self, result: Any):
        dialog.popup_message("Positions", "Exported all positions, as well as a help file with instructions on how to"
                                          " visualize the points in Paraview.")


def _write_positions_and_metadata_to_csv(positions: PositionCollection, links: Links, resolution: ImageResolution, folder: str, save_name: str):
    from ai_track.linking_analysis import lineage_id_creator
    from ai_track.position_analysis import cell_density_calculator

    file_prefix = save_name + ".csv."
    for time_point in positions.time_points():
        file_name = os.path.join(folder, file_prefix + str(time_point.time_point_number()))
        with open(file_name, "w") as file_handle:
            file_handle.write("x,y,z,density_mm1,cell_type_id,lineage_id,original_track_id\n")
            positions_of_time_point = positions.of_time_point(time_point)
            for position in positions_of_time_point:
                lineage_id = lineage_id_creator.get_lineage_id(links, position)
                original_track_id = lineage_id_creator.get_original_track_id(links, position)
                cell_type_id = hash(linking_markers.get_position_type(links, position))
                density = cell_density_calculator.get_density_mm1(positions_of_time_point, position, resolution)

                vector = position.to_vector_um(resolution)
                file_handle.write(f"{vector.x},{vector.y},{vector.z},{density},{cell_type_id},"
                                  f"{lineage_id},{original_track_id}\n")


