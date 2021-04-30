"""Additional metadata of a position, like the cell type or the fluorescent intensity."""
from typing import Set, Dict, Optional

from organoid_tracker.core.position import Position
from organoid_tracker.core.position_data import PositionData


def get_position_type(position_data: PositionData, position: Position) -> Optional[str]:
    """Gets the type of the cell in UPPERCASE, interpreted as the intestinal organoid cell type."""
    type = position_data.get_position_data(position, "type")
    if type is None:
        return None
    return type.upper()


def set_position_type(position_data: PositionData, position: Position, type: Optional[str]):
    """Sets the type of the cell. Set to None to delete the cell type."""
    type_str = type.upper() if type is not None else None
    position_data.set_position_data(position, "type", type_str)


def get_position_types(position_data: PositionData, positions: Set[Position]) -> Dict[Position, Optional[str]]:
    """Gets all known cell types of the given positions, with the names in UPPERCASE."""
    types = dict()
    for position in positions:
        types[position] = get_position_type(position_data, position)
    return types


def set_intensities(position_data: PositionData, intensities: Dict[Position, int], volumes: Dict[Position, int]):
    """Registers the given intensities for the given positions. Both dicts must have the same keys."""
    if intensities.keys() != volumes.keys():
        raise ValueError("Need to supply intensities and volumes for the same cells")
    position_data.add_positions_data("intensity", intensities)
    position_data.add_positions_data("intensity_volume", intensities)


def get_intensity_per_pixel(position_data: PositionData, position: Position) -> Optional[float]:
    """Gets the average intensity of the position (intensity/pixel)."""
    intensity = position_data.get_position_data(position, "intensity")
    if intensity is None:
        return None
    volume = position_data.get_position_data(position, "intensity_volume")
    if volume is None:
        return None
    return intensity / volume
