<script lang="ts">
	import { createShareLink, getExportPngUrl, getExportSvgUrl, type Game } from '$lib/api';

	export let game: Game;
	export let isOpen = false;
	export let onClose: () => void;

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		grid: '#30363d',
		accentBlue: '#58a6ff',
		accentGreen: '#3fb950',
		accentRed: '#f85149'
	};

	let shareUrl = '';
	let shareLoading = false;
	let shareError = '';
	let copied = false;

	async function handleShare() {
		shareLoading = true;
		shareError = '';

		try {
			const result = await createShareLink(game.game_id);
			shareUrl = result.share_url;
		} catch (e) {
			shareError = e instanceof Error ? e.message : 'Failed to create share link';
		} finally {
			shareLoading = false;
		}
	}

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(shareUrl);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		} catch {
			// Fallback for older browsers
			const input = document.createElement('input');
			input.value = shareUrl;
			document.body.appendChild(input);
			input.select();
			document.execCommand('copy');
			document.body.removeChild(input);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		}
	}

	function handleDownloadPng() {
		window.open(getExportPngUrl(game.game_id), '_blank');
	}

	function handleDownloadSvg() {
		window.open(getExportSvgUrl(game.game_id), '_blank');
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50"
		on:click={handleBackdropClick}
	>
		<div class="rounded-xl shadow-2xl max-w-md w-full mx-4 p-6" style="background-color: {THEME.cardBg}; border: 1px solid {THEME.grid};">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-lg font-semibold" style="color: {THEME.text};">Share & Export</h3>
				<button
					class="transition-colors"
					style="color: {THEME.textSecondary};"
					on:click={onClose}
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<div class="space-y-4">
				<!-- Share Link Section -->
				<div>
					<h4 class="font-medium mb-2" style="color: {THEME.textSecondary};">Share Link</h4>
					{#if shareUrl}
						<div class="flex space-x-2">
							<input
								type="text"
								readonly
								value={shareUrl}
								class="flex-1 p-2 rounded-md text-sm"
								style="background-color: {THEME.bg}; border: 1px solid {THEME.grid}; color: {THEME.text};"
							/>
							<button
								class="px-4 py-2 rounded-md transition-colors"
								style="background-color: {copied ? THEME.accentGreen : THEME.accentBlue}; color: white;"
								on:click={copyToClipboard}
							>
								{copied ? 'Copied!' : 'Copy'}
							</button>
						</div>
					{:else}
						<button
							class="w-full px-4 py-2 rounded-md transition-colors disabled:opacity-50"
							style="background-color: {THEME.accentBlue}; color: white;"
							on:click={handleShare}
							disabled={shareLoading}
						>
							{#if shareLoading}
								Creating link...
							{:else}
								Generate Shareable Link
							{/if}
						</button>
					{/if}
					{#if shareError}
						<p class="text-sm mt-1" style="color: {THEME.accentRed};">{shareError}</p>
					{/if}
				</div>

				<hr style="border-color: {THEME.grid};" />

				<!-- Download Section -->
				<div>
					<h4 class="font-medium mb-2" style="color: {THEME.textSecondary};">Download Image</h4>
					<div class="flex space-x-2">
						<button
							class="flex-1 px-4 py-2 rounded-md transition-colors flex items-center justify-center"
							style="background-color: {THEME.bg}; border: 1px solid {THEME.grid}; color: {THEME.text};"
							on:click={handleDownloadPng}
						>
							<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
							</svg>
							PNG
						</button>
						<button
							class="flex-1 px-4 py-2 rounded-md transition-colors flex items-center justify-center"
							style="background-color: {THEME.bg}; border: 1px solid {THEME.grid}; color: {THEME.text};"
							on:click={handleDownloadSvg}
						>
							<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
							</svg>
							SVG
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
