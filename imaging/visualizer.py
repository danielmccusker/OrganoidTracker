from imaging import Experiment, Particle
from matplotlib.figure import Figure, Axes
from matplotlib.backend_bases import KeyEvent, MouseEvent
from typing import Iterable, Optional
import matplotlib.pyplot as plt


class Visualizer:
    """A complete application for visualization of an experiment"""
    _experiment: Experiment

    _fig: Figure
    _ax: Axes

    _key_handler_id: int
    _mouse_handler_id: int

    def __init__(self, experiment: Experiment, figure: Figure):
        self._experiment = experiment
        self._fig = figure
        self._ax = self._fig.gca()
        self._key_handler_id = self._fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self._mouse_handler_id = self._fig.canvas.mpl_connect("button_press_event", self._on_mouse_click)

    def _clear_axis(self):
        """Clears the axis, except that zoom settings are preserved"""
        xlim, ylim = self._ax.get_xlim(), self._ax.get_ylim()
        self._ax.clear()
        if xlim[1] - xlim[0] > 2:
            # Only preserve scale if some sensible value was recorded
            self._ax.set_xlim(*xlim)
            self._ax.set_ylim(*ylim)
            self._ax.set_autoscale_on(False)

    def draw_view(self):
        print("Override this method to draw the view.")

    def _on_key_press(self, event: KeyEvent):
        pass

    def _on_mouse_click(self, event: MouseEvent):
        pass

    def detach(self):
        self._fig.canvas.mpl_disconnect(self._key_handler_id)
        self._fig.canvas.mpl_disconnect(self._mouse_handler_id)

    @staticmethod
    def get_closest_particle(particles: Iterable[Particle], x: int, y: int, z: Optional[int], max_distance: int = 100000):
        """Gets the particle closest ot the given position."""
        search_position = Particle(x, y, z)
        closest_particle = None
        closest_distance_squared = max_distance ** 2

        for particle in particles:
            if z is None:
                search_position.z = particle.z # Make search ignore z
            distance = particle.distance_squared(search_position)
            if distance < closest_distance_squared:
                closest_distance_squared = distance
                closest_particle = particle

        return closest_particle


_visualizer = None # Reference to prevent event handler from being garbage collected

def visualize(experiment: Experiment):
    pass

def _configure_matplotlib():
    plt.rcParams['keymap.forward'] = []
    plt.rcParams['keymap.back'] = ['backspace']

def activate(visualizer: Visualizer) -> None:
    _configure_matplotlib()

    global _visualizer
    if _visualizer is not None:
        # Unregister old event handlers
        _visualizer.detach()

    _visualizer = visualizer
    _visualizer.draw_view()

