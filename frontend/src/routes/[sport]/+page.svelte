<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import GamePicker from '$lib/components/GamePicker.svelte';
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
	$: sportName = sport?.toUpperCase() || 'NFL';

	function handleGameSelect(game: Game) {
		goto(`/${sport}/game/${game.game_id}`);
	}
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
</div>
