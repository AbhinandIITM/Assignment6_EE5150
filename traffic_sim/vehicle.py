"""
vehicle.py - A single vehicle with source, destination, and routing.
"""


class Vehicle:
    """
    Represents a single vehicle travelling through the network.

    Parameters
    ----------
    vehicle_id : str
    source_id  : str   node_id of the origin source
    dest_id    : str   node_id of the destination sink
    spawn_time : float simulation time at which the vehicle was created
    color      : str   hex colour (assigned per destination for visualisation)
    route      : list  ordered list of Road objects from source to sink
    """

    _counter = 0

    def __init__(self, source_id: str, dest_id: str,
                 spawn_time: float, color: str = "#ff0000",
                 route: list = None):
        Vehicle._counter += 1
        self.vehicle_id = f"V{Vehicle._counter:04d}"
        self.source_id = source_id
        self.dest_id = dest_id
        self.spawn_time = spawn_time
        self.color = color

        # Routing
        self.route: list = route or []        # list of Road objects
        self.route_index: int = 0             # index of *current* road

        # State tracking
        self.current_road = None
        self.road_enter_time: float = 0.0
        self.completed: bool = False
        self.exit_time: float = None

        # Position for visualisation: (x, y)
        self.position: tuple = (0.0, 0.0)

    # ------------------------------------------------------------------

    @property
    def current_road_obj(self):
        if self.route_index < len(self.route):
            return self.route[self.route_index]
        return None

    def enter_road(self, road, current_time: float):
        self.current_road = road
        self.road_enter_time = current_time

    def advance_route(self) -> bool:
        """
        Move to the next road in the route.
        Returns False when the vehicle has no more roads (reached sink).
        """
        self.route_index += 1
        if self.route_index >= len(self.route):
            return False   # reached destination
        return True

    def travel_time_total(self) -> float:
        if self.exit_time is None:
            return 0.0
        return self.exit_time - self.spawn_time

    def interpolate_position(self, current_time: float) -> tuple:
        """
        Return (x, y) by linearly interpolating along the current road.
        """
        road = self.current_road
        if road is None:
            return self.position

        t_start = self.road_enter_time
        t_end = t_start + road.travel_time
        if t_end <= t_start:
            frac = 1.0
        else:
            frac = min(1.0, max(0.0,
                (current_time - t_start) / (t_end - t_start)))

        # Positions of the road's start and end nodes
        sx, sy = _node_pos(road.start)
        ex, ey = _node_pos(road.end)
        x = sx + frac * (ex - sx)
        y = sy + frac * (ey - sy)
        return (x, y)

    def __repr__(self):
        return (f"Vehicle({self.vehicle_id}: {self.source_id}→{self.dest_id},"
                f" road={getattr(self.current_road,'road_id',None)},"
                f" done={self.completed})")


def _node_pos(node) -> tuple:
    """Extract (x, y) position from any network node."""
    if hasattr(node, 'position'):
        return node.position
    return (0.0, 0.0)
