<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getSharedMomentum, type MomentumResponse } from '$lib/api';
	import MomentumChart from '$lib/components/MomentumChart.svelte';

	let momentum: MomentumResponse | null = null;
	let loading = true;
	let error: string | null = null;

	$: shareCode = $page.params.shareCode;

	onMount(async () => {
		loading = true;
		error = null;

		try {
			momentum = await getSharedMomentum(shareCode);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load shared graph';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	{#if momentum}
		<title>{momentum.game.away_team} @ {momentum.game.home_team} - NFL Momentum</title>
		<meta property="og:title" content="{momentum.game.away_team} @ {momentum.game.home_team} Momentum Graph" />
		<meta property="og:description" content="Week {momentum.game.week}, {momentum.game.season} - NFL Momentum Analysis" />
	{:else}
		<title>Shared Game - NFL Momentum</title>
	{/if}
</svelte:head>

<div class="max-w-6xl mx-auto px-4 py-8">
	{#if loading}
		<div class="flex justify-center py-16">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
		</div>
	{:else if error}
		<div class="bg-red-50 text-red-700 p-6 rounded-lg text-center">
			<h2 class="font-semibold mb-2">Link Not Found</h2>
			<p>{error}</p>
			<a
				href="/"
				class="mt-4 inline-block px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
			>
				Browse Games
			</a>
		</div>
	{:else if momentum}
		<!-- Shared Badge -->
		<div class="text-center mb-6">
			<span class="inline-block px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
				Shared Momentum Graph
			</span>
		</div>

		<!-- Momentum Chart -->
		<MomentumChart game={momentum.game} dataPoints={momentum.data_points} />

		<!-- View Full Analysis Link -->
		<div class="mt-6 text-center">
			<a
				href="/game/{momentum.game.game_id}"
				class="text-primary-600 hover:text-primary-800 font-medium"
			>
				View Full Analysis &rarr;
			</a>
		</div>

		<!-- CTA -->
		<div class="mt-8 text-center bg-gray-50 rounded-lg p-6">
			<h3 class="font-semibold text-gray-900 mb-2">Want to explore more games?</h3>
			<a
				href="/"
				class="inline-block px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
			>
				Browse All Games
			</a>
		</div>
	{/if}
</div>
