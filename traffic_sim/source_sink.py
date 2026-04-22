"""
source_sink.py - Traffic sources (vehicle generators) and sinks (exits).
"""
import random
import math


class Source:
    """
    Generates vehicles at a given rate and injects them into an outgoing road.

    Parameters
    ----------
    node_id     : str
    position    : (float, float)
    rate        : float   vehicles / second (mean rate for Poisson process)
    mode        : 'constant' | 'poisson'
    dest_ids    : list[str]  destination sink node_ids (chosen uniformly at random)
    dest_colors : dict[str, str]  mapping dest_id → hex color for visualisation
    """

    def __init__(self, node_id: str, position: tuple = (0.0, 0.0),
                 rate: float = 0.1,
                 mode: str = 'poisson',
                 dest_ids: list = None,
                 dest_colors: dict = None):
        self.node_id = node_id
        self.position = position
        self.rate = rate          # vehicles/second
        self.mode = mode
        self.dest_ids = dest_ids or []
        self.dest_colors = dest_colors or {}

        self._outgoing: list = []   # Road objects
        self._time_to_next: float = self._sample_interval()

        # Stats
        self.total_spawned = 0

    def add_outgoing(self, road):
        if road not in self._outgoing:
            self._outgoing.append(road)

    def _sample_interval(self) -> float:
        if self.rate <= 0:
            return float('inf')
        if self.mode == 'constant':
            return 1.0 / self.rate
        else:  # Poisson → exponential inter-arrival times
            return random.expovariate(self.rate)

    def step(self, current_time: float, dt: float,
             router, spawn_cb=None) -> list:
        """
        Advance the source by dt seconds.  Returns list of new Vehicle objects.

        Parameters
        ----------
        router   : callable(source_id, dest_id) → list[Road] | None
        spawn_cb : optional callback(vehicle) for logging
        """
        from .vehicle import Vehicle

        spawned = []
        elapsed = dt

        while elapsed >= self._time_to_next:
            elapsed -= self._time_to_next
            self._time_to_next = self._sample_interval()

            if not self.dest_ids or not self._outgoing:
                continue

            dest_id = random.choice(self.dest_ids)
            color = self.dest_colors.get(dest_id, "#888888")
            spawn_t = current_time - elapsed   # approximate spawn time

            route = router(self.node_id, dest_id)
            if route is None:
                continue   # no path found

            v = Vehicle(self.node_id, dest_id, spawn_t, color, route)
            # Enter the first road of the route
            first_road = route[0]
            first_road.try_enter(v, spawn_t)

            self.total_spawned += 1
            spawned.append(v)
            if spawn_cb:
                spawn_cb(v)

        self._time_to_next -= elapsed
        return spawned

    def __repr__(self):
        return f"Source({self.node_id}, rate={self.rate}/s, spawned={self.total_spawned})"


class Sink:
    """
    A terminal node where vehicles exit the network.

    Parameters
    ----------
    node_id  : str
    position : (float, float)
    """

    def __init__(self, node_id: str, position: tuple = (0.0, 0.0)):
        self.node_id = node_id
        self.position = position
        self._incoming: list = []

        # Stats
        self.total_received = 0
        self._travel_times: list = []

    def add_incoming(self, road):
        if road not in self._incoming:
            self._incoming.append(road)

    def receive(self, vehicle, current_time: float):
        """Called when a vehicle completes its last road and arrives here."""
        vehicle.completed = True
        vehicle.exit_time = current_time
        self.total_received += 1
        tt = vehicle.travel_time_total()
        self._travel_times.append(tt)

    def avg_travel_time(self) -> float:
        if not self._travel_times:
            return 0.0
        return sum(self._travel_times) / len(self._travel_times)

    def __repr__(self):
        return f"Sink({self.node_id}, received={self.total_received})"
