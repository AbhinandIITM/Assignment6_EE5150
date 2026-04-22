# Traffic Simulator

A modular, educational discrete-time traffic simulator for planar road networks.

## Project Structure

```
traffic_sim/          ← reusable library
    __init__.py       ← public API exports
    road.py           ← directional road with capacity & queuing
    junction.py       ← multi-way junction with FIFO scheduling
    vehicle.py        ← vehicle with source/destination & route
    source_sink.py    ← traffic source (Poisson/constant) & sink
    router.py         ← Dijkstra shortest-path router
    engine.py         ← discrete time-step simulation engine
    visualizer.py     ← matplotlib animation + statistics plots
    network.py        ← fluent NetworkBuilder helper

main.py               ← defines the test network & runs simulation
statistics.json       ← output: raw statistics
statistics.png        ← output: statistics charts
simulation.gif        ← output: animated visualisation
```

## Quick Start

```bash
pip install matplotlib numpy pillow
python3 main.py
```

## Library Components

### Road
Directional road connecting two nodes.  
- Configurable `length`, `speed_limit`, `capacity`  
- Entry queue when road is full; FIFO drain  
- Tracks: throughput, avg queue length, avg wait time  

### Junction
Multi-way intersection (2-way, 3-way, 4-way, …).  
- FIFO queue of arriving vehicles  
- `service_rate` vehicles forwarded per time-step  
- Tracks: processed count, avg queue, avg wait  

### Vehicle
Single vehicle travelling through the network.  
- Has `source_id`, `dest_id`, `spawn_time`, `color`  
- Follows a pre-computed `route` (list of Roads)  
- Position interpolated for smooth animation  

### Source
Generates vehicles at a given rate.  
- `mode='constant'` — fixed inter-arrival time  
- `mode='poisson'`  — exponential inter-arrival (Poisson process)  
- Randomly selects destination from configured sink list  

### Sink
Terminal node; vehicles exit here.  
- Records arrival count and travel times  

### Router
Dijkstra shortest-path on the directed road graph.  
- Edge weight = nominal travel time  
- Results cached for repeated (source, sink) pairs  

### SimulationEngine
Time-step loop (`dt` seconds per step).  
1. Advance all roads → collect arrivals  
2. Deliver to junctions / sinks  
3. Junctions drain their queues  
4. Sources spawn new vehicles  
- Records positional snapshots for animation  

### Visualizer
- `save_gif(path)` — animated GIF  
- `save_mp4(path)` — MP4 (requires ffmpeg)  
- `save_stats_figure(path)` — static statistics PNG  

## Adapting to a New Network Topology

Only `main.py` needs to change. Example:

```python
from traffic_sim import NetworkBuilder, Visualizer

nb = NetworkBuilder()

# Nodes
nb.add_source("S1", (0, 0),   rate=0.05)
nb.add_sink("SK1",  (500, 0))
nb.add_junction("J1", (250, 0), service_rate=2)

# Roads
nb.add_road("R1", "S1", "J1", length=250, speed=10, capacity=8)
nb.add_road("R2", "J1", "SK1", length=250, speed=10, capacity=8)

engine = nb.build(dt=1.0, max_time=300)
engine.run()

viz = Visualizer(engine)
viz.save_gif("my_sim.gif")
```

## Design Decisions

| Question | Choice |
|----------|--------|
| **Queuing** | At road entry (upstream queue) AND at junctions |
| **Scheduling** | FIFO with configurable `service_rate` per junction |
| **Routing** | Dijkstra on travel-time-weighted directed graph |
| **Time model** | Uniform time-step (Δt = 1 s default) |
| **Vehicle generation** | Poisson process (exponential inter-arrivals) |

## Statistics Collected

- Total vehicles spawned / completed  
- Average end-to-end travel time  
- Per-source: total spawned  
- Per-sink: total received, avg travel time  
- Per-road: throughput, avg queue length, avg entry-queue wait  
- Per-junction: processed, avg queue length, avg wait time  
