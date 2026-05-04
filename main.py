"""
test_network.py - Custom Grid Traffic Network Simulation
========================================================
Implements the 3x2 junction grid network provided in the diagram.

Usage: python3 test_network.py
"""
import json
import os
import sys

# Ensure the parent directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_sim import NetworkBuilder, Visualizer


def build_grid_network():
    
    nb = NetworkBuilder()
 
    # Sinks (Traffic Exits)
    nb.add_sink("K2", position=(600, 400))
    
    nb.add_sink("K3", position=(0, 20))
    nb.add_sink("K4", position=(0, -20))
    
    nb.add_sink("K1", position=(600, 20))
    nb.add_sink("K5", position=(600, -20))

    # Sources (Traffic Entries)
    nb.add_source("S1", position=(0, 420), rate=0.06, mode='poisson')
    nb.add_source("S4", position=(0, 380), rate=0.06, mode='poisson')
    
    nb.add_source("S2", position=(0, 220), rate=0.06, mode='poisson')
    nb.add_source("S5", position=(0, 180), rate=0.06, mode='poisson')
    
    nb.add_source("S3", position=(600, 200), rate=0.08, mode='poisson')


    #  Junctions (3x2 Grid)
    nb.add_junction("J1", position=(200, 400), service_rate=2) # Top-Left
    nb.add_junction("J2", position=(400, 400), service_rate=2) # Top-Right
    nb.add_junction("J3", position=(200, 200), service_rate=2) # Mid-Left
    nb.add_junction("J4", position=(400, 200), service_rate=2) # Mid-Right
    nb.add_junction("J5", position=(200, 0),   service_rate=2) # Bot-Left
    nb.add_junction("J6", position=(400, 0),   service_rate=2) # Bot-Right


    #  Roads
    road_params = {"length": 200, "speed": 12, "capacity": 10}
    # Helper to add bidirectional roads between internal junctions
    def add_bidirectional(id_prefix, n1, n2):
        nb.add_road(f"R_{id_prefix}_F", n1, n2, **road_params)
        nb.add_road(f"R_{id_prefix}_B", n2, n1, **road_params)

    # Internal Horizontal Connections
    add_bidirectional("J1_J2", "J1", "J2")
    add_bidirectional("J3_J4", "J3", "J4")
    add_bidirectional("J5_J6", "J5", "J6")

    # Internal Vertical Connections
    add_bidirectional("J1_J3", "J1", "J3")
    add_bidirectional("J3_J5", "J3", "J5")
    add_bidirectional("J2_J4", "J2", "J4")
    add_bidirectional("J4_J6", "J4", "J6")

    # Entry Roads (Sources -> Junctions)
    nb.add_road("R_S1_J1", "S1", "J1", **road_params)
    nb.add_road("R_S4_J1", "S4", "J1", **road_params)
    
    nb.add_road("R_S2_J3", "S2", "J3", **road_params)
    nb.add_road("R_S5_J3", "S5", "J3", **road_params)
    
    nb.add_road("R_S3_J4", "S3", "J4", **road_params)

    # Exit Roads (Junctions -> Sinks)
    nb.add_road("R_J2_K2", "J2", "K2", **road_params)
    
    nb.add_road("R_J5_K3", "J5", "K3", **road_params)
    nb.add_road("R_J5_K4", "J5", "K4", **road_params)
    
    nb.add_road("R_J6_K1", "J6", "K1", **road_params)
    nb.add_road("R_J6_K5", "J6", "K5", **road_params)

    return nb


def main():
    print("=" * 60)
    print("  TRAFFIC SIMULATOR — Grid Network Test")
    print("=" * 60)

    # 1. Build the network
    nb = build_grid_network()

    # 2. Create the simulation engine
    engine = nb.build(
        dt=1.0,         # 1 second time-step
        max_time=600.0, # 10 minutes of simulated time
        auto_dest_colors=True
    )

    # 3. Run the simulation
    engine.run(record_interval=2.0, verbose=True)

    # 4. Save Statistics
    stats = engine.statistics()
    with open("grid_statistics.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("\n[Main] Statistics saved → grid_statistics.json")

    # 5. Visualisation
    viz = Visualizer(engine, figsize=(14, 10), fps=12)

    viz.save_gif("grid_simulation.gif", max_frames=200)
    viz.save_stats_figure("grid_statistics.png")

    print("\n[Main] Done. Output files:")
    print("       grid_simulation.gif")
    print("       grid_statistics.png")
    print("       grid_statistics.json")


if __name__ == "__main__":
    main()