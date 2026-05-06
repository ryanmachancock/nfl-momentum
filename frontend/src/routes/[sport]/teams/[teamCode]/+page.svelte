<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getTeamLogoUrl } from '$lib/teamLogos';
	import type { Game } from '$lib/api';

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		border: '#30363d',
		accentBlue: '#58a6ff',
		accentGreen: '#3fb950',
		accentRed: '#f85149',
		accentYellow: '#d29922'
	};

	$: sport = $page.params.sport;
	$: teamCode = $page.params.teamCode;
	$: sportName = sport?.toUpperCase() || 'NFL';

	const TEAM_NAMES: Record<string, string> = {
		'ARI': 'Arizona Cardinals',
		'ATL': 'Atlanta Falcons',
		'BAL': 'Baltimore Ravens',
		'BUF': 'Buffalo Bills',
		'CAR': 'Carolina Panthers',
		'CHI': 'Chicago Bears',
		'CIN': 'Cincinnati Bengals',
		'CLE': 'Cleveland Browns',
		'DAL': 'Dallas Cowboys',
		'DEN': 'Denver Broncos',
		'DET': 'Detroit Lions',
		'GB': 'Green Bay Packers',
		'HOU': 'Houston Texans',
		'IND': 'Indianapolis Colts',
		'JAX': 'Jacksonville Jaguars',
		'KC': 'Kansas City Chiefs',
		'LAC': 'Los Angeles Chargers',
		'LAR': 'Los Angeles Rams',
		'LV': 'Las Vegas Raiders',
		'MIA': 'Miami Dolphins',
		'MIN': 'Minnesota Vikings',
		'NE': 'New England Patriots',
		'NO': 'New Orleans Saints',
		'NYG': 'New York Giants',
		'NYJ': 'New York Jets',
		'PHI': 'Philadelphia Eagles',
		'PIT': 'Pittsburgh Steelers',
		'SEA': 'Seattle Seahawks',
		'SF': 'San Francisco 49ers',
		'TB': 'Tampa Bay Buccaneers',
		'TEN': 'Tennessee Titans',
		'WAS': 'Washington Commanders'
	};

	$: teamName = TEAM_NAMES[teamCode.toUpperCase()] || teamCode;

	let games: Game[] = [];
	let loading = true;
	let error: string | null = null;
	let selectedSeason = 2024;

	// Stats
	$: totalGames = games.length;
	$: wins = games.filter(g => {
		if (g.home_score === null || g.away_score === null) return false;
		if (g.home_team === teamCode.toUpperCase()) {
			return g.home_score > g.away_score;
		} else {
			return g.away_score > g.home_score;
		}
	}).length;
	$: losses = games.filter(g => {
		if (g.home_score === null || g.away_score === null) return false;
		if (g.home_team === teamCode.toUpperCase()) {
			return g.home_score < g.away_score;
		} else {
			return g.away_score < g.home_score;
		}
	}).length;
	$: homeGames = games.filter(g => g.home_team === teamCode.toUpperCase());
	$: awayGames = games.filter(g => g.away_team === teamCode.toUpperCase());

	onMount(async () => {
		await loadTeamGames();
	});

	async function loadTeamGames() {
		loading = true;
		error = null;

		try {
			const response = await fetch(
				`http://localhost:8000/api/games/search?q=${encodeURIComponent(teamCode)}&limit=100`
			);

			if (!response.ok) {
				throw new Error('Failed to load team games');
			}

			const data = await response.json();
			games = (data.games || []).sort((a: Game, b: Game) => {
				// Sort by season desc, then week desc
				if (a.season !== b.season) return b.season - a.season;
				return b.week - a.week;
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load team data';
		} finally {
			loading = false;
		}
	}

	function viewGame(gameId: string) {
		goto(`/${sport}/game/${gameId}`);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function getGameResult(game: Game): 'W' | 'L' | 'T' | null {
		if (game.home_score === null || game.away_score === null) return null;

		const isHome = game.home_team === teamCode.toUpperCase();
		const teamScore = isHome ? game.home_score : game.away_score;
		const oppScore = isHome ? game.away_score : game.home_score;

		if (teamScore > oppScore) return 'W';
		if (teamScore < oppScore) return 'L';
		return 'T';
	}

	function getOpponent(game: Game): string {
		return game.home_team === teamCode.toUpperCase() ? game.away_team : game.home_team;
	}

	function isHomeGame(game: Game): boolean {
		return game.home_team === teamCode.toUpperCase();
	}
</script>

<svelte:head>
	<title>{teamName} - {sportName} Momentum</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Back Link -->
	<a
		href="/{sport}/teams"
		class="inline-flex items-center mb-6 transition-colors"
		style="color: {THEME.textSecondary};"
		onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
		onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
	>
		<svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		Back to Teams
	</a>

	<!-- Team Header -->
	<div class="mb-8 rounded-xl p-8" style="background-color: {THEME.cardBg};">
		<div class="flex items-center gap-6">
			<img
				src={getTeamLogoUrl(teamCode)}
				alt={teamCode}
				class="w-24 h-24 object-contain"
				onerror="this.style.display='none'"
			/>
			<div>
				<h1 class="text-4xl font-bold mb-2" style="color: {THEME.text};">
					{teamName}
				</h1>
				<div class="flex items-center gap-4 text-lg">
					<span style="color: {THEME.textSecondary};">{teamCode.toUpperCase()}</span>
					{#if !loading && totalGames > 0}
						<span style="color: {THEME.border};">•</span>
						<span style="color: {THEME.text};" class="font-semibold">
							{wins}-{losses}
						</span>
					{/if}
				</div>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="flex justify-center py-16">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2" style="border-color: {THEME.accentBlue};"></div>
		</div>
	{:else if error}
		<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.accentRed}40;">
			<h2 class="font-semibold mb-2" style="color: {THEME.accentRed};">Error Loading Team Data</h2>
			<p style="color: {THEME.textSecondary};">{error}</p>
		</div>
	{:else if games.length === 0}
		<div class="rounded-xl p-12 text-center" style="background-color: {THEME.cardBg};">
			<h3 class="text-lg font-semibold mb-2" style="color: {THEME.text};">
				No games found
			</h3>
			<p style="color: {THEME.textSecondary};">
				No game data available for this team
			</p>
		</div>
	{:else}
		<!-- Stats Cards -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
			<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg};">
				<div class="text-sm mb-1" style="color: {THEME.textSecondary};">Total Games</div>
				<div class="text-3xl font-bold" style="color: {THEME.text};">{totalGames}</div>
			</div>
			<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg};">
				<div class="text-sm mb-1" style="color: {THEME.textSecondary};">Wins</div>
				<div class="text-3xl font-bold" style="color: {THEME.accentGreen};">{wins}</div>
			</div>
			<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg};">
				<div class="text-sm mb-1" style="color: {THEME.textSecondary};">Losses</div>
				<div class="text-3xl font-bold" style="color: {THEME.accentRed};">{losses}</div>
			</div>
			<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg};">
				<div class="text-sm mb-1" style="color: {THEME.textSecondary};">Win Rate</div>
				<div class="text-3xl font-bold" style="color: {THEME.accentBlue};">
					{totalGames > 0 ? ((wins / totalGames) * 100).toFixed(0) : 0}%
				</div>
			</div>
		</div>

		<!-- Game History -->
		<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
			<h2 class="text-xl font-semibold mb-4" style="color: {THEME.text};">
				Game History
			</h2>
			<div class="space-y-3">
				{#each games.slice(0, 20) as game}
					{@const result = getGameResult(game)}
					{@const opponent = getOpponent(game)}
					{@const isHome = isHomeGame(game)}
					<button
						class="w-full text-left p-4 rounded-lg border transition-all"
						style="background-color: {THEME.bg}; border-color: {THEME.border};"
						on:mouseenter={(e) => {
							e.currentTarget.style.backgroundColor = THEME.cardBg;
							e.currentTarget.style.borderColor = THEME.accentBlue;
						}}
						on:mouseleave={(e) => {
							e.currentTarget.style.backgroundColor = THEME.bg;
							e.currentTarget.style.borderColor = THEME.border;
						}}
						on:click={() => viewGame(game.game_id)}
					>
						<div class="flex items-center gap-4">
							<!-- Result Badge -->
							{#if result}
								<div
									class="px-3 py-1 rounded-md font-bold text-sm w-12 text-center"
									style="background-color: {result === 'W' ? THEME.accentGreen : THEME.accentRed}20;
									       color: {result === 'W' ? THEME.accentGreen : THEME.accentRed};"
								>
									{result}
								</div>
							{:else}
								<div class="w-12"></div>
							{/if}

							<!-- Game Info -->
							<div class="flex-1">
								<div class="flex items-center gap-2 mb-1">
									<span class="font-semibold" style="color: {THEME.text};">
										{isHome ? 'vs' : '@'} {opponent}
									</span>
									{#if game.home_score !== null && game.away_score !== null}
										<span class="font-bold tabular-nums" style="color: {THEME.textSecondary};">
											{isHome ? `${game.home_score}-${game.away_score}` : `${game.away_score}-${game.home_score}`}
										</span>
									{/if}
								</div>
								<div class="flex items-center gap-3 text-sm" style="color: {THEME.textSecondary};">
									<span>Week {game.week}, {game.season}</span>
									{#if game.game_date}
										<span>•</span>
										<span>{formatDate(game.game_date)}</span>
									{/if}
								</div>
							</div>

							<!-- Arrow -->
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.accentBlue};">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>

			{#if games.length > 20}
				<div class="mt-4 text-center text-sm" style="color: {THEME.textSecondary};">
					Showing 20 of {games.length} games
				</div>
			{/if}
		</div>
	{/if}
</div>
