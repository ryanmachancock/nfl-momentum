<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Chart, LineController, LinearScale, PointElement, LineElement, CategoryScale, Filler, Tooltip, Legend } from 'chart.js';
	import type { MomentumDataPoint, Game } from '$lib/api';
	import { getTeamLogoUrl } from '$lib/teamLogos';

	export let dataPoints: MomentumDataPoint[];
	export let game: Game;
	export let showWinProbability = true;
	export let highlightedPlayId: number | null = null;

	const dispatch = createEventDispatcher<{
		playHover: { playId: number | null; index: number | null };
	}>();

	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	// Interactive scoreboard state
	let hoveredScore: { away: number; home: number; quarter: number; time: string } | null = null;

	// Quarter-end scores (calculated from data)
	let quarterScores: { quarter: number; away: number; home: number }[] = [];

	// Modern team colors (optimized for dark backgrounds)
	const TEAM_COLORS: Record<string, string> = {
		ARI: '#97233F', ATL: '#A71930', BAL: '#241773', BUF: '#00338D',
		CAR: '#0085CA', CHI: '#C83803', CIN: '#FB4F14', CLE: '#FF3C00',
		DAL: '#003594', DEN: '#FB4F14', DET: '#0076B6', GB: '#203731',
		HOU: '#03202F', IND: '#002C5F', JAX: '#006778', KC: '#E31837',
		LA: '#003594', LAC: '#0080C6', LV: '#A5ACAF', MIA: '#008E97',
		MIN: '#4F2683', NE: '#002244', NO: '#D3BC8D', NYG: '#0B2265',
		NYJ: '#125740', PHI: '#004C54', PIT: '#FFB612', SEA: '#69BE28',
		SF: '#AA0000', TB: '#D50A0A', TEN: '#4B92DB', WAS: '#773141',
		SD: '#0080C6', STL: '#003594', OAK: '#A5ACAF'
	};

	// Modern dark theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		grid: '#30363d',
		accentBlue: '#58a6ff',
		accentGreen: '#3fb950',
		accentRed: '#f85149'
	};

	const DEFAULT_HOME_COLOR = THEME.accentGreen;
	const DEFAULT_AWAY_COLOR = THEME.accentRed;

	function getTeamColor(team: string, fallback: string): string {
		return TEAM_COLORS[team] || fallback;
	}

	/**
	 * Calculate the score at the end of each quarter from play data.
	 */
	function calculateQuarterScores() {
		quarterScores = [];

		// Group plays by quarter and find the last play of each quarter
		const quarters = new Map<number, MomentumDataPoint>();

		for (const dp of dataPoints) {
			if (dp.home_score !== null && dp.away_score !== null) {
				// Keep track of the last play we've seen for each quarter
				const existing = quarters.get(dp.quarter);
				if (!existing) {
					quarters.set(dp.quarter, dp);
				} else {
					// Compare game time - later in quarter means lower time remaining
					const existingTime = parseGameTime(existing.quarter, existing.time_remaining);
					const currentTime = parseGameTime(dp.quarter, dp.time_remaining);
					if (currentTime > existingTime) {
						quarters.set(dp.quarter, dp);
					}
				}
			}
		}

		// Convert to array sorted by quarter
		quarterScores = Array.from(quarters.entries())
			.sort((a, b) => a[0] - b[0])
			.map(([quarter, dp]) => ({
				quarter,
				away: dp.away_score ?? 0,
				home: dp.home_score ?? 0
			}));
	}

	/**
	 * Convert time_remaining (MM:SS) and quarter to absolute game time in minutes.
	 * Q1: 0-15 min, Q2: 15-30 min, Q3: 30-45 min, Q4: 45-60 min, OT: 60+ min
	 */
	function parseGameTime(quarter: number, timeRemaining: string): number {
		// Parse "MM:SS" or "M:SS" format
		const parts = timeRemaining.split(':');
		if (parts.length !== 2) {
			// Fallback: assume start of quarter
			return (quarter - 1) * 15;
		}

		const minutes = parseInt(parts[0], 10) || 0;
		const seconds = parseInt(parts[1], 10) || 0;
		const timeRemainingMinutes = minutes + seconds / 60;

		// Game time = (quarter - 1) * 15 + (15 - time_remaining)
		// e.g., Q1 with 14:30 remaining = 0 + (15 - 14.5) = 0.5 min into game
		// e.g., Q2 with 10:00 remaining = 15 + (15 - 10) = 20 min into game
		const quarterStartTime = (quarter - 1) * 15;
		const elapsedInQuarter = 15 - timeRemainingMinutes;

		return quarterStartTime + Math.max(0, elapsedInQuarter);
	}

	function createChart() {
		if (!canvas || !dataPoints.length) return;

		const homeColor = getTeamColor(game.home_team, DEFAULT_HOME_COLOR);
		const awayColor = getTeamColor(game.away_team, DEFAULT_AWAY_COLOR);

		// Convert data to time-based x values
		const timeData = dataPoints.map((dp, index) => ({
			x: parseGameTime(dp.quarter, dp.time_remaining),
			y: dp.home_momentum,
			index,
			dataPoint: dp
		}));

		// Win probability data (also time-based)
		const wpData = dataPoints.map((dp, index) => {
			if (dp.home_wp === null) return null;
			return {
				x: parseGameTime(dp.quarter, dp.time_remaining),
				y: (dp.home_wp - 0.5) * 200,
				index
			};
		}).filter(d => d !== null);

		// Determine max time (handle overtime)
		const maxTime = Math.max(...timeData.map(d => d.x), 60);

		const datasets: any[] = [
			{
				label: 'Momentum',
				data: timeData,
				borderColor: '#ffffff',
				borderWidth: 2,
				fill: {
					target: 'origin',
					above: homeColor + '99',
					below: awayColor + '99'
				},
				tension: 0.3,
				pointRadius: (ctx: any) => {
					const dp = dataPoints[ctx.dataIndex];
					return dp?.is_significant ? 6 : 0;
				},
				pointHoverRadius: (ctx: any) => {
					const dp = dataPoints[ctx.dataIndex];
					return dp?.is_significant ? 10 : 4;
				},
				pointBackgroundColor: (ctx: any) => {
					const dp = dataPoints[ctx.dataIndex];
					if (!dp?.is_significant) return 'transparent';
					return dp.momentum_delta > 0 ? homeColor : awayColor;
				},
				pointHoverBackgroundColor: (ctx: any) => {
					const dp = dataPoints[ctx.dataIndex];
					return dp.momentum_delta > 0 ? homeColor : awayColor;
				},
				pointBorderColor: '#ffffff',
				pointHoverBorderColor: '#ffffff',
				pointBorderWidth: 2,
				pointHoverBorderWidth: 3,
				order: 1
			}
		];

		// Add win probability line if enabled
		if (showWinProbability && wpData.length > 0) {
			datasets.push({
				label: 'Win Probability',
				data: wpData,
				borderColor: '#ffd700', // Bright yellow for better visibility
				borderWidth: 2,
				borderDash: [8, 4], // Dashed line for better readability
				fill: false,
				tension: 0.4,
				pointRadius: 0,
				order: 2
			});
		}

		chart = new Chart(canvas, {
			type: 'line',
			data: { datasets },
			options: {
				responsive: true,
				maintainAspectRatio: false,
				parsing: false, // Data already in {x, y} format
				interaction: {
					intersect: false,
					mode: 'nearest',
					axis: 'x'
				},
				onHover: (event, elements) => {
					if (elements.length > 0 && elements[0].datasetIndex === 0) {
						const index = elements[0].index;
						const dp = dataPoints[index];
						if (dp && dp.home_score !== null && dp.away_score !== null) {
							hoveredScore = {
								away: dp.away_score,
								home: dp.home_score,
								quarter: dp.quarter,
								time: dp.time_remaining
							};
						}
						// Dispatch event for list sync
						if (dp?.is_significant) {
							dispatch('playHover', { playId: dp.play_id, index });
						}
					} else {
						hoveredScore = null;
						dispatch('playHover', { playId: null, index: null });
					}
				},
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						backgroundColor: THEME.cardBg,
						titleColor: THEME.text,
						bodyColor: THEME.textSecondary,
						borderColor: THEME.grid,
						borderWidth: 1,
						padding: 12,
						displayColors: false,
						titleFont: {
							size: 13,
							weight: 'bold'
						},
						bodyFont: {
							size: 12
						},
						callbacks: {
							title: (items) => {
								const item = items[0];
								if (item.datasetIndex === 0) {
									const dp = dataPoints[item.dataIndex];
									// Event description is the title (what happened)
									return dp.event_description || 'Play';
								}
								return '';
							},
							afterTitle: (items) => {
								const item = items[0];
								if (item.datasetIndex === 0) {
									const dp = dataPoints[item.dataIndex];
									// Game time context
									return `Q${dp.quarter} · ${dp.time_remaining}`;
								}
								return '';
							},
							label: (ctx) => {
								if (ctx.datasetIndex === 0) {
									const dp = dataPoints[ctx.dataIndex];
									const lines: string[] = [''];

									// Momentum shift in natural language
									const absDelta = Math.abs(dp.momentum_delta);
									const team = dp.momentum_delta > 0 ? game.home_team : game.away_team;
									const arrow = dp.momentum_delta > 0 ? '↑' : '↓';

									// Categorize magnitude
									let magnitude = '';
									if (absDelta >= 25) magnitude = 'Huge swing';
									else if (absDelta >= 15) magnitude = 'Big swing';
									else if (absDelta >= 8) magnitude = 'Moderate shift';
									else if (absDelta >= 3) magnitude = 'Small shift';
									else magnitude = 'Minimal change';

									lines.push(`${arrow} ${magnitude} for ${team}`);

									return lines;
								}
								return [];
							}
						}
					}
				},
				scales: {
					x: {
						type: 'linear',
						display: true,
						min: 0,
						max: maxTime,
						grid: {
							color: (ctx) => {
								// Show grid lines at quarter boundaries
								if (ctx.tick.value % 15 === 0) return THEME.grid;
								return 'transparent';
							},
							lineWidth: 1
						},
						ticks: {
							color: THEME.textSecondary,
							font: { size: 11 },
							stepSize: 15,
							callback: (value) => {
								const quarter = Math.floor(Number(value) / 15) + 1;
								if (Number(value) % 15 === 0) {
									if (quarter <= 4) return `Q${quarter}`;
									return `OT${quarter - 4}`;
								}
								return '';
							}
						},
						border: {
							display: false
						}
					},
					y: {
						display: true,
						min: -100,
						max: 100,
						grid: {
							color: (ctx) => {
								if (ctx.tick.value === 0) return THEME.grid;
								return THEME.grid + '40';
							},
							lineWidth: (ctx) => ctx.tick.value === 0 ? 2 : 1
						},
						ticks: {
							color: THEME.textSecondary,
							font: { size: 11 },
							stepSize: 25,
							callback: (value) => {
								if (value === 0) return '0';
								if (value === 50 || value === -50) return '';
								if (value === 100) return game.home_team;
								if (value === -100) return game.away_team;
								return '';
							}
						},
						border: {
							display: false
						}
					}
				}
			}
		});
	}

	onMount(() => {
		Chart.register(LineController, LinearScale, PointElement, LineElement, CategoryScale, Filler, Tooltip, Legend);
		calculateQuarterScores();
		createChart();
	});

	onDestroy(() => {
		if (chart) {
			chart.destroy();
			chart = null;
		}
	});

	$: if (chart && dataPoints) {
		chart.destroy();
		calculateQuarterScores();
		createChart();
	}

	// Highlight a specific point when highlightedPlayId changes
	$: if (chart && highlightedPlayId !== null) {
		const index = dataPoints.findIndex(dp => dp.play_id === highlightedPlayId);
		if (index >= 0) {
			// Show tooltip and scroll chart to this point
			chart.setActiveElements([{ datasetIndex: 0, index }]);
			chart.tooltip?.setActiveElements([{ datasetIndex: 0, index }], { x: 0, y: 0 });
			chart.update('none');

			// Update scoreboard
			const dp = dataPoints[index];
			if (dp && dp.home_score !== null && dp.away_score !== null) {
				hoveredScore = {
					away: dp.away_score,
					home: dp.home_score,
					quarter: dp.quarter,
					time: dp.time_remaining
				};
			}
		}
	} else if (chart && highlightedPlayId === null) {
		chart.setActiveElements([]);
		chart.tooltip?.setActiveElements([], { x: 0, y: 0 });
		chart.update('none');
		hoveredScore = null;
	}

	// Expose a method to highlight a specific play
	export function highlightPlay(playId: number | null) {
		highlightedPlayId = playId;
	}
