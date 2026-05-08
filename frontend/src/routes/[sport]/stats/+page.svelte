<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getSeasonStats, getSeasons, getTopMomentumGames, getStatsOverview, type SeasonStats, type GameAnalysis, type TopMomentumGame, type StatsOverview } from '$lib/api';

	let stats: SeasonStats | null = null;
	let topGames: TopMomentumGame[] = [];
	let overview: StatsOverview | null = null;
	let loading = true;
	let error: string | null = null;
	let selectedSeason: number | 'all' = 'all';
	let selectedCategory: 'swings' | 'comebacks' | 'blowouts' | 'close' = 'swings';
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

	const CATEGORIES = [
		{ id: 'swings' as const, label: 'Biggest Swings', description: 'Games with the largest single momentum shifts' },
		{ id: 'comebacks' as const, label: 'Wild Rides', description: 'Most volatile games with constant momentum changes' },
		{ id: 'blowouts' as const, label: 'Dominant Wins', description: 'Games with most one-sided momentum' },
		{ id: 'close' as const, label: 'Nail Biters', description: 'Games with competitive momentum throughout' }
	];

	$: sport = $page.params.sport;
	$: sportName = sport?.toUpperCase() || 'NFL';

	onMount(async () => {
		await loadAvailableSeasons();
		await loadData();
	});

	async function loadAvailableSeasons() {
		try {
			const data = await getSeasons();
			availableSeasons = data.seasons;
		} catch (e) {
			console.error('Failed to load seasons:', e);
		}
	}

	async function loadData() {
		loading = true;
		error = null;

		try {
			const seasonNum = selectedSeason === 'all' ? undefined : selectedSeason;

			const [topData, overviewData, seasonStats] = await Promise.all([
				getTopMomentumGames(selectedCategory, seasonNum, 25),
				getStatsOverview(seasonNum),
				selectedSeason !== 'all' ? getSeasonStats(selectedSeason) : Promise.resolve(null)
			]);

			topGames = topData.games;
			overview = overviewData;
			stats = seasonStats;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load stats';
		} finally {
			loading = false;
		}
	}

	async function handleSeasonChange() {
		await loadData();
	}

	async function handleCategoryChange(category: typeof selectedCategory) {
		selectedCategory = category;
		await loadData();
	}

	function viewGame(gameId: string) {
		goto(`/${sport}/game/${gameId}`);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}

	function getPredictionResult(game: TopMomentumGame): 'correct' | 'incorrect' | 'unknown' {
		if (game.home_score === null || game.away_score === null) return 'unknown';
		const actualHomeWin = game.home_score > game.away_score;
		const momentumHomeWin = game.final_home_momentum > game.final_away_momentum;
		return actualHomeWin === momentumHomeWin ? 'correct' : 'incorrect';
	}
</script>

