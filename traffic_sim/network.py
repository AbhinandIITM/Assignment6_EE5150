"""
network.py - Helper to build and wire a road network declaratively.
"""
from .road import Road
from .junction import Junction
from .source_sink import Source, Sink
from .router import Router
from .engine import SimulationEngine
from .visualizer import assign_dest_colors


class NetworkBuilder:
    """
    Fluent API for defining a traffic network.

    Example
    -------
    nb = NetworkBuilder()
    nb.add_junction("J1", (100, 200))
    nb.add_source("S1", (0, 200), rate=0.05)
    nb.add_sink("SK1", (300, 200))
    nb.add_road("R1", "S1", "J1", length=100, speed=10, capacity=8)
    nb.add_road("R2", "J1", "SK1", length=100, speed=10, capacity=8)
    engine = nb.build(dt=1.0, max_time=300)
    """

    def __init__(self):
        self._nodes: dict = {}   # node_id → node object
        self._roads: dict = {}   # road_id → Road object
        self._sources: list = []
        self._sinks: list = []
        self._junctions: list = []

    # ------------------------------------------------------------------
    # Node registration
    # ------------------------------------------------------------------

    def add_junction(self, node_id: str, position: tuple,
                     service_rate: int = 2) -> 'NetworkBuilder':
        j = Junction(node_id, position, service_rate)
        self._nodes[node_id] = j
        self._junctions.append(j)
        return self

    def add_source(self, node_id: str, position: tuple,
                   rate: float = 0.05,
                   mode: str = 'poisson',
                   dest_ids: list = None,
                   dest_colors: dict = None) -> 'NetworkBuilder':
        s = Source(node_id, position, rate, mode, dest_ids, dest_colors)
        self._nodes[node_id] = s
        self._sources.append(s)
        return self

    def add_sink(self, node_id: str, position: tuple) -> 'NetworkBuilder':
        sk = Sink(node_id, position)
        self._nodes[node_id] = sk
        self._sinks.append(sk)
        return self

    # ------------------------------------------------------------------
    # Road registration
    # ------------------------------------------------------------------

    def add_road(self, road_id: str, start_id: str, end_id: str,
                 length: float = 100.0,
                 speed: float = 10.0,
                 capacity: int = 8) -> 'NetworkBuilder':
        assert start_id in self._nodes, f"Unknown node: {start_id}"
        assert end_id in self._nodes, f"Unknown node: {end_id}"
        start = self._nodes[start_id]
        end = self._nodes[end_id]
        road = Road(road_id, start, end, length, speed, capacity)
        self._roads[road_id] = road

        # Wire up the nodes
        if hasattr(start, 'add_outgoing'):
            start.add_outgoing(road)
        if hasattr(end, 'add_incoming'):
            end.add_incoming(road)
        if hasattr(start, '_outgoing'):
            start._outgoing.append(road) if road not in start._outgoing else None

        return self

    # ------------------------------------------------------------------
    # Build engine
    # ------------------------------------------------------------------

    def build(self, dt: float = 1.0, max_time: float = 300.0,
              auto_dest_colors: bool = True) -> SimulationEngine:
        """
        Wire everything together and return a ready-to-run SimulationEngine.
        """
        # Auto-assign destination colours if not set
        if auto_dest_colors:
            sink_ids = [s.node_id for s in self._sinks]
            colors = assign_dest_colors(sink_ids)
            for source in self._sources:
                if not source.dest_ids:
                    source.dest_ids = sink_ids
                if not source.dest_colors:
                    source.dest_colors = colors

        engine = SimulationEngine(dt=dt, max_time=max_time)

        for source in self._sources:
            engine.register_source(source)
        for sink in self._sinks:
            engine.register_sink(sink)
        for junction in self._junctions:
            engine.register_junction(junction)
        for road in self._roads.values():
            engine.register_road(road)

        router = Router()
        engine.set_router(router)

        return engine

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def node(self, node_id: str):
        return self._nodes[node_id]

    def road(self, road_id: str):
        return self._roads[road_id]
