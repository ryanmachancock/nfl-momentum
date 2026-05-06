"""
Graph export service for generating modern PNG and SVG momentum charts.
Inspired by modern fintech app aesthetics (clean, dark theme, gradient fills).
Uses time-based x-axis for evenly spaced quarters.
"""
import io
from typing import Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from ..schemas import MomentumDataPoint, GameResponse


class GraphExporter:
    """Generates modern, exportable momentum charts."""

    # Modern team colors (slightly adjusted for dark backgrounds)
    TEAM_COLORS = {
        'ARI': '#97233F', 'ATL': '#A71930', 'BAL': '#241773', 'BUF': '#00338D',
        'CAR': '#0085CA', 'CHI': '#C83803', 'CIN': '#FB4F14', 'CLE': '#FF3C00',
        'DAL': '#003594', 'DEN': '#FB4F14', 'DET': '#0076B6', 'GB': '#203731',
        'HOU': '#03202F', 'IND': '#002C5F', 'JAX': '#006778', 'KC': '#E31837',
        'LA': '#003594', 'LAC': '#0080C6', 'LV': '#A5ACAF', 'MIA': '#008E97',
        'MIN': '#4F2683', 'NE': '#002244', 'NO': '#D3BC8D', 'NYG': '#0B2265',
        'NYJ': '#125740', 'PHI': '#004C54', 'PIT': '#FFB612', 'SEA': '#69BE28',
        'SF': '#AA0000', 'TB': '#D50A0A', 'TEN': '#4B92DB', 'WAS': '#773141',
        'SD': '#0080C6', 'STL': '#003594', 'OAK': '#A5ACAF',
    }

    # Dark theme colors
    BG_COLOR = '#0d1117'
    CARD_BG = '#161b22'
    TEXT_COLOR = '#e6edf3'
    TEXT_SECONDARY = '#8b949e'
    GRID_COLOR = '#30363d'
    ACCENT_GREEN = '#3fb950'
    ACCENT_RED = '#f85149'
    ACCENT_BLUE = '#58a6ff'

    def __init__(self):
        pass

    def _parse_game_time(self, quarter: int, time_remaining: str) -> float:
        """
        Convert time_remaining (MM:SS) and quarter to absolute game time in minutes.
        Q1: 0-15 min, Q2: 15-30 min, Q3: 30-45 min, Q4: 45-60 min, OT: 60+ min
        """
        try:
            parts = time_remaining.split(':')
            if len(parts) != 2:
                return (quarter - 1) * 15

            minutes = int(parts[0]) if parts[0] else 0
            seconds = int(parts[1]) if parts[1] else 0
            time_remaining_minutes = minutes + seconds / 60

            # Game time = (quarter - 1) * 15 + (15 - time_remaining)
            quarter_start_time = (quarter - 1) * 15
            elapsed_in_quarter = 15 - time_remaining_minutes

            return quarter_start_time + max(0, elapsed_in_quarter)
        except (ValueError, AttributeError):
            return (quarter - 1) * 15

    def generate_png(
        self,
        game: GameResponse,
        data_points: list[MomentumDataPoint],
        width: int = 1400,
        height: int = 800,
        show_win_prob: bool = True
    ) -> bytes:
        """Generate a modern PNG chart of the momentum graph."""
        fig = self._create_figure(game, data_points, width, height, show_win_prob)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.BG_COLOR, edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_svg(
        self,
        game: GameResponse,
        data_points: list[MomentumDataPoint],
        width: int = 1400,
        height: int = 800,
        show_win_prob: bool = True
    ) -> str:
        """Generate a modern SVG chart of the momentum graph."""
        fig = self._create_figure(game, data_points, width, height, show_win_prob)

        buf = io.StringIO()
        fig.savefig(buf, format='svg', bbox_inches='tight',
                    facecolor=self.BG_COLOR, edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def _create_figure(
        self,
        game: GameResponse,
        data_points: list[MomentumDataPoint],
        width: int,
        height: int,
        show_win_prob: bool = True
    ) -> plt.Figure:
        """Create the modern matplotlib figure with time-based x-axis."""
        fig_width = width / 100
        fig_height = height / 100

        fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=self.BG_COLOR)
        ax.set_facecolor(self.CARD_BG)

        if not data_points:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                    transform=ax.transAxes, fontsize=16, color=self.TEXT_COLOR)
            return fig

        # Get team colors
        home_color = self.TEAM_COLORS.get(game.home_team, self.ACCENT_GREEN)
        away_color = self.TEAM_COLORS.get(game.away_team, self.ACCENT_RED)

        # Convert to time-based x values
        x = np.array([self._parse_game_time(dp.quarter, dp.time_remaining) for dp in data_points])
        y = np.array([dp.home_momentum for dp in data_points])

        # Determine max time (handle overtime)
        max_time = max(np.max(x), 60)

        # Smooth the line using interpolation
        if len(x) > 10:
            from scipy.ndimage import gaussian_filter1d
            y_smooth = gaussian_filter1d(y, sigma=2)
        else:
            y_smooth = y

        # Create gradient fills
        self._fill_gradient(ax, x, y_smooth, home_color, away_color)

        # Draw the main momentum line with glow effect
        ax.plot(x, y_smooth, color='white', linewidth=4, alpha=0.15, zorder=4)
        ax.plot(x, y_smooth, color='white', linewidth=2.5, alpha=0.3, zorder=5)
        ax.plot(x, y_smooth, color='#ffffff', linewidth=1.5, zorder=6)

        # Win probability overlay (if data available and enabled)
        if show_win_prob and data_points[0].home_wp is not None:
            self._add_win_prob_overlay(ax, data_points, x)

        # Mark significant events with subtle dots
        for i, dp in enumerate(data_points):
            if dp.is_significant:
                color = home_color if dp.momentum_delta > 0 else away_color
                ax.scatter([x[i]], [y_smooth[i]], color=color, s=60, zorder=10,
                          edgecolors='white', linewidths=1.5, alpha=0.9)

        # Add quarter markers at fixed time positions
        self._add_quarter_markers(ax, max_time)

        # Styling
        ax.axhline(y=0, color=self.GRID_COLOR, linewidth=1, linestyle='-', zorder=1)
        ax.set_xlim(0, max_time)
        ax.set_ylim(-110, 110)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Minimal grid
        ax.yaxis.grid(True, color=self.GRID_COLOR, alpha=0.3, linewidth=0.5)
        ax.xaxis.grid(True, color=self.GRID_COLOR, alpha=0.3, linewidth=0.5)

        # X-axis labels for quarters
        quarter_ticks = [0, 15, 30, 45, 60]
        if max_time > 60:
            # Add overtime ticks
            ot_count = int((max_time - 60) // 15) + 1
            quarter_ticks.extend([60 + i * 15 for i in range(1, ot_count + 1)])

        ax.set_xticks(quarter_ticks)
        quarter_labels = ['Q1', 'Q2', 'Q3', 'Q4', 'End']
        if max_time > 60:
            quarter_labels = ['Q1', 'Q2', 'Q3', 'Q4'] + [f'OT{i}' for i in range(1, ot_count + 1)] + ['End']
        ax.set_xticklabels(quarter_labels[:len(quarter_ticks)])

        # Labels with modern styling
        ax.set_ylabel('MOMENTUM', fontsize=10, color=self.TEXT_SECONDARY,
                     fontweight='600', labelpad=10)
        ax.tick_params(axis='both', colors=self.TEXT_SECONDARY, labelsize=9)

        # Title area (top of chart)
        self._add_header(fig, ax, game, home_color, away_color)

        # Legend
        self._add_legend(ax, game, home_color, away_color, show_win_prob)

        fig.tight_layout()
        fig.subplots_adjust(top=0.85, bottom=0.1)

        return fig

    def _fill_gradient(self, ax, x, y, home_color, away_color):
        """Create gradient fills above and below zero."""
        # Home team (positive)
        y_pos = np.clip(y, 0, None)
        ax.fill_between(x, 0, y_pos, alpha=0.6, color=home_color, zorder=2)
        ax.fill_between(x, 0, y_pos, alpha=0.3, color=home_color, zorder=2)

        # Away team (negative)
        y_neg = np.clip(y, None, 0)
        ax.fill_between(x, 0, y_neg, alpha=0.6, color=away_color, zorder=2)
        ax.fill_between(x, 0, y_neg, alpha=0.3, color=away_color, zorder=2)

    def _add_win_prob_overlay(self, ax, data_points, x):
        """Add win probability as a subtle overlay line."""
        # Convert win prob (0-1) to our scale (-100 to 100)
        wp_values = []
        for dp in data_points:
            if dp.home_wp is not None:
                scaled = (dp.home_wp - 0.5) * 200
                wp_values.append(scaled)
            else:
                wp_values.append(0)

        wp = np.array(wp_values)

        # Smooth it
        if len(wp) > 10:
            from scipy.ndimage import gaussian_filter1d
            wp_smooth = gaussian_filter1d(wp, sigma=3)
        else:
            wp_smooth = wp

        # Draw as dashed line with subtle styling
        ax.plot(x, wp_smooth, color=self.ACCENT_BLUE, linewidth=1.5, linestyle='--',
               alpha=0.7, zorder=3, label='Win Probability')

    def _add_quarter_markers(self, ax, max_time):
        """Add subtle quarter transition markers at fixed time positions."""
        quarter_times = [15, 30, 45]
        if max_time > 60:
            # Add overtime markers
            ot_count = int((max_time - 60) // 15)
            quarter_times.extend([60 + i * 15 for i in range(1, ot_count + 1)])

        for t in quarter_times:
            ax.axvline(x=t, color=self.GRID_COLOR, linewidth=1,
                      linestyle=':', alpha=0.5, zorder=1)

    def _add_header(self, fig, ax, game, home_color, away_color):
        """Add modern header with game info."""
        title = f"{game.away_team}  @  {game.home_team}"
        fig.text(0.5, 0.94, title, ha='center', fontsize=24, fontweight='bold',
                color=self.TEXT_COLOR, transform=fig.transFigure)

        score_str = ""
        if game.home_score is not None and game.away_score is not None:
            score_str = f"{game.away_score} - {game.home_score}"
        details = f"Week {game.week}, {game.season}"
        if score_str:
            details = f"{score_str}  |  {details}"

        fig.text(0.5, 0.89, details, ha='center', fontsize=12,
                color=self.TEXT_SECONDARY, transform=fig.transFigure)

    def _add_legend(self, ax, game, home_color, away_color, show_win_prob):
        """Add a clean legend."""
        from matplotlib.lines import Line2D

        legend_elements = [
            mpatches.Patch(facecolor=home_color, alpha=0.6,
                          label=f'{game.home_team} Momentum'),
            mpatches.Patch(facecolor=away_color, alpha=0.6,
                          label=f'{game.away_team} Momentum'),
        ]

        if show_win_prob:
            legend_elements.append(
                Line2D([0], [0], color=self.ACCENT_BLUE, linewidth=1.5, linestyle='--',
                      label='Win Probability', alpha=0.7)
            )

        legend = ax.legend(handles=legend_elements, loc='upper right',
                          frameon=True, facecolor=self.CARD_BG,
                          edgecolor=self.GRID_COLOR, fontsize=9,
                          labelcolor=self.TEXT_SECONDARY)
        legend.get_frame().set_alpha(0.9)