<svelte:head>
	<title>Stats - {sportName} Momentum</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold mb-2" style="color: {THEME.text};">Momentum Statistics</h1>
		<p style="color: {THEME.textSecondary};">
			Explore the most interesting {sportName} games by momentum patterns across {selectedSeason === 'all' ? 'all seasons' : selectedSeason}
		</p>
	</div>

	<!-- Filters Row -->
	<div class="mb-6 flex flex-col md:flex-row gap-4">
		<!-- Season Selector -->
		<div>
			<label for="season-select" class="block text-sm font-medium mb-2" style="color: {THEME.text};">
				Season
			</label>
			<select
				id="season-select"
				bind:value={selectedSeason}
				on:change={handleSeasonChange}
				class="px-4 py-2 rounded-md border transition-colors min-w-[140px]"
				style="background-color: {THEME.cardBg}; color: {THEME.text}; border-color: {THEME.grid};"
			>
				<option value="all">All Seasons</option>
				{#each availableSeasons as season}
					<option value={season}>{season}</option>
				{/each}
			</select>
		</div>

		<!-- Category Tabs -->
		<div class="flex-1">
			<label class="block text-sm font-medium mb-2" style="color: {THEME.text};">
				Category
			</label>
			<div class="flex flex-wrap gap-2">
				{#each CATEGORIES as cat}
					<button
						class="px-4 py-2 rounded-md text-sm font-medium transition-all"
						style="background-color: {selectedCategory === cat.id ? THEME.accentBlue : THEME.cardBg};
						       color: {selectedCategory === cat.id ? 'white' : THEME.text};
						       border: 1px solid {selectedCategory === cat.id ? THEME.accentBlue : THEME.grid};"
						on:click={() => handleCategoryChange(cat.id)}
					>
						{cat.label}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- Overview Stats -->
	{#if overview && !loading}
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<div class="text-3xl font-bold mb-1" style="color: {THEME.text};">
					{overview.total_games.toLocaleString()}
				</div>
				<div class="text-sm" style="color: {THEME.textSecondary};">Games Analyzed</div>
			</div>
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<div class="text-3xl font-bold mb-1" style="color: {THEME.accentGreen};">
					{overview.accuracy_percentage}%
				</div>
				<div class="text-sm" style="color: {THEME.textSecondary};">Prediction Accuracy</div>
			</div>
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<div class="text-3xl font-bold mb-1" style="color: {THEME.accentBlue};">
					{overview.correct_predictions.toLocaleString()}
				</div>
				<div class="text-sm" style="color: {THEME.textSecondary};">Correct Predictions</div>
			</div>
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<div class="text-3xl font-bold mb-1" style="color: {THEME.text};">
					{overview.home_wins} - {overview.away_wins}
				</div>
				<div class="text-sm" style="color: {THEME.textSecondary};">Home - Away Wins</div>
			</div>
		</div>
	{/if}

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
				on:click={loadData}
			>
				Retry
			</button>
		</div>
	{:else}
		<!-- Top Games List -->
		<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
			<div class="flex items-center justify-between mb-4">
				<div>
					<h2 class="text-xl font-semibold" style="color: {THEME.text};">
						{CATEGORIES.find(c => c.id === selectedCategory)?.label || 'Top Games'}
					</h2>
					<p class="text-sm" style="color: {THEME.textSecondary};">
						{CATEGORIES.find(c => c.id === selectedCategory)?.description || ''}
					</p>
				</div>
				<span class="text-sm" style="color: {THEME.textSecondary};">
					{topGames.length} games
				</span>
			</div>

			{#if topGames.length === 0}
				<div class="text-center py-8" style="color: {THEME.textSecondary};">
					No games found for the selected criteria
				</div>
			{:else}
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr style="border-bottom: 1px solid {THEME.grid};">
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Rank
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Season
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Matchup
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Score
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									{selectedCategory === 'swings' ? 'Max Swing' : 'Volatility'}
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Final Momentum
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
									Prediction
								</th>
								<th class="text-left py-3 px-4 text-sm font-semibold" style="color: {THEME.text};">
								</th>
							</tr>
						</thead>
						<tbody>
							{#each topGames as game, index}
								{@const prediction = getPredictionResult(game)}
								<tr
									class="transition-colors cursor-pointer"
									style="border-bottom: 1px solid {THEME.grid};"
									on:mouseenter={(e) => e.currentTarget.style.backgroundColor = THEME.bg}
									on:mouseleave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
									on:click={() => viewGame(game.game_id)}
								>
									<td class="py-3 px-4">
										<span class="text-sm font-semibold" style="color: {index < 3 ? THEME.accentYellow : THEME.textSecondary};">
											#{index + 1}
											{#if index === 0}
												<span class="ml-1">🏆</span>
											{:else if index === 1}
												<span class="ml-1">🥈</span>
											{:else if index === 2}
												<span class="ml-1">🥉</span>
											{/if}
										</span>
									</td>
									<td class="py-3 px-4">
										<div class="text-sm font-medium" style="color: {THEME.text};">
											{game.season}
										</div>
										<div class="text-xs" style="color: {THEME.textSecondary};">
											Week {game.week}
										</div>
									</td>
									<td class="py-3 px-4">
										<div class="text-sm font-medium" style="color: {THEME.text};">
											{game.away_team} @ {game.home_team}
										</div>
										{#if game.game_date}
											<div class="text-xs" style="color: {THEME.textSecondary};">
												{formatDate(game.game_date)}
											</div>
										{/if}
									</td>
									<td class="py-3 px-4">
										<span class="text-sm font-bold tabular-nums" style="color: {THEME.text};">
											{game.away_score ?? '-'} - {game.home_score ?? '-'}
										</span>
									</td>
									<td class="py-3 px-4">
										<span class="text-sm font-bold" style="color: {THEME.accentYellow};">
											{selectedCategory === 'swings'
												? game.max_swing?.toFixed(1) || '-'
												: game.total_volatility?.toFixed(1) || '-'}
										</span>
									</td>
									<td class="py-3 px-4">
										<div class="flex items-center gap-2">
											<span class="text-xs px-2 py-0.5 rounded" style="background-color: {THEME.accentGreen}20; color: {THEME.accentGreen};">
												{game.home_team} {game.final_home_momentum > 0 ? '+' : ''}{game.final_home_momentum?.toFixed(1) || '0'}
											</span>
											<span class="text-xs px-2 py-0.5 rounded" style="background-color: {THEME.accentRed}20; color: {THEME.accentRed};">
												{game.away_team} {game.final_away_momentum > 0 ? '+' : ''}{game.final_away_momentum?.toFixed(1) || '0'}
											</span>
										</div>
									</td>
									<td class="py-3 px-4">
										{#if prediction === 'correct'}
											<span class="text-xs px-2 py-1 rounded" style="background-color: {THEME.accentGreen}20; color: {THEME.accentGreen};">
												Correct
											</span>
										{:else if prediction === 'incorrect'}
											<span class="text-xs px-2 py-1 rounded" style="background-color: {THEME.accentRed}20; color: {THEME.accentRed};">
												Wrong
											</span>
										{:else}
											<span class="text-xs px-2 py-1 rounded" style="background-color: {THEME.grid}; color: {THEME.textSecondary};">
												-
											</span>
										{/if}
									</td>
									<td class="py-3 px-4">
										<button
											class="text-xs px-3 py-1 rounded transition-colors"
											style="background-color: {THEME.accentBlue}; color: white;"
											on:click|stopPropagation={() => viewGame(game.game_id)}
										>
											View
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Season-specific detailed stats -->
		{#if stats && selectedSeason !== 'all'}
			<div class="mt-6 rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<h2 class="text-xl font-semibold mb-4" style="color: {THEME.text};">
					{selectedSeason} Season Details
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-2xl font-bold" style="color: {THEME.accentGreen};">
							{stats.best_metric?.percentage ?? 0}%
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Best Prediction Method
						</div>
						<div class="text-xs mt-1" style="color: {THEME.textSecondary};">
							{stats.best_metric?.metric.replace(/_/g, ' ') ?? 'N/A'}
						</div>
					</div>
					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-2xl font-bold" style="color: {THEME.text};">
							{stats.games_analyzed}
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Games Analyzed
						</div>
					</div>
					<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
						<div class="text-2xl font-bold" style="color: {THEME.accentBlue};">
							{stats.average_swing_per_game?.toFixed(1) ?? '0'}
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							Avg Swing Per Game
						</div>
					</div>
				</div>

				{#if stats.validation_comparison && stats.validation_comparison.length > 0}
					<div class="overflow-x-auto">
						<table class="w-full">
							<thead>
								<tr style="border-bottom: 1px solid {THEME.grid};">
									<th class="text-left py-2 px-4 text-sm" style="color: {THEME.text};">Method</th>
									<th class="text-left py-2 px-4 text-sm" style="color: {THEME.text};">Description</th>
									<th class="text-right py-2 px-4 text-sm" style="color: {THEME.text};">Accuracy</th>
								</tr>
							</thead>
							<tbody>
								{#each stats.validation_comparison as metric, idx}
									<tr style="border-bottom: 1px solid {THEME.grid}; {idx === 0 ? `background-color: ${THEME.accentGreen}10;` : ''}">
										<td class="py-2 px-4 text-sm" style="color: {idx === 0 ? THEME.accentGreen : THEME.text};">
											{metric.metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
											{#if idx === 0}★{/if}
										</td>
										<td class="py-2 px-4 text-sm" style="color: {THEME.textSecondary};">
											{metric.description}
										</td>
										<td class="py-2 px-4 text-sm text-right font-bold" style="color: {idx === 0 ? THEME.accentGreen : THEME.text};">
											{metric.percentage}%
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
