<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
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

	let searchQuery = '';
	let searchResults: Game[] = [];
	let loading = false;
	let error: string | null = null;
	let hasSearched = false;

	async function handleSearch() {
		if (!searchQuery || searchQuery.length < 2) {
			error = 'Please enter at least 2 characters';
			return;
		}

		loading = true;
		error = null;
		hasSearched = true;

		try {
			const response = await fetch(
				`http://localhost:8000/api/games/search?q=${encodeURIComponent(searchQuery)}&limit=50`
			);

			if (!response.ok) {
				throw new Error('Search failed');
			}

			const data = await response.json();
			searchResults = data.games || [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to search games';
			searchResults = [];
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

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSearch();
		}
	}
</script>

<svelte:head>
	<title>Search - {sportName} Momentum</title>
</svelte:head>

<div class="max-w-5xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold mb-2" style="color: {THEME.text};">Search Games</h1>
		<p style="color: {THEME.textSecondary};">
			Search for games by team name
		</p>
	</div>

	<!-- Search Bar -->
	<div class="mb-8">
		<div class="flex gap-3">
			<div class="flex-1 relative">
				<input
					type="text"
					bind:value={searchQuery}
					on:keypress={handleKeyPress}
					placeholder="Search by team name (e.g., Chiefs, Ravens, KC, BAL)..."
					class="w-full px-4 py-3 pl-12 rounded-lg border focus:outline-none focus:ring-2"
					style="background-color: {THEME.cardBg};
					       color: {THEME.text};
					       border-color: {THEME.border};"
				/>
				<svg
					class="w-5 h-5 absolute left-4 top-1/2 transform -translate-y-1/2"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					style="color: {THEME.textSecondary};"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
			<button
				class="px-6 py-3 rounded-lg font-medium transition-colors"
				style="background-color: {THEME.accentBlue}; color: white;"
				on:click={handleSearch}
				disabled={loading}
			>
				{loading ? 'Searching...' : 'Search'}
			</button>
		</div>

		{#if error}
			<div class="mt-3 p-3 rounded-lg" style="background-color: {THEME.accentRed}20; border: 1px solid {THEME.accentRed}40;">
				<p class="text-sm" style="color: {THEME.accentRed};">{error}</p>
			</div>
		{/if}
	</div>

	<!-- Results -->
	{#if loading}
		<div class="flex justify-center py-16">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2" style="border-color: {THEME.accentBlue};"></div>
		</div>
	{:else if hasSearched}
		{#if searchResults.length > 0}
			<div class="rounded-xl p-6" style="background-color: {THEME.cardBg};">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-lg font-semibold" style="color: {THEME.text};">
						Search Results
					</h2>
					<span class="text-sm" style="color: {THEME.textSecondary};">
						{searchResults.length} {searchResults.length === 1 ? 'game' : 'games'} found
					</span>
				</div>

				<div class="space-y-3">
					{#each searchResults as game}
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
							<div class="flex items-center justify-between gap-4">
								<div class="flex-1">
									<div class="flex items-center gap-4 mb-1">
										<span class="font-semibold" style="color: {THEME.text};">
											{game.away_team} @ {game.home_team}
										</span>
										{#if game.away_score !== null && game.home_score !== null}
											<span class="font-bold tabular-nums" style="color: {THEME.textSecondary};">
												{game.away_score} - {game.home_score}
											</span>
										{/if}
									</div>
									<div class="flex items-center gap-3 text-sm" style="color: {THEME.textSecondary};">
										<span>Season {game.season}</span>
										<span>•</span>
										<span>Week {game.week}</span>
										{#if game.game_date}
											<span>•</span>
											<span>{formatDate(game.game_date)}</span>
										{/if}
									</div>
								</div>
								<div class="flex items-center">
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.accentBlue};">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
								</div>
							</div>
						</button>
					{/each}
				</div>
			</div>
		{:else}
			<div class="rounded-xl p-12 text-center" style="background-color: {THEME.cardBg};">
				<svg class="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.textSecondary};">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<h3 class="text-lg font-semibold mb-2" style="color: {THEME.text};">
					No results found
				</h3>
				<p style="color: {THEME.textSecondary};">
					Try searching for a different team name
				</p>
			</div>
		{/if}
	{:else}
		<div class="rounded-xl p-12 text-center" style="background-color: {THEME.cardBg};">
			<svg class="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.textSecondary};">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
			<h3 class="text-lg font-semibold mb-2" style="color: {THEME.text};">
				Search for games
			</h3>
			<p style="color: {THEME.textSecondary};">
				Enter a team name to find their games
			</p>
		</div>
	{/if}
</div>