</script>

<div class="chart-container rounded-xl overflow-hidden" style="background-color: {THEME.cardBg};">
	<!-- Header -->
	<div class="p-6 pb-4">
		<div class="flex flex-col sm:flex-row justify-between items-start gap-3">
			<div>
				<!-- Team logos and matchup -->
				<div class="flex items-center gap-4 mb-2">
					<div class="flex items-center gap-2">
						<img
							src={getTeamLogoUrl(game.away_team)}
							alt={game.away_team}
							class="w-10 h-10 object-contain"
							onerror="this.style.display='none'"
						/>
						<span class="text-2xl font-bold" style="color: {THEME.text};">{game.away_team}</span>
					</div>
					<span class="text-xl" style="color: {THEME.textSecondary};">@</span>
					<div class="flex items-center gap-2">
						<img
							src={getTeamLogoUrl(game.home_team)}
							alt={game.home_team}
							class="w-10 h-10 object-contain"
							onerror="this.style.display='none'"
						/>
						<span class="text-2xl font-bold" style="color: {THEME.text};">{game.home_team}</span>
					</div>
				</div>
				<p style="color: {THEME.textSecondary};" class="mt-1">
					Week {game.week}, {game.season}
					{#if game.home_score !== null}
						<span class="ml-2 font-semibold" style="color: {THEME.accentBlue};">
							Final: {game.away_score} - {game.home_score}
						</span>
					{/if}
				</p>
			</div>
			<div class="flex flex-col gap-2 text-sm">
				<div class="flex items-center">
					<div
						class="w-4 h-4 rounded mr-2"
						style="background-color: {getTeamColor(game.home_team, DEFAULT_HOME_COLOR)};"
					></div>
					<span style="color: {THEME.textSecondary};">{game.home_team} Momentum</span>
				</div>
				<div class="flex items-center">
					<div
						class="w-4 h-4 rounded mr-2"
						style="background-color: {getTeamColor(game.away_team, DEFAULT_AWAY_COLOR)};"
					></div>
					<span style="color: {THEME.textSecondary};">{game.away_team} Momentum</span>
				</div>
				{#if showWinProbability}
					<div class="flex items-center">
						<div
							class="w-4 h-0.5 mr-2 border-t-2 border-dashed"
							style="border-color: #ffd700;"
						></div>
						<span style="color: {THEME.textSecondary};">Win Probability</span>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Interactive Scoreboard -->
	<div class="px-6 pb-4">
		<div class="flex items-center justify-center gap-8 p-4 rounded-lg" style="background-color: {THEME.bg};">
			<!-- Away Team Score -->
			<div class="flex items-center gap-3">
				<img
					src={getTeamLogoUrl(game.away_team)}
					alt={game.away_team}
					class="w-8 h-8 object-contain"
					onerror="this.style.display='none'"
				/>
				<span class="text-lg font-semibold" style="color: {THEME.text};">{game.away_team}</span>
				<span class="text-3xl font-bold tabular-nums" style="color: {getTeamColor(game.away_team, DEFAULT_AWAY_COLOR)};">
					{hoveredScore ? hoveredScore.away : (game.away_score ?? 0)}
				</span>
			</div>

			<!-- Game Time -->
			<div class="text-center min-w-[100px]">
				{#if hoveredScore}
					<div class="text-sm font-medium" style="color: {THEME.accentBlue};">
						Q{hoveredScore.quarter} · {hoveredScore.time}
					</div>
				{:else}
					<div class="text-sm font-medium" style="color: {THEME.textSecondary};">
						Final
					</div>
				{/if}
			</div>

			<!-- Home Team Score -->
			<div class="flex items-center gap-3">
				<span class="text-3xl font-bold tabular-nums" style="color: {getTeamColor(game.home_team, DEFAULT_HOME_COLOR)};">
					{hoveredScore ? hoveredScore.home : (game.home_score ?? 0)}
				</span>
				<span class="text-lg font-semibold" style="color: {THEME.text};">{game.home_team}</span>
				<img
					src={getTeamLogoUrl(game.home_team)}
					alt={game.home_team}
					class="w-8 h-8 object-contain"
					onerror="this.style.display='none'"
				/>
			</div>
		</div>

	</div>

	<!-- Quarter Scores Timeline -->
	{#if quarterScores.length > 0}
		<div class="px-6 pb-4">
			<div class="flex justify-around items-center">
				{#each quarterScores as qs}
					<div class="text-center px-3 py-2 rounded" style="background-color: {THEME.bg};">
						<div class="text-xs font-medium mb-1" style="color: {THEME.textSecondary};">
							{qs.quarter <= 4 ? `End Q${qs.quarter}` : `End OT${qs.quarter - 4}`}
						</div>
						<div class="text-sm font-semibold" style="color: {THEME.text};">
							<span style="color: {getTeamColor(game.away_team, DEFAULT_AWAY_COLOR)};">{qs.away}</span>
							<span style="color: {THEME.textSecondary};"> - </span>
							<span style="color: {getTeamColor(game.home_team, DEFAULT_HOME_COLOR)};">{qs.home}</span>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Chart -->
	<div class="h-96 px-4 pb-6">
		<canvas bind:this={canvas}></canvas>
	</div>
</div>

<style>
	.chart-container {
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
	}
</style>
