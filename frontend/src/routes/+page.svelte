<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { SPORTS } from '$lib/sports';

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

	// Auto-redirect to NFL on mount (default sport)
	onMount(() => {
		// For now, just redirect to NFL
		goto('/nfl');
	});

	function selectSport(sportId: string) {
		goto(`/${sportId}`);
	}
</script>

<svelte:head>
	<title>Sports Momentum Analyzer</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center" style="background-color: {THEME.bg};">
	<div class="max-w-2xl mx-auto px-4">
		<!-- Hero Section -->
		<div class="text-center mb-10">
			<h1 class="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
				Sports Momentum Analyzer
			</h1>
			<p class="text-xl mb-8" style="color: {THEME.textSecondary};">
				Visualize game momentum through play-by-play analysis
			</p>
		</div>

		<!-- Sport Selection -->
		<div class="rounded-xl p-6 mb-8" style="background-color: {THEME.cardBg};">
			<h2 class="text-xl font-semibold mb-4 text-center" style="color: {THEME.text};">
				Select a Sport
			</h2>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each SPORTS as sport}
					<button
						class="p-6 rounded-lg border-2 transition-all text-center"
						style="background-color: {THEME.bg};
						       border-color: {sport.enabled ? THEME.border : THEME.border};
						       opacity: {sport.enabled ? 1 : 0.5};"
						on:mouseenter={(e) => {
							if (sport.enabled) {
								e.currentTarget.style.borderColor = sport.primaryColor;
								e.currentTarget.style.transform = 'scale(1.05)';
							}
						}}
						on:mouseleave={(e) => {
							e.currentTarget.style.borderColor = THEME.border;
							e.currentTarget.style.transform = 'scale(1)';
						}}
						on:click={() => sport.enabled && selectSport(sport.id)}
						disabled={!sport.enabled}
					>
						<div class="text-4xl mb-3">{sport.icon}</div>
						<div class="text-lg font-semibold mb-1" style="color: {THEME.text};">
							{sport.name}
						</div>
						<div class="text-sm" style="color: {THEME.textSecondary};">
							{sport.fullName}
						</div>
						{#if !sport.enabled}
							<div class="mt-2 text-xs px-2 py-1 rounded inline-block" style="background-color: {THEME.accentYellow}20; color: {THEME.accentYellow};">
								Coming Soon
							</div>
						{/if}
					</button>
				{/each}
			</div>
		</div>

		<!-- Features Section -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
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
</div>
