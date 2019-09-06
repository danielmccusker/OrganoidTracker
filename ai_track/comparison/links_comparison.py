"""Compares two sets of links on the level of individual links. Missed cell divisions/deaths are not reported. Instead,
for every link in the baseline data, it is checked if it is present in the automatic data, and vice versa."""
from typing import Iterable, Optional, Tuple, Set

import math

from ai_track.comparison.report import Category, ComparisonReport, Statistics
from ai_track.core.experiment import Experiment
from ai_track.core.links import Links
from ai_track.core.position import Position
from ai_track.linking import nearby_position_finder

LINKS_FALSE_NEGATIVES = Category("Missed links")
LINKS_TRUE_POSITIVES = Category("Correctly detected links")
LINKS_FALSE_POSITIVES = Category("Made up links")


class LinksReport(ComparisonReport):

    def __init__(self):
        super().__init__()
        self.title = "Links comparison"

    def calculate_time_correctness_statistics(self) -> Statistics:
        return self.calculate_time_statistics(LINKS_TRUE_POSITIVES, LINKS_FALSE_POSITIVES, LINKS_FALSE_NEGATIVES)

    def calculate_z_correctness_statistics(self) -> Statistics:
        return self.calculate_z_statistics(LINKS_TRUE_POSITIVES, LINKS_FALSE_POSITIVES, LINKS_FALSE_NEGATIVES)


def _find_close_positions(position: Position, experiment: Experiment, max_distance: float) -> Iterable[Position]:
    all_positions = experiment.positions.of_time_point(position.time_point())
    resolution = experiment.images.resolution()
    return nearby_position_finder.find_closest_n_positions(all_positions, around=position, resolution=resolution,
                                                           max_amount=3, max_distance_um=max_distance, ignore_self=False)

class _Link:
    """A link, that keeps it arbitrariy which is pos1 and which is pos2"""
    pos1: Position
    pos2: Position

    def __init__(self, pos1: Position, pos2: Position):
        self.pos1 = pos1
        self.pos2 = pos2

    def __hash__(self):
        return hash(self.pos1) + hash(self.pos2)

    def __eq__(self, other):
        if not isinstance(other, _Link):
            return False
        return (other.pos1 == self.pos1 and other.pos2 == self.pos2) or (other.pos1 == self.pos2 and other.pos2 == self.pos1)


def _get_link(links: Links, positions1: Iterable[Position], positions2: Iterable[Position],
              forbidden_links: Set[_Link]
              ) -> Optional[_Link]:
    for position1 in positions1:
        for position2 in positions2:
            if links.contains_link(position1, position2) and _Link(position1, position2) not in forbidden_links:
                return _Link(position1, position2)
    return None


def compare_links(ground_truth: Experiment, scratch: Experiment, max_distance_um: float = 5) -> LinksReport:
    result = LinksReport()

    # Check if all baseline links exist
    used_scratch_links = set()
    for position1, position2 in ground_truth.links.find_all_links():
        scratch_positions1 = _find_close_positions(position1, scratch, max_distance_um)
        scratch_positions2 = _find_close_positions(position2, scratch, max_distance_um)
        found_scratch_link = _get_link(scratch.links, scratch_positions1, scratch_positions2, used_scratch_links)
        if found_scratch_link is not None:
            # True positive
            used_scratch_links.add(found_scratch_link)
            result.add_data(LINKS_TRUE_POSITIVES, position1, "is linked to", position2)
        else:
            # False negative
            result.add_data(LINKS_FALSE_NEGATIVES, position1, "has mistakenly no link to", position2)

    # Check if all scratch links are real
    used_ground_truth_links = set()
    for position1, position2 in scratch.links.find_all_links():
        ground_truth_positions1 = _find_close_positions(position1, ground_truth, max_distance_um)
        ground_truth_positions2 = _find_close_positions(position2, ground_truth, max_distance_um)
        found_ground_truth_link = _get_link(ground_truth.links, ground_truth_positions1, ground_truth_positions2,
                                            used_ground_truth_links)
        if found_ground_truth_link is not None:
            # True positive, already detected in earlier loop
            used_ground_truth_links.add(found_ground_truth_link)
            pass
        else:
            # False positive
            result.add_data(LINKS_FALSE_POSITIVES, position1, "has mistakenly a link to", position2)

    return result
