"""
main.py - Traffic Simulator Entry Point
========================================
Defines a planar test network with 7 junctions, 3 sources, 3 sinks,
and 18 directional roads, then runs the simulation and saves outputs.

Network topology (approximate layout):
                  S2(top)
                   |
     S1(left) --J1--J2--J3-- SK1(right)
                |        |
               J4--J5---J6
                |        |
             SK2(bottom) SK3(bottom-right)

Usage:  python3 main.py
"""
import json
import os
import sys

# Make sure the parent directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_sim import NetworkBuilder, Visualizer


def build_network():
    """
    Define a 7-junction, 3-source, 3-sink network.

    Coordinates are in metres and chosen to produce a visually clean
    planar layout for the animation.
    """
    nb = NetworkBuilder()

    # ------------------------------------------------------------------ #
    #  Node layout (x, y) in metres
    # ------------------------------------------------------------------ #
    #   Sources  (green squares in visualisation)
    nb.add_source("S1", position=(0,   300), rate=0.08, mode='poisson')
    nb.add_source("S2", position=(200, 500), rate=0.06, mode='poisson')
    nb.add_source("S3", position=(400,   0), rate=0.07, mode='poisson')

    #   Sinks  (red diamonds in visualisation)
    nb.add_sink("SK1", position=(600, 300))
    nb.add_sink("SK2", position=(200,   0))
    nb.add_sink("SK3", position=(600,   0))

    #   Junctions  (blue circles)
    nb.add_junction("J1", position=(200, 300), service_rate=2)   # 4-way
    nb.add_junction("J2", position=(400, 300), service_rate=2)   # 4-way
    nb.add_junction("J3", position=(200, 150), service_rate=2)   # 3-way
    nb.add_junction("J4", position=(400, 150), service_rate=2)   # 3-way
    nb.add_junction("J5", position=(300, 300), service_rate=1)   # pass-through
    nb.add_junction("J6", position=(300, 150), service_rate=1)   # pass-through
    nb.add_junction("J7", position=(500, 150), service_rate=2)   # 3-way

    # ------------------------------------------------------------------ #
    #  Roads  (directional)
    #  add_road(id, start, end, length[m], speed[m/s], capacity)
    # ------------------------------------------------------------------ #
    # From sources
    nb.add_road("R_S1_J1",  "S1", "J1",  length=200, speed=12, capacity=10)
    nb.add_road("R_S2_J1",  "S2", "J1",  length=220, speed=10, capacity=8)
    nb.add_road("R_S3_J4",  "S3", "J4",  length=150, speed=12, capacity=8)

    # Main horizontal corridor (top)
    nb.add_road("R_J1_J5",  "J1", "J5",  length=100, speed=14, capacity=10)
    nb.add_road("R_J5_J2",  "J5", "J2",  length=100, speed=14, capacity=10)
    nb.add_road("R_J2_SK1", "J2", "SK1", length=200, speed=12, capacity=10)

    # Main horizontal corridor (bottom)
    nb.add_road("R_J3_J6",  "J3", "J6",  length=100, speed=12, capacity=8)
    nb.add_road("R_J6_J4",  "J6", "J4",  length=100, speed=12, capacity=8)   # reverse
    nb.add_road("R_J4_J7",  "J4", "J7",  length=100, speed=12, capacity=8)
    nb.add_road("R_J7_SK3", "J7", "SK3", length=100, speed=12, capacity=8)

    # Vertical connectors
    nb.add_road("R_J1_J3",  "J1", "J3",  length=150, speed=10, capacity=8)
    nb.add_road("R_J2_J4",  "J2", "J4",  length=150, speed=10, capacity=8)
    nb.add_road("R_J3_SK2", "J3", "SK2", length=150, speed=10, capacity=8)

    # Diagonal / shortcut roads
    nb.add_road("R_J5_J6",  "J5", "J6",  length=155, speed=10, capacity=6)
    nb.add_road("R_J6_J7",  "J6", "J7",  length=105, speed=10, capacity=6)

    # Return / reverse roads to give routing flexibility
    nb.add_road("R_J4_J2",  "J4", "J2",  length=155, speed=10, capacity=6)
    nb.add_road("R_J3_J1",  "J3", "J1",  length=155, speed=10, capacity=6)
    nb.add_road("R_J7_J2",  "J7", "J2",  length=115, speed=10, capacity=6)

    # ------------------------------------------------------------------ #
    #  Assign destinations for each source
    # ------------------------------------------------------------------ #
    #  S1 → SK1, SK2, SK3
    #  S2 → SK1, SK2
    #  S3 → SK1, SK3
    from traffic_sim.visualizer import assign_dest_colors
    all_sinks = ["SK1", "SK2", "SK3"]
    colors = assign_dest_colors(all_sinks)

    nb.node("S1").dest_ids = ["SK1", "SK2", "SK3"]
    nb.node("S1").dest_colors = colors
    nb.node("S2").dest_ids = ["SK1", "SK2"]
    nb.node("S2").dest_colors = colors
    nb.node("S3").dest_ids = ["SK1", "SK3"]
    nb.node("S3").dest_colors = colors

    return nb


def main():
    print("=" * 60)
    print("  TRAFFIC SIMULATOR — Multi-junction Network")
    print("=" * 60)

    # 1. Build the network
    nb = build_network()

    # 2. Create the simulation engine
    engine = nb.build(
        dt=1.0,         # 1 second time-step
        max_time=600.0, # 10 minutes of simulated time
    )

    # 3. Run the simulation (records snapshots every second)
    engine.run(record_interval=2.0, verbose=True)

    # 4. Statistics
    stats = engine.statistics()

    # Save JSON statistics
    with open("statistics.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("\n[Main] Statistics saved → statistics.json")

    # 5. Visualisation
    viz = Visualizer(engine, figsize=(13, 9), fps=12)

    # GIF animation
    viz.save_gif("simulation.gif", max_frames=180)

    # Static statistics figure
    viz.save_stats_figure("statistics.png")

    print("\n[Main] Done.  Output files:")
    print("       simulation.gif  — animated network visualisation")
    print("       statistics.png  — traffic statistics charts")
    print("       statistics.json — raw statistics data")


if __name__ == "__main__":
    main()
