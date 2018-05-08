import cv2

import numpy
from numpy import ndarray
from matplotlib.backend_bases import KeyEvent

from gui import Window, dialog
from particle_detection import thresholding, watershedding, missed_cell_finder
from segmentation import iso_intensity_curvature
from segmentation.iso_intensity_curvature import ImageDerivatives
from visualizer import activate, DisplaySettings
from visualizer.image_visualizer import AbstractImageVisualizer


class DetectionVisualizer(AbstractImageVisualizer):
    """Visualizer specialized in displaying particle positions.
    """

    threshold_block_size = 51
    sampling = (2, 0.32, 0.32)
    minimal_size = (3, 11, 11)
    distance_transform_smooth_size = 21

    color_map = "gray"

    def __init__(self, window: Window, time_point_number: int, z: int, display_settings: DisplaySettings):
        display_settings.show_next_time_point = False
        display_settings.show_shapes = False
        super().__init__(window, time_point_number, z, display_settings)

    def _draw_image(self):
        if self._time_point_images is not None:
            self._ax.imshow(self._time_point_images[self._z], cmap=self.color_map)

    def _get_window_title(self) -> str:
        return "Cell detection"

    def get_extra_menu_options(self):
        return {
            **super().get_extra_menu_options(),
            "View": [
                ("Show original images (T)", self.refresh_view),
                "-",
                ("Exit this view (/exit)", self._show_main_view)
            ],
            "Threshold": [
                ("Show basic threshold", self._basic_threshold),
                ("Add iso-intensity segmentation", self._segment_using_iso_intensity),
                ("Show advanced threshold (T)", self._advanced_threshold)
            ],
            "Detection": [
                ("Detect cells", self._detect_cells),
                ("Detect cells using existing points", self._detect_cells_using_particles),
                ("Detect contours", self._detect_contours),
            ]
        }

    def _on_command(self, command: str):
        if command == "exit":
            self._show_main_view()
            return True
        if command == "help":
            self._update_status("Available commands:\n"
                               "/exit - Return to main view\.n"
                               "/t30 - Jump to time point 30. Also works for other time points.")

        return super()._on_command(command)

    def _show_main_view(self):
        from visualizer.image_visualizer import StandardImageVisualizer
        v = StandardImageVisualizer(self._window, self._time_point.time_point_number(), self._z, self._display_settings)
        activate(v)

    def _basic_threshold(self):
        images = self._experiment.get_image_stack(self._time_point)
        if images is None:
            dialog.popup_error("Failed to apply threshold", "Cannot show threshold - no images loaded.")
            return
        images = thresholding.image_to_8bit(images)
        out = numpy.empty_like(images, dtype=numpy.uint8)
        thresholding.adaptive_threshold(images, out, self.threshold_block_size)

        self._time_point_to_rgb()
        self._time_point_images[:, :, :, 1] = out
        self._time_point_images[:, :, :, 2] = out
        self.draw_view()

    def _advanced_threshold(self):
        images = self._get_8bit_images()
        if images is None:
            dialog.popup_error("Failed to apply threshold", "Cannot show threshold - no images loaded.")
            return
        threshold = numpy.empty_like(images, dtype=numpy.uint8)
        thresholding.advanced_threshold(images, threshold, self.threshold_block_size)

        self._time_point_to_rgb()
        self._time_point_images[:, :, :, 1] = threshold
        self._time_point_images[:, :, :, 2] = threshold
        self.draw_view()

    def _get_8bit_images(self):
        images = self._experiment.get_image_stack(self._time_point)
        if images is not None:
            return thresholding.image_to_8bit(images)
        return None

    def _draw_images(self, image_stack: ndarray, color_map=None):
        self._time_point_images = image_stack
        self.color_map = color_map if color_map is not None else DetectionVisualizer.color_map
        self.draw_view()

    def _detect_cells(self):
        self.refresh_view()
        images = self._get_8bit_images()
        if images is None:
            dialog.popup_error("Failed to detect cells", "Cannot detect cells - no images loaded.")
            return

        threshold = numpy.empty_like(images, dtype=numpy.uint8)
        thresholding.advanced_threshold(images, threshold, self.threshold_block_size)
        self._draw_images(threshold)

        distance_transform = numpy.empty_like(images, dtype=numpy.float64)
        watershedding.distance_transform(threshold, distance_transform, self.sampling)
        self._draw_images(distance_transform)

        watershed = watershedding.watershed_maxima(threshold, distance_transform, self.minimal_size)
        self._draw_images(watershed, watershedding.COLOR_MAP)
        self._print_missed_cells(watershed)

    def _detect_cells_using_particles(self):
        if len(self._time_point.particles()) == 0:
            dialog.popup_error("Failed to detect cells", "Cannot detect cells - no particle positions loaded.")
            return
        images = self._get_8bit_images()
        if images is None:
            dialog.popup_error("Failed to detect cells", "Cannot detect cells - no images loaded.")
            return

        self.refresh_view()

        threshold = numpy.empty_like(images, dtype=numpy.uint8)
        thresholding.advanced_threshold(images, threshold, self.threshold_block_size)
        self._draw_images(threshold)

        # Labelling, calculate distance to label
        labels = numpy.empty_like(images, dtype=numpy.uint16)
        watershedding.create_labels(self._time_point.particles(), labels)
        distance_transform_to_labels = self._get_distances_to_labels(images, labels)

        # Distance transform to edge and labels
        distance_transform = numpy.empty_like(images, dtype=numpy.float64)
        watershedding.distance_transform(threshold, distance_transform, self.sampling)
        watershedding.smooth(distance_transform, self.distance_transform_smooth_size)
        distance_transform += distance_transform_to_labels
        self._draw_images(distance_transform)

        watershed = watershedding.watershed_labels(threshold, distance_transform.max() - distance_transform, labels)
        watershedding.remove_big_labels(watershed)
        self._draw_images(watershed, watershedding.COLOR_MAP)
        self._print_missed_cells(watershed)

    def _get_distances_to_labels(self, images, labels):
        labels_inv = numpy.full_like(images, 255, dtype=numpy.uint8)
        labels_inv[labels != 0] = 0
        distance_transform_to_labels = numpy.empty_like(images, dtype=numpy.float64)
        watershedding.distance_transform(labels_inv, distance_transform_to_labels, self.sampling)
        distance_transform_to_labels[distance_transform_to_labels > 4] = 4
        distance_transform_to_labels = 4 - distance_transform_to_labels
        return distance_transform_to_labels

    def _detect_contours(self):
        self.refresh_view()
        images = self._get_8bit_images()
        if images is None:
            dialog.popup_error("Failed to detect cells", "Cannot detect cells - no images loaded.")
            return

        threshold = numpy.empty_like(images, dtype=numpy.uint8)
        thresholding.advanced_threshold(images, threshold, self.threshold_block_size)
        self._draw_images(threshold)

        im2, contours, hierarchy = cv2.findContours(threshold[self._z], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        threshold[self._z] = 0
        for contour in contours:
            cv2.drawContours(threshold[self._z], [contour], 0, 255, 2)
        self._draw_images(threshold)

    def _time_point_to_rgb(self):
        """If the time point image is a black-and-white image, it is converted to RGB"""
        shape = self._time_point_images.shape
        if len(shape) == 4:
            # Already a full-color image
            return

        old = self._time_point_images
        self._time_point_images = numpy.zeros((shape[0], shape[1], shape[2], 3), dtype=numpy.uint8)
        self._time_point_images[:, :, :, 0] = old / old.max() * 255
        self._time_point_images[:, :, :, 1] = self._time_point_images[:, :, :, 0]
        self._time_point_images[:, :, :, 2] = self._time_point_images[:, :, :, 0]

    def _segment_using_iso_intensity(self):
        images = self._experiment.get_image_stack(self._time_point)
        if images is None:
            dialog.popup_error("Failed to perform detection", "Cannot detect negative Gaussian curvatures of "
                                                              "iso-intensity planes - no images loaded.")
            return
        images = thresholding.image_to_8bit(images)
        out = numpy.full_like(images, 255, dtype=numpy.uint8)
        iso_intensity_curvature.get_negative_gaussian_curvatures(images, ImageDerivatives(), out)

        self._time_point_to_rgb()
        self._time_point_images[:, :, :, 1] = self._time_point_images[:, :, :, 1] & out
        self._time_point_images[:, :, :, 2] = self._time_point_images[:, :, :, 2] & out
        self.draw_view()

    def _on_key_press(self, event: KeyEvent):
        if event.key == "t":
            if len(self._time_point_images.shape) == 4:
                # Reset view
                self.refresh_view()
            else:
                # Show advanced threshold
                self._advanced_threshold()
            return
        super()._on_key_press(event)

    def refresh_view(self):
        self.color_map = DetectionVisualizer.color_map
        super().refresh_view()

    def _print_missed_cells(self, watershed: ndarray):
        particles = self._time_point.particles()
        if len(particles) == 0:
            return
        errors = missed_cell_finder.find_undetected_particles(watershed, particles)
        for particle, error in errors.items():
            print("Error at " + str(particle) + ": " + str(error))