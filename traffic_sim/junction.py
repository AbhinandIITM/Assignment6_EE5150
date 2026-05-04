"""
junction.py - A multi-way road junction with simple FIFO scheduling.

Supports 2-way, 3-way, and 4-way (and beyond) junctions.
Each junction services one waiting vehicle per time-step (configurable).
"""


class Junction:
    """
    A road junction node.

    Vehicles arriving from any incoming road are placed in a FIFO queue.
    Each call to `process(dt)` allows up to `service_rate` vehicles to
    leave the junction onto their next road.

    Parameters
    ----------
    node_id  : str
    position : (float, float)  (x, y) in metres for visualisation
    service_rate : int   vehicles processed per simulation step (≥1)
    """

    def __init__(self, node_id: str, position: tuple = (0.0, 0.0),
                 service_rate: int = 1):
        self.node_id = node_id
        self.position = position
        self.service_rate = service_rate

        # Incoming roads registered at this junction
        self._incoming: list = []   # Road objects
        # Outgoing roads
        self._outgoing: list = []   # Road objects

        # FIFO queue: vehicles waiting to leave the junction
        from collections import deque
        self._queue: deque = deque()

        # Stats
        self.total_processed = 0
        self._queue_samples: list = []
        self.total_queue_wait = 0.0

    # ------------------------------------------------------------------
    # Network construction helpers
    # ------------------------------------------------------------------

    def add_incoming(self, road):
        if road not in self._incoming:
            self._incoming.append(road)

    def add_outgoing(self, road):
        if road not in self._outgoing:
            self._outgoing.append(road)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def receive(self, vehicle, current_time: float):
        """Called when a vehicle finishes a road and arrives at this junction."""
        self._queue.append((vehicle, current_time))

    def process(self, current_time: float) -> list:
        """
        Try to forward up to `service_rate` vehicles from the queue.

        Returns list of (vehicle, road) pairs that could NOT be forwarded
        (e.g. next road is full) - these stay in the queue.
        """
        self._queue_samples.append(len(self._queue))
        processed = 0
        still_waiting = []

        while self._queue and processed < self.service_rate:
            vehicle, queued_at = self._queue[0]

            # Determine the next road for this vehicle
            next_road = self._next_road(vehicle)

            if next_road is None:
                # No valid next road - discard (shouldn't happen with correct routing)
                self._queue.popleft()
                vehicle.completed = True
                vehicle.exit_time = current_time
                processed += 1
                self.total_processed += 1
                continue

            if next_road.is_full:
                # Can't proceed - leave at front of queue and stop
                break

            self._queue.popleft()
            wait = current_time - queued_at
            self.total_queue_wait += wait
            vehicle.advance_route()
            next_road.try_enter(vehicle, current_time)
            processed += 1
            self.total_processed += 1

        return []   # API placeholder; queue drain handled internally

    def _next_road(self, vehicle):
        """Return the next Road in the vehicle's route, or None."""
        # The vehicle is currently *at* this junction; its route_index
        # points to the road it just completed. Next road = route_index+1.
        next_idx = vehicle.route_index + 1
        if next_idx < len(vehicle.route):
            return vehicle.route[next_idx]
        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def queue_length(self) -> int:
        return len(self._queue)

    def avg_queue_length(self) -> float:
        if not self._queue_samples:
            return 0.0
        return sum(self._queue_samples) / len(self._queue_samples)

    def avg_wait_time(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.total_queue_wait / self.total_processed

    def way_count(self) -> int:
        """Number of unique connected roads (incoming + outgoing, de-duped)."""
        return len(set(self._incoming) | set(self._outgoing))

    def __repr__(self):
        return (f"Junction({self.node_id}, "
                f"{len(self._incoming)}in/{len(self._outgoing)}out, "
                f"q={self.queue_length})")
