"""Cell density is defined as the average distance to the X nearest cells."""
from typing import Iterable

from autotrack.core.position import Position
from autotrack.core.resolution import ImageResolution
from autotrack.linking import nearby_position_finder


_AMOUNT_OF_NEIGHBOR_CELLS = 6


def get_density(positions: Iterable[Position], around: Position, resolution: ImageResolution) -> float:
    """Returns the density around the cells. The returned value is 1/average neighbor distance, in um^(-1)."""
    nearby_positions = nearby_position_finder.find_closest_n_positions(positions, around=around, resolution=resolution,
                                                                       max_amount=_AMOUNT_OF_NEIGHBOR_CELLS)
    if len(nearby_positions) == 0:
        return 0

    total_distance_um = sum(nearby_position.distance_um(around, resolution) for nearby_position in nearby_positions)
    average_distance_um = total_distance_um / len(nearby_positions)
    return 1 / average_distance_um
