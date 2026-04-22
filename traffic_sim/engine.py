"""
engine.py - Discrete time-step simulation engine.

Each simulation step:
1. Advance all roads → collect vehicles that finished traversal
2. Deliver arrived vehicles to their next node (junction or sink)
3. Each junction processes its queue → forward vehicles to next roads
4. Each source generates new vehicles
"""


class SimulationEngine:
    """
    Time-step based simulation engine.

    Parameters
    ----------
    dt       : float   time step in seconds (default 1 s)
    max_time : float   total simulation duration in seconds
    """

    def __init__(self, dt: float = 1.0, max_time: float = 300.0):
        self.dt = dt
        self.max_time = max_time
        self.current_time: float = 0.0

        # Network components (populated via register_* methods)
        self._sources: list = []
        self._sinks: list = []
        self._junctions: list = []
        self._roads: list = []
        self._all_nodes: list = []

        # All active (not yet completed) vehicles
        self._active_vehicles: list = []
        self._completed_vehicles: list = []

        # Router
        self.router = None

        # Per-step snapshot for visualisation
        self.snapshots: list = []   # list of dicts

        # Callbacks
        self._on_vehicle_complete = []

    # ------------------------------------------------------------------
    # Network registration
    # ------------------------------------------------------------------

    def register_source(self, source):
        self._sources.append(source)
        self._all_nodes.append(source)

    def register_sink(self, sink):
        self._sinks.append(sink)
        self._all_nodes.append(sink)

    def register_junction(self, junction):
        self._junctions.append(junction)
        self._all_nodes.append(junction)

    def register_road(self, road):
        self._roads.append(road)

    def set_router(self, router):
        self.router = router
        router.build(self._all_nodes, self._roads)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, record_interval: float = 1.0, verbose: bool = True):
        """
        Run the simulation from t=0 to t=max_time.

        Parameters
        ----------
        record_interval : float  seconds between visualisation snapshots
        verbose         : bool   print progress
        """
        assert self.router is not None, "Call set_router() before run()"

        next_record = 0.0
        step_count = int(self.max_time / self.dt)

        if verbose:
            print(f"[Engine] Starting simulation: dt={self.dt}s, "
                  f"T={self.max_time}s, steps={step_count}")

        for step in range(step_count):
            self.current_time = step * self.dt
            self._step()

            if self.current_time >= next_record:
                self._record_snapshot()
                next_record += record_interval

        # Final step
        self.current_time = self.max_time
        self._step()
        self._record_snapshot()

        if verbose:
            self._print_summary()

    def _step(self):
        t = self.current_time

        # 1. Advance all roads → collect arrivals
        for road in self._roads:
            arrived = road.advance(t)
            for vehicle in arrived:
                self._deliver(vehicle, road.end, t)

        # 2. Process junctions
        for junction in self._junctions:
            junction.process(t)

        # 3. Sources spawn new vehicles
        for source in self._sources:
            new_vehicles = source.step(
                t, self.dt,
                router=self.router,
                spawn_cb=self._active_vehicles.append
            )

        # 4. Sweep completed vehicles
        still_active = []
        for v in self._active_vehicles:
            if v.completed:
                self._completed_vehicles.append(v)
                for cb in self._on_vehicle_complete:
                    cb(v)
            else:
                still_active.append(v)
        self._active_vehicles = still_active

    def _deliver(self, vehicle, node, current_time: float):
        """Route an arrived vehicle to its next node."""
        from .source_sink import Sink
        from .junction import Junction

        if isinstance(node, Sink):
            # Advance route to mark road as done, then deliver
            vehicle.route_index += 1
            node.receive(vehicle, current_time)
        elif isinstance(node, Junction):
            # Advance route index so junction knows which road was just done
            vehicle.route_index += 1
            # Peek at next road
            next_idx = vehicle.route_index
            if next_idx >= len(vehicle.route):
                # Arrived at junction but route is exhausted - treat as sink
                vehicle.completed = True
                vehicle.exit_time = current_time
            else:
                next_road = vehicle.route[next_idx]
                if not next_road.is_full:
                    wait_start = current_time
                    self.router  # just to keep reference
                    next_road.try_enter(vehicle, current_time)
                else:
                    node.receive(vehicle, current_time)

    # ------------------------------------------------------------------
    # Snapshot recording
    # ------------------------------------------------------------------

    def _record_snapshot(self):
        """Record the positions of all active vehicles for animation."""
        t = self.current_time
        vehicle_data = []
        for v in self._active_vehicles:
            pos = v.interpolate_position(t)
            vehicle_data.append({
                'id': v.vehicle_id,
                'x': pos[0],
                'y': pos[1],
                'color': v.color,
                'dest': v.dest_id,
                'source': v.source_id,
            })
        self.snapshots.append({
            'time': t,
            'vehicles': vehicle_data,
        })

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(self) -> dict:
        """Return a dict of aggregate statistics."""
        all_done = self._completed_vehicles
        n = len(all_done)
        travel_times = [v.travel_time_total() for v in all_done]
        avg_tt = sum(travel_times) / n if n else 0

        road_stats = {}
        for road in self._roads:
            road_stats[road.road_id] = {
                'throughput': road.total_vehicles_passed,
                'avg_queue': road.avg_queue_length(),
                'avg_wait': road.avg_wait_time(),
            }

        junction_stats = {}
        for j in self._junctions:
            junction_stats[j.node_id] = {
                'processed': j.total_processed,
                'avg_queue': j.avg_queue_length(),
                'avg_wait': j.avg_wait_time(),
            }

        source_stats = {s.node_id: s.total_spawned for s in self._sources}
        sink_stats = {s.node_id: {
            'received': s.total_received,
            'avg_travel_time': s.avg_travel_time()
        } for s in self._sinks}

        return {
            'total_completed': n,
            'total_spawned': sum(source_stats.values()),
            'avg_travel_time': avg_tt,
            'sources': source_stats,
            'sinks': sink_stats,
            'roads': road_stats,
            'junctions': junction_stats,
        }

    def _print_summary(self):
        stats = self.statistics()
        print("\n" + "="*60)
        print("SIMULATION SUMMARY")
        print("="*60)
        print(f"  Simulation duration : {self.max_time:.0f} s")
        print(f"  Vehicles spawned    : {stats['total_spawned']}")
        print(f"  Vehicles completed  : {stats['total_completed']}")
        print(f"  Avg travel time     : {stats['avg_travel_time']:.1f} s")
        print("\n  Source throughput:")
        for sid, count in stats['sources'].items():
            print(f"    {sid}: {count} vehicles spawned")
        print("\n  Sink throughput:")
        for sid, info in stats['sinks'].items():
            print(f"    {sid}: {info['received']} received, "
                  f"avg travel {info['avg_travel_time']:.1f} s")
        print("\n  Road statistics (top by throughput):")
        sorted_roads = sorted(stats['roads'].items(),
                              key=lambda x: -x[1]['throughput'])[:8]
        for rid, rs in sorted_roads:
            print(f"    {rid}: {rs['throughput']} passed, "
                  f"avg_queue={rs['avg_queue']:.2f}, "
                  f"avg_wait={rs['avg_wait']:.1f} s")
        print("="*60)
