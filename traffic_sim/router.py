"""
router.py - Dijkstra-based shortest-path router for the road network.

The router builds a graph from registered nodes and roads and finds the
minimum-travel-time route (list of Road objects) from any source to any sink.
"""
import heapq


class Router:
    """
    Pre-computes shortest paths between all (source, sink) pairs using
    Dijkstra's algorithm on a directed graph.

    Usage
    -----
    router = Router()
    router.build(nodes, roads)          # call once after network is wired
    route = router(source_id, dest_id)  # returns list[Road] or None
    """

    def __init__(self):
        # adjacency: node_id → list of (road, neighbour_node_id, weight)
        self._adj: dict = {}
        self._nodes: dict = {}   # node_id → node object
        self._roads: list = []
        self._cache: dict = {}   # (src, dst) → list[Road]

    def build(self, nodes: list, roads: list):
        """
        Parameters
        ----------
        nodes : list of Junction | Source | Sink objects
        roads : list of Road objects
        """
        self._nodes = {n.node_id: n for n in nodes}
        self._roads = roads
        self._adj = {n.node_id: [] for n in nodes}
        self._cache = {}

        for road in roads:
            src_id = road.start.node_id
            dst_id = road.end.node_id
            weight = road.travel_time     # use travel time as edge weight
            if src_id in self._adj:
                self._adj[src_id].append((road, dst_id, weight))

    def __call__(self, source_id: str, dest_id: str):
        """Return list[Road] from source_id to dest_id, or None."""
        key = (source_id, dest_id)
        if key in self._cache:
            return self._cache[key]
        result = self._dijkstra(source_id, dest_id)
        self._cache[key] = result
        return result

    def _dijkstra(self, start: str, end: str):
        """
        Standard Dijkstra.  Returns ordered list of Road objects or None.
        """
        if start not in self._adj or end not in self._adj:
            return None

        # Use a tiebreaker to prevent heapq from comparing Road objects
        # when costs and node_ids are identical.
        tiebreaker = 0
        
        # (cost, tiebreaker, node_id, roads_taken_so_far)
        heap = [(0.0, tiebreaker, start, [])]
        visited = set()

        while heap:
            cost, _, node, roads_so_far = heapq.heappop(heap)

            if node in visited:
                continue
            visited.add(node)

            if node == end:
                return roads_so_far

            for road, neighbour, weight in self._adj.get(node, []):
                if neighbour not in visited:
                    tiebreaker += 1
                    heapq.heappush(heap,
                        (cost + weight, tiebreaker, neighbour, roads_so_far + [road]))

        return None   # no path found

    def all_pairs(self, source_ids: list, sink_ids: list) -> dict:
        """Pre-compute routes for all (source, sink) pairs."""
        result = {}
        for s in source_ids:
            for d in sink_ids:
                result[(s, d)] = self(s, d)
        return result