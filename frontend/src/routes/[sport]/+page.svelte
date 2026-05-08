<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import GamePicker from '$lib/components/GamePicker.svelte';
	import { getTopMomentumGames, getTeamStats } from '$lib/api';
	import type { Game, TopMomentumGame, TeamStats } from '$lib/api';

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
		accentYellow: '#d29922',
		accentPurple: '#bc8cff'
	};

	$: sport = $page.params.sport;
	$: sportName = sport?.toUpperCase() || 'NFL';

	function handleGameSelect(game: Game) {
		goto(`/${sport}/game/${game.game_id}`);
	}

	let wildestGames: TopMomentumGame[] = [];
	let volatileTeams: TeamStats[] = [];
	let statsLoading = true;

	onMount(async () => {
		try {
			const [gamesData, teamsData] = await Promise.all([
				getTopMomentumGames('swings', undefined, 5),
				getTeamStats(2024).catch(() => null)
			]);
			wildestGames = gamesData.games;
			if (teamsData) {
				volatileTeams = teamsData.teams_by_biggest_swing.slice(0, 5);
			}
		} catch {
			// non-critical — homepage stats degrade gracefully
		} finally {
			statsLoading = false;
		}
	});
</script>

<svelte:head>
	<title>{sportName} Momentum Analyzer</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 py-12">
	<!-- Hero Section -->
	<div class="text-center mb-10">
		<h1 class="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
			{sportName} Momentum Analyzer
		</h1>
		<p class="text-lg" style="color: {THEME.textSecondary};">
			Visualize game momentum through play-by-play analysis
		</p>
	</div>

	<!-- Game Picker -->
	<GamePicker onGameSelect={handleGameSelect} />

	<!-- Features Section -->
	<div class="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
		<div class="p-5 rounded-xl" style="background-color: {THEME.cardBg};">
			<div class="w-10 h-10 rounded-lg flex items-center justify-center mb-3" style="background-color: {THEME.accentBlue}20;">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.accentBlue};">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
			</div>
			<h3 class="font-semibold mb-2" style="color: {THEME.text};">Event-Based Scoring</h3>
			<p class="text-sm" style="color: {THEME.textSecondary};">
				Touchdowns, turnovers, sacks, and big plays all contribute to momentum shifts.
			</p>
		</div>

		<div class="p-5 rounded-xl" style="background-color: {THEME.cardBg};">
			<div class="w-10 h-10 rounded-lg flex items-center justify-center mb-3" style="background-color: {THEME.accentYellow}20;">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.accentYellow};">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
			</div>
			<h3 class="font-semibold mb-2" style="color: {THEME.text};">Decay Over Time</h3>
			<p class="text-sm" style="color: {THEME.textSecondary};">
				Momentum fades naturally as plays progress, so recent events matter more.
			</p>
		</div>

		<div class="p-5 rounded-xl" style="background-color: {THEME.cardBg};">
			<div class="w-10 h-10 rounded-lg flex items-center justify-center mb-3" style="background-color: {THEME.accentGreen}20;">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.accentGreen};">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
				</svg>
			</div>
			<h3 class="font-semibold mb-2" style="color: {THEME.text};">Streak Bonuses</h3>
			<p class="text-sm" style="color: {THEME.textSecondary};">
				Consecutive positive plays build momentum faster, reflecting real game dynamics.
			</p>
		</div>
	</div>

	<!-- Homepage Stats Section -->
	{#if statsLoading}
		<div class="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
			{#each [0, 1] as _}
				<div class="rounded-xl p-5 animate-pulse" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.border};">
					<div class="h-5 w-36 rounded mb-2" style="background-color: {THEME.border};"></div>
					<div class="h-3 w-56 rounded mb-5" style="background-color: {THEME.border};"></div>
					{#each [0,1,2,3,4] as __}
						<div class="h-9 rounded-lg mb-2" style="background-color: {THEME.border};"></div>
					{/each}
				</div>
			{/each}
		</div>
	{:else if wildestGames.length > 0 || volatileTeams.length > 0}
		<div class="mt-12">
			<h2 class="text-sm font-semibold uppercase tracking-widest mb-6 text-center" style="color: {THEME.textSecondary};">
				By the Numbers
			</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">

				<!-- Wildest Games -->
				{#if wildestGames.length > 0}
				<div class="rounded-xl p-5" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.border};">
					<div class="mb-4">
						<h3 class="text-base font-semibold" style="color: {THEME.text};">⚡ Wildest Games</h3>
						<p class="text-xs mt-1 leading-relaxed" style="color: {THEME.textSecondary};">
							Biggest single momentum swings ever recorded — one play that changed everything.
						</p>
					</div>
					<div class="space-y-1">
						{#each wildestGames as game, i}
						<a
							href="/{sport}/game/{game.game_id}"
							class="flex items-center justify-between px-3 py-2 rounded-lg transition-colors"
							style="color: inherit;"
							onmouseenter={(e) => e.currentTarget.style.backgroundColor = THEME.border + '80'}
							onmouseleave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
						>
							<div class="flex items-center space-x-3 min-w-0">
								<span class="text-xs font-mono shrink-0 w-4 text-right" style="color: {THEME.textSecondary};">{i + 1}</span>
								<div class="min-w-0">
									<span class="text-sm font-medium" style="color: {THEME.text};">{game.away_team} @ {game.home_team}</span>
									<span class="text-xs ml-2" style="color: {THEME.textSecondary};">Wk {game.week} · {game.season}</span>
								</div>
							</div>
							<span class="text-xs px-2 py-0.5 rounded-full font-mono shrink-0 ml-2" style="background-color: {THEME.accentBlue}20; color: {THEME.accentBlue};">
								↔ {game.max_swing.toFixed(1)}
							</span>
						</a>
						{/each}
					</div>
				</div>
				{/if}

				<!-- Most Volatile Teams -->
				{#if volatileTeams.length > 0}
				<div class="rounded-xl p-5" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.border};">
					<div class="mb-4">
						<h3 class="text-base font-semibold" style="color: {THEME.text};">🌊 Most Volatile Teams</h3>
						<p class="text-xs mt-1 leading-relaxed" style="color: {THEME.textSecondary};">
							2024 season — these teams had the biggest single-game momentum swings. Expect anything.
						</p>
					</div>
					<div class="space-y-1">
						{#each volatileTeams as team, i}
						<a
							href="/{sport}/teams/{team.team}"
							class="flex items-center justify-between px-3 py-2 rounded-lg transition-colors"
							style="color: inherit;"
							onmouseenter={(e) => e.currentTarget.style.backgroundColor = THEME.border + '80'}
							onmouseleave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
						>
							<div class="flex items-center space-x-3">
								<span class="text-xs font-mono w-4 text-right shrink-0" style="color: {THEME.textSecondary};">{i + 1}</span>
								<div>
									<span class="text-sm font-medium" style="color: {THEME.text};">{team.team}</span>
									{#if team.biggest_swing_game}
										<span class="text-xs ml-2" style="color: {THEME.textSecondary};">vs {team.biggest_swing_game.opponent} · Wk {team.biggest_swing_game.week}</span>
									{/if}
								</div>
							</div>
							<span class="text-xs px-2 py-0.5 rounded-full font-mono shrink-0 ml-2" style="background-color: {THEME.accentPurple}20; color: {THEME.accentPurple};">
								{team.biggest_swing.toFixed(1)}
							</span>
						</a>
						{/each}
					</div>
				</div>
				{/if}

			</div>
		</div>
	{/if}
</div>
