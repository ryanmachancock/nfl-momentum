<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getMomentum, type MomentumResponse } from '$lib/api';
	import MomentumChart from '$lib/components/MomentumChart.svelte';
	import ExportModal from '$lib/components/ExportModal.svelte';

	// Accept SvelteKit props to avoid warnings
	export let data: any = {};
	export let params: any = {};

	let momentum: MomentumResponse | null = null;
	let loading = true;
	let error: string | null = null;
	let showExportModal = false;

	// State for list-chart sync
	let hoveredPlayId: number | null = null;

	function handleChartPlayHover(event: CustomEvent<{ playId: number | null; index: number | null }>) {
		hoveredPlayId = event.detail.playId;
	}

	function handleListItemHover(playId: number | null) {
		hoveredPlayId = playId;
	}

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

	$: gameId = $page.params.gameId;
	$: sport = $page.params.sport;
	$: sportName = sport?.toUpperCase() || 'NFL';

	// Parse team names optimistically from gameId (format: 2024_01_DET_LAR)
	$: gameIdParts = gameId?.split('_') || [];
	$: optimisticAway = gameIdParts[2] || '';
	$: optimisticHome = gameIdParts[3] || '';
	$: pageTitle = momentum
		? `${momentum.game.away_team} @ ${momentum.game.home_team} - ${sportName} Momentum`
		: optimisticAway && optimisticHome
			? `${optimisticAway} @ ${optimisticHome} - ${sportName} Momentum`
			: `Game - ${sportName} Momentum`;

	// Calculate final momentum values for predictions
	$: finalMomentum = momentum?.data_points?.[momentum.data_points.length - 1];
	$: finalHomeMomentum = finalMomentum?.home_momentum || 0;
	$: finalAwayMomentum = finalMomentum?.away_momentum || 0;
	$: predictedWinner = momentum && finalHomeMomentum > finalAwayMomentum ? momentum.game.home_team : momentum?.game.away_team || '';
	$: actualWinner = (momentum?.game?.home_score !== null && momentum?.game?.away_score !== null && momentum?.game)
		? (momentum.game.home_score > momentum.game.away_score ? momentum.game.home_team : momentum.game.away_team)
		: null;
	$: predictionCorrect = actualWinner && predictedWinner === actualWinner;

	onMount(async () => {
		await loadMomentum();
	});

	async function loadMomentum() {
		loading = true;
		error = null;

		try {
			momentum = await getMomentum(gameId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load momentum data';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{pageTitle}</title>
	{#if momentum}
		<meta property="og:title" content="{momentum.game.away_team} @ {momentum.game.home_team} - Week {momentum.game.week}" />
		<meta property="og:description" content="{sportName} momentum analysis - Week {momentum.game.week}, {momentum.game.season} season" />
		<meta property="og:type" content="article" />
	{/if}
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Back Link -->
	<a
		href="/{sport}"
		class="inline-flex items-center mb-6 transition-colors"
		style="color: {THEME.textSecondary};"
		onmouseenter={(e) => e.currentTarget.style.color = THEME.text}
		onmouseleave={(e) => e.currentTarget.style.color = THEME.textSecondary}
	>
		<svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		Back to Games
	</a>

	{#if loading}
		<div class="flex justify-center py-16">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2" style="border-color: {THEME.accentBlue};"></div>
		</div>
	{:else if error}
		<div class="p-6 rounded-xl" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.accentRed}40;">
			<h2 class="font-semibold mb-2" style="color: {THEME.accentRed};">Error Loading Game</h2>
			<p style="color: {THEME.textSecondary};">{error}</p>
			<button
				class="mt-4 px-4 py-2 rounded-md transition-colors"
				style="background-color: {THEME.accentRed}; color: white;"
				on:click={loadMomentum}
			>
				Retry
			</button>
		</div>
	{:else if momentum}
		<!-- Main content area with chart and plays side by side on large screens -->
		<div class="flex flex-col lg:flex-row gap-6">
			<!-- Left: Chart and actions -->
			<div class="flex-1 min-w-0">
				<MomentumChart
					game={momentum.game}
					dataPoints={momentum.data_points}
					highlightedPlayId={hoveredPlayId}
					on:playHover={handleChartPlayHover}
				/>

				<!-- Actions -->
				<div class="mt-4 flex justify-end">
					<button
						class="px-4 py-2 rounded-md transition-all flex items-center"
						style="background-color: {THEME.accentBlue}; color: white;"
						on:click={() => (showExportModal = true)}
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
						</svg>
						Share / Export
					</button>
				</div>
			</div>

			<!-- Right: Key Momentum Plays sidebar -->
			{#if momentum.data_points.filter(dp => dp.is_significant).length > 0}
			{@const significantPlays = momentum.data_points.filter(dp => dp.is_significant)}
			<div class="lg:w-80 flex-shrink-0">
				<div class="rounded-xl p-4 sticky top-4" style="background-color: {THEME.cardBg};">
					<h4 class="text-md font-semibold mb-2" style="color: {THEME.text};">Key Momentum Plays</h4>
					<p class="text-xs mb-3" style="color: {THEME.textSecondary};">
						Tap a play to highlight it on the chart
					</p>
					<div class="space-y-2 max-h-[500px] overflow-y-auto pr-1">
						{#each significantPlays as play}
							{@const isHomePlay = play.momentum_delta > 0}
							{@const isHighlighted = hoveredPlayId === play.play_id}
							<div
								class="flex items-center gap-2 p-2 rounded-lg transition-all cursor-pointer focus:outline-none focus-visible:ring-2"
								style="background-color: {isHighlighted ? (isHomePlay ? THEME.accentGreen + '30' : THEME.accentRed + '30') : THEME.bg};
								       border: 2px solid {isHighlighted ? (isHomePlay ? THEME.accentGreen : THEME.accentRed) : 'transparent'};
								       --tw-ring-color: {THEME.accentBlue};"
								on:mouseenter={() => handleListItemHover(play.play_id)}
								on:mouseleave={() => handleListItemHover(null)}
								on:click={() => handleListItemHover(play.play_id)}
								role="button"
								tabindex="0"
								aria-pressed={isHighlighted}
								on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleListItemHover(hoveredPlayId === play.play_id ? null : play.play_id); } }}
							>
								<div
									class="w-2.5 h-2.5 rounded-full flex-shrink-0 transition-all"
									style="background-color: {isHomePlay ? THEME.accentGreen : THEME.accentRed};
									       transform: {isHighlighted ? 'scale(1.4)' : 'scale(1)'};"
								></div>
								<div class="flex-1 min-w-0">
									<div class="text-xs font-medium truncate" style="color: {THEME.text};">
										{play.event_description || 'Momentum shift'}
									</div>
									<div class="text-xs" style="color: {THEME.textSecondary};">
										Q{play.quarter} · {play.time_remaining}
									</div>
								</div>
								<div
									class="text-xs font-semibold flex-shrink-0"
									style="color: {isHomePlay ? THEME.accentGreen : THEME.accentRed};"
								>
									{play.momentum_delta > 0 ? '+' : ''}{play.momentum_delta.toFixed(1)}
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
			{/if}
		</div>

		<!-- Stats Summary - Full width below -->
		<div class="mt-6 rounded-xl p-6" style="background-color: {THEME.cardBg};">
			<h3 class="text-lg font-semibold mb-4" style="color: {THEME.text};">Game Summary</h3>

			<!-- Final Momentum - Used for Predictions -->
			<div class="mb-6 p-4 rounded-lg" style="background-color: {predictionCorrect ? THEME.accentGreen : (actualWinner ? THEME.accentRed : THEME.accentBlue)}20; border: 2px solid {predictionCorrect ? THEME.accentGreen : (actualWinner ? THEME.accentRed : THEME.accentBlue)}40;">
				<div class="flex items-center justify-between mb-3">
					<div>
						<div class="text-sm font-medium mb-1" style="color: {THEME.text};">Final Momentum (Prediction Metric)</div>
						<div class="text-xs" style="color: {THEME.textSecondary};">
							{#if actualWinner}
								Momentum predicted: <span class="font-semibold" style="color: {THEME.text};">{predictedWinner}</span>
								{#if predictionCorrect}
									<span style="color: {THEME.accentGreen};"> ✓ Correct</span>
								{:else}
									<span style="color: {THEME.accentRed};"> ✗ Incorrect (Winner: {actualWinner})</span>
								{/if}
							{:else}
								Momentum predicts: <span class="font-semibold" style="color: {THEME.text};">{predictedWinner}</span>
							{/if}
						</div>
					</div>
				</div>
				<div class="grid grid-cols-2 gap-4">
					<div class="text-center p-3 rounded" style="background-color: {THEME.bg};">
						<div class="text-2xl font-bold mb-1" style="color: {finalHomeMomentum > 0 ? THEME.accentGreen : THEME.text};">
							{finalHomeMomentum > 0 ? '+' : ''}{finalHomeMomentum.toFixed(1)}
						</div>
						<div class="text-xs" style="color: {THEME.textSecondary};">{momentum?.game?.home_team || 'Home'} Final</div>
					</div>
					<div class="text-center p-3 rounded" style="background-color: {THEME.bg};">
						<div class="text-2xl font-bold mb-1" style="color: {finalAwayMomentum < 0 ? THEME.accentRed : THEME.text};">
							{finalAwayMomentum > 0 ? '+' : ''}{finalAwayMomentum.toFixed(1)}
						</div>
						<div class="text-xs" style="color: {THEME.textSecondary};">{momentum?.game?.away_team || 'Away'} Final</div>
					</div>
				</div>
			</div>

			<!-- Other Stats -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
				<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
					<div class="text-2xl font-bold" style="color: {THEME.text};">
						{momentum.data_points.length}
					</div>
					<div class="text-sm" style="color: {THEME.textSecondary};">Total Plays</div>
				</div>
				<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
					<div class="text-2xl font-bold" style="color: {THEME.accentGreen};">
						{momentum.max_momentum.toFixed(1)}
					</div>
					<div class="text-sm" style="color: {THEME.textSecondary};">Max {momentum.game.home_team} Momentum</div>
				</div>
				<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
					<div class="text-2xl font-bold" style="color: {THEME.accentRed};">
						{Math.abs(momentum.min_momentum).toFixed(1)}
					</div>
					<div class="text-sm" style="color: {THEME.textSecondary};">Max {momentum.game.away_team} Momentum</div>
				</div>
				<div class="p-4 rounded-lg" style="background-color: {THEME.bg};">
					<div class="text-2xl font-bold" style="color: {THEME.text};">
						{momentum.data_points.filter(dp => dp.is_significant).length}
					</div>
					<div class="text-sm" style="color: {THEME.textSecondary};">Big Momentum Swings</div>
				</div>
			</div>

			{#if momentum.biggest_swing}
				<div class="mt-4 p-4 rounded-lg" style="background-color: {THEME.accentYellow}20; border: 1px solid {THEME.accentYellow}40;">
					<div class="font-medium" style="color: {THEME.accentYellow};">Biggest Momentum Swing</div>
					<div class="text-sm mt-1" style="color: {THEME.textSecondary};">
						Q{momentum.biggest_swing.quarter} - {momentum.biggest_swing.time_remaining}:
						{momentum.biggest_swing.event_description || 'Major play'}
						({momentum.biggest_swing.momentum_delta > 0 ? '+' : ''}{momentum.biggest_swing.momentum_delta.toFixed(1)} momentum)
					</div>
				</div>
			{/if}
		</div>

		<!-- Export Modal -->
		<ExportModal
			game={momentum.game}
			isOpen={showExportModal}
			onClose={() => (showExportModal = false)}
		/>
	{/if}
</div>
