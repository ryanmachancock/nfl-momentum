<script lang="ts">
	import { onMount } from 'svelte';
	import { getSeasons, getGames, type Game, type SeasonWeekResponse } from '$lib/api';
	import { selectedSeason, selectedWeek } from '$lib/stores/game';
	import { getTeamLogoUrl } from '$lib/teamLogos';

	export let onGameSelect: (game: Game) => void;

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		cardHover: '#21262d',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		border: '#30363d',
		accentBlue: '#58a6ff',
		accentGreen: '#3fb950',
		accentRed: '#f85149'
	};

	let seasonsData: SeasonWeekResponse | null = null;
	let games: Game[] = [];
	let loading = false;
	let error: string | null = null;

	$: weeks = seasonsData?.weeks_by_season[$selectedSeason ?? 0] ?? [];

	onMount(async () => {
		try {
			seasonsData = await getSeasons();
			// Default to most recent season
			if (seasonsData.seasons.length > 0 && !$selectedSeason) {
				selectedSeason.set(seasonsData.seasons[0]);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load seasons';
		}
	});

	async function loadGames() {
		if (!$selectedSeason || !$selectedWeek) return;

		loading = true;
		error = null;

		try {
			const result = await getGames($selectedSeason, $selectedWeek);
			games = result.games;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load games';
			games = [];
		} finally {
			loading = false;
		}
	}

	$: if ($selectedSeason && $selectedWeek) {
		loadGames();
	}

	function handleSeasonChange(event: Event) {
		const value = (event.target as HTMLSelectElement).value;
		selectedSeason.set(value ? parseInt(value) : null);
		selectedWeek.set(null);
		games = [];
	}

	function handleWeekChange(event: Event) {
		const value = (event.target as HTMLSelectElement).value;
		selectedWeek.set(value ? parseInt(value) : null);
	}

	function formatScore(game: Game): string {
		if (game.home_score !== null && game.away_score !== null) {
			return `${game.away_score} - ${game.home_score}`;
		}
		return '';
	}

	function getWinner(game: Game): 'home' | 'away' | null {
		if (game.home_score === null || game.away_score === null) return null;
		if (game.home_score > game.away_score) return 'home';
		if (game.away_score > game.home_score) return 'away';
		return null;
	}
</script>

<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
	{#if error}
		<div class="p-3 rounded-lg mb-4" style="background-color: {THEME.accentRed}20; border: 1px solid {THEME.accentRed}40;">
			<p style="color: {THEME.accentRed};">{error}</p>
		</div>
	{/if}

	<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
		<!-- Season Selector -->
		<div>
			<label for="season" class="block text-sm font-medium mb-2" style="color: {THEME.text};">
				Season
			</label>
			<select
				id="season"
				class="w-full rounded-lg px-4 py-3 focus:outline-none focus:ring-2"
				style="background-color: {THEME.bg}; color: {THEME.text}; border: 1px solid {THEME.border};"
				value={$selectedSeason ?? ''}
				on:change={handleSeasonChange}
			>
				<option value="">Select season...</option>
				{#if seasonsData}
					{#each seasonsData.seasons as season}
						<option value={season}>{season}</option>
					{/each}
				{/if}
			</select>
		</div>

		<!-- Week Selector -->
		<div>
			<label for="week" class="block text-sm font-medium mb-2" style="color: {THEME.text};">
				Week
			</label>
			<select
				id="week"
				class="w-full rounded-lg px-4 py-3 focus:outline-none focus:ring-2 disabled:opacity-50"
				style="background-color: {THEME.bg}; color: {THEME.text}; border: 1px solid {THEME.border};"
				value={$selectedWeek ?? ''}
				on:change={handleWeekChange}
				disabled={!$selectedSeason}
			>
				<option value="">Select week...</option>
				{#each weeks as week}
					<option value={week}>Week {week}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Games List -->
	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-2 border-t-transparent" style="border-color: {THEME.accentBlue}; border-top-color: transparent;"></div>
		</div>
	{:else if games.length > 0}
		<div class="grid gap-3">
			{#each games as game}
				{@const winner = getWinner(game)}
				<button
					class="w-full text-left p-4 rounded-lg border transition-all hover:scale-[1.01]"
					style="background-color: {THEME.bg}; border-color: {THEME.border};"
					on:mouseenter={(e) => {
						e.currentTarget.style.backgroundColor = THEME.cardHover;
						e.currentTarget.style.borderColor = THEME.accentBlue;
					}}
					on:mouseleave={(e) => {
						e.currentTarget.style.backgroundColor = THEME.bg;
						e.currentTarget.style.borderColor = THEME.border;
					}}
					on:click={() => onGameSelect(game)}
				>
					<div class="flex items-center justify-between">
						<!-- Teams -->
						<div class="flex items-center gap-6">
							<!-- Away Team -->
							<div class="flex items-center gap-3 min-w-[120px]">
								<img
									src={getTeamLogoUrl(game.away_team)}
									alt={game.away_team}
									class="w-8 h-8 object-contain"
									onerror="this.style.display='none'"
								/>
								<span
									class="font-semibold"
									style="color: {winner === 'away' ? THEME.text : THEME.textSecondary};"
								>
									{game.away_team}
								</span>
							</div>

							<span style="color: {THEME.textSecondary};">@</span>

							<!-- Home Team -->
							<div class="flex items-center gap-3 min-w-[120px]">
								<img
									src={getTeamLogoUrl(game.home_team)}
									alt={game.home_team}
									class="w-8 h-8 object-contain"
									onerror="this.style.display='none'"
								/>
								<span
									class="font-semibold"
									style="color: {winner === 'home' ? THEME.text : THEME.textSecondary};"
								>
									{game.home_team}
								</span>
							</div>
						</div>

						<!-- Score & Date -->
						<div class="text-right">
							{#if game.home_score !== null}
								<div class="font-bold text-lg tabular-nums" style="color: {THEME.text};">
									{formatScore(game)}
								</div>
							{/if}
							{#if game.game_date}
								<div class="text-sm" style="color: {THEME.textSecondary};">
									{new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
								</div>
							{/if}
						</div>
					</div>
				</button>
			{/each}
		</div>
	{:else if $selectedSeason && $selectedWeek}
		<div class="text-center py-12">
			<p style="color: {THEME.textSecondary};">
				No games found for Week {$selectedWeek}, {$selectedSeason}
			</p>
		</div>
	{:else}
		<div class="text-center py-12">
			<div class="mb-4">
				<svg class="w-16 h-16 mx-auto opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.textSecondary};">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
			</div>
			<p style="color: {THEME.textSecondary};">
				Select a season and week to view games
			</p>
		</div>
	{/if}
</div>
