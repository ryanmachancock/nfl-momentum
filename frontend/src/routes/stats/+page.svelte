<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getSeasonStats, getSeasons, type SeasonStats, type GameAnalysis } from '$lib/api';

	let stats: SeasonStats | null = null;
	let loading = true;
	let error: string | null = null;
	let selectedSeason = 2024;
	let availableSeasons: number[] = [];

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		grid: '#30363d',
		accentBlue: '#58a6ff',
		accentGreen: '#3fb950',
		accentRed: '#f85149',
		accentYellow: '#d29922'
	};

	onMount(async () => {
		await loadAvailableSeasons();
		await loadStats();
	});

	async function loadAvailableSeasons() {
		try {
			const data = await getSeasons();
			availableSeasons = data.seasons;
			if (availableSeasons.length > 0 && !selectedSeason) {
				selectedSeason = availableSeasons[0];
			}
		} catch (e) {
			console.error('Failed to load seasons:', e);
		}
	}

	async function loadStats() {
		loading = true;
		error = null;

		try {
			stats = await getSeasonStats(selectedSeason);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load season stats';
		} finally {
			loading = false;
		}
	}

	async function handleSeasonChange() {
		await loadStats();
	}

	function viewGame(gameId: string) {
		goto(`/game/${gameId}`);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<svelte:head>
	<title>Season Stats - NFL Momentum</title>
</svelte:head>

<div class="min-h-screen" style="background-color: {THEME.bg};">
	<div class="max-w-7xl mx-auto px-4 py-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold mb-2" style="color: {THEME.text};">Season Statistics</h1>
			<p style="color: {THEME.textSecondary};">
				Validation metrics and momentum analysis for the NFL season
			</p>
		</div>

		<!-- Season Selector -->
		<div class="mb-6">
			<label for="season-select" class="block text-sm font-medium mb-2" style="color: {THEME.text};">
				Select Season
			</label>
			<select
				id="season-select"
				bind:value={selectedSeason}
				on:change={handleSeasonChange}
				class="px-4 py-2 rounded-md border transition-colors"
				style="background-color: {THEME.cardBg}; color: {THEME.text}; border-color: {THEME.grid};"
			>
				{#each availableSeasons as season}
					<option value={season}>{season}</option>
				{/each}
			</select>
		</div>

		{#if loading}
			<div class="flex justify-center py-16">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2" style="border-color: {THEME.accentBlue};"></div>
			</div>
		{:else if error}
			<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.accentRed}40;">
				<h2 class="font-semibold mb-2" style="color: {THEME.accentRed};">Error Loading Stats</h2>
				<p style="color: {THEME.textSecondary};">{error}</p>
				<button
					class="mt-4 px-4 py-2 rounded-md transition-colors"
					style="background-color: {THEME.accentRed}; color: white;"
					on:click={loadStats}
				>
					Retry
				</button>
			</div>
		{:else if stats}
			<!-- Validation Metrics Comparison -->
			<div class="rounded-xl p-6 mb-6" style="background-color: {THEME.cardBg};">
				<h2 class="text-xl font-semibold mb-2" style="color: {THEME.text};">
					Prediction Method Comparison
				</h2>
				<p class="text-sm mb-4" style="color: {THEME.textSecondary};">
					Comparing different ways to use momentum to predict game winners
				</p>

				<!-- Metric Comparison Table -->
				<div class="overflow-x-auto mb-6">
					<table class="w-full">
						<thead>
							<tr style="border-bottom: 1px solid {THEME.grid};">
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">Rank</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">Method</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">Description</th>
								<th class="text-right py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">Accuracy</th>
								<th class="text-right py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">Correct</th>
							</tr>
						</thead>
						<tbody>
							{#each stats.validation_comparison as metric, index}
								<tr
									style="border-bottom: 1px solid {THEME.grid}; {index === 0 ? `background-color: ${THEME.accentGreen}15;` : ''}"
								>
									<td class="py-3 px-4">
										<span class="text-sm font-semibold" style="color: {index === 0 ? THEME.accentGreen : THEME.textSecondary};">
											#{index + 1}
											{#if index === 0}
												<span class="ml-1">★</span>
											{/if}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm font-medium" style="color: {THEME.text};">
											{metric.metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm" style="color: {THEME.textSecondary};">
											{metric.description}
										</span>
									</td>
									<td class="py-3 px-4 text-right">
										<span class="text-lg font-bold" style="color: {index === 0 ? THEME.accentGreen : THEME.text};">
											{metric.percentage}%
										</span>
									</td>
									<td class="py-3 px-4 text-right">
										<span class="text-sm" style="color: {THEME.textSecondary};">
											{metric.correct_predictions}/{metric.total_games}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Summary Stats -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-3xl font-bold mb-1" style="color: {THEME.accentGreen};">
							{stats.best_metric?.percentage ?? 0}%
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Best Prediction Accuracy
						</div>
						<div class="text-xs mt-2" style="color: {THEME.textSecondary};">
							Using: {stats.best_metric?.metric.replace(/_/g, ' ') ?? 'N/A'}
						</div>
					</div>

					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-3xl font-bold mb-1" style="color: {THEME.text};">
							{stats.games_analyzed}
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Games Analyzed
						</div>
						<div class="text-xs mt-2" style="color: {THEME.textSecondary};">
							Out of {stats.total_games} total games
						</div>
					</div>

					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-3xl font-bold mb-1" style="color: {THEME.accentBlue};">
							{stats.average_swing_per_game.toFixed(1)}
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Avg. Swing Per Game
						</div>
						<div class="text-xs mt-2" style="color: {THEME.textSecondary};">
							Average momentum swing
						</div>
					</div>
				</div>

				<div class="mt-4 p-4 rounded-lg" style="background-color: {THEME.accentGreen}20; border: 1px solid {THEME.accentGreen}40;">
					<div class="font-medium" style="color: {THEME.accentGreen};">
						Best Predictor: {stats.best_metric?.metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) ?? 'N/A'}
					</div>
					<div class="text-sm mt-1" style="color: {THEME.textSecondary};">
						{stats.best_metric?.description ?? ''} correctly predicted the winner in {stats.best_metric?.percentage ?? 0}% of games.
						{#if (stats.best_metric?.percentage ?? 0) > 60}
							This is significantly better than a coin flip (50%), showing momentum is a meaningful predictor.
						{:else}
							This suggests momentum alone may not be a strong predictor of game outcomes.
						{/if}
					</div>
				</div>
			</div>

			<!-- Games by Volatility -->
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<h2 class="text-xl font-semibold mb-4" style="color: {THEME.text};">
					Games Ranked by Momentum Volatility
				</h2>
				<p class="text-sm mb-4" style="color: {THEME.textSecondary};">
					Games with the most momentum swings - the most exciting matchups of the season
				</p>

				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr style="border-bottom: 1px solid {THEME.grid};">
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Rank
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Week
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Matchup
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Score
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Volatility
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Biggest Swing
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Predicted
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">

								</th>
							</tr>
						</thead>
						<tbody>
							{#each stats.games_by_volatility.slice(0, 20) as game, index}
								<tr
									class="transition-colors cursor-pointer"
									style="border-bottom: 1px solid {THEME.grid};"
									on:mouseenter={(e) => e.currentTarget.style.backgroundColor = THEME.bg}
									on:mouseleave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
								>
									<td class="py-3 px-4">
										<span class="text-sm font-semibold" style="color: {THEME.textSecondary};">
											#{index + 1}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm" style="color: {THEME.text};">
											{game.week}
										</span>
									</td>
									<td class="py-3 px-4">
										<div class="text-sm" style="color: {THEME.text};">
											{game.away_team} @ {game.home_team}
										</div>
										{#if game.game_date}
											<div class="text-xs" style="color: {THEME.textSecondary};">
												{formatDate(game.game_date)}
											</div>
										{/if}
									</td>
									<td class="py-3 px-4">
										<span class="text-sm font-medium" style="color: {THEME.text};">
											{game.away_score} - {game.home_score}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm font-bold" style="color: {THEME.accentYellow};">
											{game.total_volatility.toFixed(1)}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm" style="color: {THEME.text};">
											{game.biggest_swing.toFixed(1)}
										</span>
										{#if game.biggest_swing_quarter}
											<span class="text-xs ml-1" style="color: {THEME.textSecondary};">
												(Q{game.biggest_swing_quarter})
											</span>
										{/if}
									</td>
									<td class="py-3 px-4">
										{#if game.predicted_correctly}
											<span class="text-xs px-2 py-1 rounded" style="background-color: {THEME.accentGreen}20; color: {THEME.accentGreen};">
												Correct
											</span>
										{:else}
											<span class="text-xs px-2 py-1 rounded" style="background-color: {THEME.accentRed}20; color: {THEME.accentRed};">
												Wrong
											</span>
										{/if}
									</td>
									<td class="py-3 px-4">
										<button
											class="text-xs px-3 py-1 rounded transition-colors"
											style="background-color: {THEME.accentBlue}; color: white;"
											on:click={() => viewGame(game.game_id)}
										>
											View
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				{#if stats.games_by_volatility.length > 20}
					<div class="mt-4 text-center text-sm" style="color: {THEME.textSecondary};">
						Showing top 20 of {stats.games_by_volatility.length} games
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
