<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	// Valid sports
	const VALID_SPORTS = ['nfl', 'nba', 'mlb', 'nhl'];

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		grid: '#30363d',
		accentBlue: '#58a6ff'
	};

	$: sport = $page.params.sport;

	onMount(() => {
		// Validate sport parameter
		if (!VALID_SPORTS.includes(sport?.toLowerCase() || '')) {
			goto('/');
		}
	});

	$: sportName = sport?.toUpperCase() || 'NFL';
</script>

<div class="min-h-screen" style="background-color: {THEME.bg};">
	<!-- Header -->
	<header style="background-color: {THEME.cardBg}; border-bottom: 1px solid {THEME.grid};">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between items-center h-16">
				<a href="/{sport}" class="flex items-center space-x-2">
					<span class="text-2xl font-bold" style="color: {THEME.text};">{sportName} Momentum</span>
				</a>
				<nav class="flex items-center space-x-4">
					<a
						href="/{sport}"
						class="transition-colors hover:text-opacity-100"
						style="color: {THEME.textSecondary};"
						onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
						onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
					>
						Games
					</a>
					<a
						href="/{sport}/stats"
						class="transition-colors hover:text-opacity-100"
						style="color: {THEME.textSecondary};"
						onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
						onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
					>
						Stats
					</a>
					<a
						href="/search"
						class="transition-colors hover:text-opacity-100"
						style="color: {THEME.textSecondary};"
						onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
						onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
					>
						Search
					</a>
					<a
						href="/"
						class="transition-colors hover:text-opacity-100 text-xs"
						style="color: {THEME.textSecondary};"
						onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
						onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
					>
						Change Sport
					</a>
				</nav>
			</div>
		</div>
	</header>

	<!-- Main content -->
	<main>
		<slot />
	</main>

	<!-- Footer -->
	<footer style="background-color: {THEME.cardBg}; border-top: 1px solid {THEME.grid};" class="mt-auto">
		<div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
			<p class="text-center text-sm" style="color: {THEME.textSecondary};">
				{sportName} Momentum Analyzer - Data from nflfastR
			</p>
		</div>
	</footer>
</div>
