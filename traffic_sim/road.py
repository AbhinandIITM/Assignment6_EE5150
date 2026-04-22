"""
road.py - Directional road with capacity and queuing.
"""
from collections import deque


class Road:
    """
    A directional road connecting two junctions (or a source/sink).

    Vehicles travel along the road at a fixed speed. The road has a finite
    capacity; once full, entering vehicles are queued at the upstream end.

    Attributes
    ----------
    road_id : str
    start   : Junction | Source | Sink  (upstream node)
    end     : Junction | Source | Sink  (downstream node)
    length  : float  [m]
    speed_limit : float  [m/s]
    capacity    : int    max vehicles on the road simultaneously
    """

    def __init__(self, road_id: str, start, end,
                 length: float = 100.0,
                 speed_limit: float = 10.0,
                 capacity: int = 10):
        self.road_id = road_id
        self.start = start
        self.end = end
        self.length = length
        self.speed_limit = speed_limit
        self.capacity = capacity

        # Vehicles currently travelling on the road:
        # list of (vehicle, arrival_time_at_end)
        self._travelling: list = []

        # Vehicles queued waiting to enter the road (upstream queue)
        self._entry_queue: deque = deque()

        # Statistics
        self.total_vehicles_passed = 0
        self.total_wait_time = 0.0          # cumulative entry-queue wait
        self._queue_length_samples: list = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def travel_time(self) -> float:
        """Nominal travel time [s]."""
        return self.length / self.speed_limit

    @property
    def occupancy(self) -> int:
        return len(self._travelling)

    @property
    def is_full(self) -> bool:
        return self.occupancy >= self.capacity

    @property
    def entry_queue_length(self) -> int:
        return len(self._entry_queue)

    # ------------------------------------------------------------------
    # Vehicle management
    # ------------------------------------------------------------------

    def try_enter(self, vehicle, current_time: float) -> bool:
        """
        Attempt to place *vehicle* onto the road at *current_time*.
        Returns True if the vehicle started travelling, False if queued.
        """
        if not self.is_full:
            arrival = current_time + self.travel_time
            self._travelling.append((vehicle, arrival))
            vehicle.enter_road(self, current_time)
            return True
        else:
            self._entry_queue.append((vehicle, current_time))
            return False

    def enqueue(self, vehicle, current_time: float):
        """Force-queue vehicle without trying to enter (used by sources)."""
        self._entry_queue.append((vehicle, current_time))

    def advance(self, current_time: float) -> list:
        """
        Move simulation forward to *current_time*.

        Returns list of vehicles that have completed this road segment
        and are ready to enter the next node (junction / sink).
        """
        self._queue_length_samples.append(
            len(self._travelling) + len(self._entry_queue))

        # 1. Collect vehicles that have finished travelling
        arrived = []
        still_travelling = []
        for vehicle, t_arrival in self._travelling:
            if current_time >= t_arrival:
                arrived.append(vehicle)
            else:
                still_travelling.append((vehicle, t_arrival))
        self._travelling = still_travelling

        # 2. Try to drain the entry queue into freed slots
        while self._entry_queue and not self.is_full:
            vehicle, queued_at = self._entry_queue.popleft()
            wait = current_time - queued_at
            self.total_wait_time += wait
            arrival = current_time + self.travel_time
            self._travelling.append((vehicle, arrival))
            vehicle.enter_road(self, current_time)

        self.total_vehicles_passed += len(arrived)
        return arrived

    # ------------------------------------------------------------------
    # Stats helpers
    # ------------------------------------------------------------------

    def avg_queue_length(self) -> float:
        if not self._queue_length_samples:
            return 0.0
        return sum(self._queue_length_samples) / len(self._queue_length_samples)

    def avg_wait_time(self) -> float:
        if self.total_vehicles_passed == 0:
            return 0.0
        return self.total_wait_time / self.total_vehicles_passed

    def __repr__(self):
        return (f"Road({self.road_id}: {getattr(self.start,'node_id',str(self.start))}"
                f" → {getattr(self.end,'node_id',str(self.end))},"
                f" occ={self.occupancy}/{self.capacity})")
