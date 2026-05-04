"""
traffic_sim - Modular traffic simulation library.
"""

from .road import Road
from .junction import Junction
from .source_sink import Source, Sink
from .vehicle import Vehicle
from .router import Router
from .engine import SimulationEngine
from .visualizer import Visualizer, assign_dest_colors
from .network import NetworkBuilder

__all__ = [
    "Road", "Junction", "Source", "Sink",
    "Vehicle", "Router", "SimulationEngine",
    "Visualizer", "assign_dest_colors",
    "NetworkBuilder",
]
