from typing import Optional, Set

from matplotlib.backend_bases import KeyEvent

from ai_track.core import TimePoint
from ai_track.core.position import Position
from ai_track.gui.window import Window
from ai_track.linking_analysis import lineage_error_finder
from ai_track.visualizer import activate
from ai_track.visualizer.exitable_image_visualizer import ExitableImageVisualizer


class LineageErrorsVisualizer(ExitableImageVisualizer):
    """Viewer to detect errors in lineages. All cells with a gray marker have potential errors in them. Hover your mouse
    over a cell and press E to dismiss or correct the errors in that lineage."""

    _verified_lineages: Set[Position] = set()

    def _on_key_press(self, event: KeyEvent):
        if event.key == "l":
            self._exit_view()
        elif event.key == "e":
            position = self._get_position_at(event.xdata, event.ydata)
            self._show_linking_errors(position)
        else:
            super()._on_key_press(event)

    def _move_in_time(self, dt: int):
        # Rendering this view is quite slow, so it is better to exit this view instead of rerendering it for another
        # time point
        try:
            self._display_settings.time_point = self._experiment.get_time_point(
                self._display_settings.time_point.time_point_number() + dt)
            self._exit_view()
        except ValueError:
            pass  # Time point doesn't exit

    def _exit_view(self):
        from ai_track.visualizer.link_and_position_editor import LinkAndPositionEditor
        image_visualizer = LinkAndPositionEditor(self._window)
        activate(image_visualizer)

    def _show_linking_errors(self, position: Optional[Position] = None):
        from ai_track.visualizer.errors_visualizer import ErrorsVisualizer
        warnings_visualizer = ErrorsVisualizer(self._window, position)
        activate(warnings_visualizer)

    def _load_time_point(self, time_point: TimePoint):
        super()._load_time_point(time_point)

        # Check what lineages contain errors
        links = self._experiment.links
        if not links.has_links():
            self._verified_lineages = set()
            return

        positions = self._experiment.positions.of_time_point(time_point)
        lineages_with_errors = lineage_error_finder.get_problematic_lineages(links, positions,
                                    min_time_point=self._display_settings.error_correction_min_time_point,
                                    max_time_point=self._display_settings.error_correction_max_time_point)
        verified_lineages = set()
        for position in positions:
            if not links.contains_position(position):
                continue
            if lineage_error_finder.find_lineage_index_with_crumb(lineages_with_errors, position) is None:
                verified_lineages.add(position)
        self._verified_lineages = verified_lineages

    def _on_position_draw(self, position: Position, color: str, dz: int, dt: int) -> bool:
        if dt != 0 or abs(dz) > 3:
            return super()._on_position_draw(position, color, dz, dt)

        verified = position in self._verified_lineages
        color = color if verified else "gray"
        self._draw_selection(position, color)
        return super()._on_position_draw(position, color, dz, dt)
