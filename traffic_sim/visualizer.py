"""
visualizer.py - Produce an animated GIF / MP4 of the simulation.

Uses matplotlib only (no extra dependencies beyond the standard scientific stack).
"""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
import numpy as np


# ---- colour helpers -------------------------------------------------------

SINK_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
]


def assign_dest_colors(sink_ids: list) -> dict:
    """Return {sink_id: hex_color} mapping."""
    return {sid: SINK_COLORS[i % len(SINK_COLORS)]
            for i, sid in enumerate(sink_ids)}


# ---- main visualiser class ------------------------------------------------

class Visualizer:
    """
    Animates the traffic simulation using pre-recorded snapshots.

    Parameters
    ----------
    engine  : SimulationEngine
    figsize : (width, height) in inches
    fps     : frames per second for the output animation
    """

    def __init__(self, engine, figsize=(12, 9), fps=10):
        self.engine = engine
        self.figsize = figsize
        self.fps = fps

        # Collect network geometry
        self._nodes = engine._all_nodes
        self._roads = engine._roads
        self._snapshots = engine.snapshots

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_gif(self, path: str = "simulation.gif", max_frames: int = 200):
        """Save an animated GIF."""
        print(f"[Viz] Rendering GIF → {path}  "
              f"({min(len(self._snapshots), max_frames)} frames)")
        fig, ax = self._setup_figure()
        anim = self._make_animation(fig, ax, max_frames)
        writer = PillowWriter(fps=self.fps)
        anim.save(path, writer=writer)
        print(f"[Viz] Saved: {path}")
        plt.close(fig)

    def save_mp4(self, path: str = "simulation.mp4", max_frames: int = 200):
        """Save an MP4 (requires ffmpeg)."""
        try:
            from matplotlib.animation import FFMpegWriter
        except ImportError:
            print("[Viz] ffmpeg not available, falling back to GIF")
            self.save_gif(path.replace(".mp4", ".gif"), max_frames)
            return

        print(f"[Viz] Rendering MP4 → {path}")
        fig, ax = self._setup_figure()
        anim = self._make_animation(fig, ax, max_frames)
        writer = FFMpegWriter(fps=self.fps, bitrate=1800)
        anim.save(path, writer=writer)
        print(f"[Viz] Saved: {path}")
        plt.close(fig)

    def save_stats_figure(self, path: str = "statistics.png"):
        """Save a static statistics plot."""
        stats = self.engine.statistics()
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Traffic Simulation Statistics", fontsize=16, fontweight='bold')
        fig.patch.set_facecolor('#1a1a2e')
        for ax in axes.flat:
            ax.set_facecolor('#16213e')
            ax.tick_params(colors='white')
            ax.title.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            for spine in ax.spines.values():
                spine.set_edgecolor('#0f3460')

        # ---- Plot 1: Source throughput ----
        ax = axes[0, 0]
        sids = list(stats['sources'].keys())
        counts = [stats['sources'][s] for s in sids]
        bars = ax.bar(sids, counts, color=SINK_COLORS[:len(sids)], edgecolor='white')
        ax.set_title("Vehicles Spawned per Source")
        ax.set_ylabel("Count")
        for bar, val in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(val), ha='center', va='bottom', color='white', fontsize=9)

        # ---- Plot 2: Sink throughput ----
        ax = axes[0, 1]
        dk = list(stats['sinks'].keys())
        received = [stats['sinks'][d]['received'] for d in dk]
        bars = ax.bar(dk, received, color=SINK_COLORS[:len(dk)], edgecolor='white')
        ax.set_title("Vehicles Received per Sink")
        ax.set_ylabel("Count")
        for bar, val in zip(bars, received):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(val), ha='center', va='bottom', color='white', fontsize=9)

        # ---- Plot 3: Road avg queue lengths ----
        ax = axes[1, 0]
        road_ids = list(stats['roads'].keys())
        q_lens = [stats['roads'][r]['avg_queue'] for r in road_ids]
        sorted_pairs = sorted(zip(q_lens, road_ids), reverse=True)[:10]
        q_lens_s, road_ids_s = zip(*sorted_pairs) if sorted_pairs else ([], [])
        ax.barh(road_ids_s, q_lens_s, color='#e74c3c', edgecolor='white')
        ax.set_title("Avg Queue Length (top roads)")
        ax.set_xlabel("Vehicles")

        # ---- Plot 4: Road throughput ----
        ax = axes[1, 1]
        tp = [stats['roads'][r]['throughput'] for r in road_ids]
        sorted_tp = sorted(zip(tp, road_ids), reverse=True)[:10]
        tp_s, road_ids_tp = zip(*sorted_tp) if sorted_tp else ([], [])
        ax.barh(road_ids_tp, tp_s, color='#3498db', edgecolor='white')
        ax.set_title("Throughput (top roads)")
        ax.set_xlabel("Vehicles passed")

        plt.tight_layout()
        plt.savefig(path, dpi=120, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"[Viz] Saved statistics figure: {path}")
        plt.close(fig)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _setup_figure(self):
        fig, ax = plt.subplots(figsize=self.figsize)
        fig.patch.set_facecolor('#0d0d1a')
        ax.set_facecolor('#0d0d1a')
        ax.set_aspect('equal')
        ax.axis('off')

        # Draw roads as dark grey lines
        for road in self._roads:
            sx, sy = road.start.position
            ex, ey = road.end.position
            # Slight offset to show directionality
            dx, dy = ex - sx, ey - sy
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy / length * 3, dx / length * 3  # normal offset
            ax.annotate("",
                xy=(ex + nx, ey + ny), xytext=(sx + nx, sy + ny),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color='#3a3a5c',
                    lw=2.0,
                    mutation_scale=10,
                ))

        # Draw nodes
        from .source_sink import Source, Sink
        from .junction import Junction
        for node in self._nodes:
            x, y = node.position
            if isinstance(node, Source):
                ax.plot(x, y, 's', ms=14, color='#2ecc71',
                        markeredgecolor='white', markeredgewidth=1.5, zorder=5)
                ax.text(x, y + 8, node.node_id, ha='center', va='bottom',
                        color='#2ecc71', fontsize=8, fontweight='bold')
            elif isinstance(node, Sink):
                ax.plot(x, y, 'D', ms=14, color='#e74c3c',
                        markeredgecolor='white', markeredgewidth=1.5, zorder=5)
                ax.text(x, y + 8, node.node_id, ha='center', va='bottom',
                        color='#e74c3c', fontsize=8, fontweight='bold')
            else:
                ax.plot(x, y, 'o', ms=10, color='#4a90d9',
                        markeredgecolor='white', markeredgewidth=1.2, zorder=5)
                ax.text(x, y + 8, node.node_id, ha='center', va='bottom',
                        color='#aaaacc', fontsize=7)

        # Legend
        legend_elements = []
        # Collect unique destinations seen in snapshots
        seen_dest_colors = {}
        for snap in self._snapshots:
            for vd in snap['vehicles']:
                seen_dest_colors[vd['dest']] = vd['color']
        for dest, color in sorted(seen_dest_colors.items()):
            legend_elements.append(
                mpatches.Patch(color=color, label=f'→ {dest}'))
        if legend_elements:
            legend = ax.legend(handles=legend_elements, loc='upper right',
                               fontsize=8, framealpha=0.3,
                               facecolor='#1a1a2e', edgecolor='#4a4a6a',
                               labelcolor='white')

        # Auto-scale axes
        xs = [n.position[0] for n in self._nodes]
        ys = [n.position[1] for n in self._nodes]
        if xs and ys:
            pad = 30
            ax.set_xlim(min(xs) - pad, max(xs) + pad)
            ax.set_ylim(min(ys) - pad, max(ys) + pad)

        return fig, ax

    def _make_animation(self, fig, ax, max_frames: int):
        snapshots = self._snapshots
        step = max(1, len(snapshots) // max_frames)
        frames = snapshots[::step]

        # Scatter placeholder
        scat = ax.scatter([], [], s=30, zorder=10)
        time_text = ax.text(0.02, 0.97, '', transform=ax.transAxes,
                            color='white', fontsize=10, va='top',
                            fontweight='bold')
        count_text = ax.text(0.02, 0.93, '', transform=ax.transAxes,
                             color='#aaaacc', fontsize=9, va='top')

        def init():
            scat.set_offsets(np.empty((0, 2)))
            time_text.set_text('')
            count_text.set_text('')
            return scat, time_text, count_text

        def update(frame_data):
            vlist = frame_data['vehicles']
            t = frame_data['time']
            if vlist:
                xy = np.array([[v['x'], v['y']] for v in vlist])
                colors = [v['color'] for v in vlist]
                scat.set_offsets(xy)
                scat.set_color(colors)
            else:
                scat.set_offsets(np.empty((0, 2)))
            time_text.set_text(f"t = {t:.0f} s")
            count_text.set_text(f"vehicles: {len(vlist)}")
            return scat, time_text, count_text

        anim = FuncAnimation(fig, update, frames=frames,
                             init_func=init, blit=True, interval=100)
        return anim
