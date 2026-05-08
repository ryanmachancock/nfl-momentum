<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { SPORTS, getSportFromPath, DEFAULT_SPORT } from '$lib/sports';

	// Accept SvelteKit props to avoid warnings
	export let data: any = {};
	export let params: any = {};

	// Theme colors
	const THEME = {
		bg: '#0d1117',
		cardBg: '#161b22',
		text: '#e6edf3',
		textSecondary: '#8b949e',
		border: '#30363d',
		accentBlue: '#58a6ff'
	};

	let isDropdownOpen = false;
	let isMobileMenuOpen = false;

	// Reactive statement to get current sport from URL
	$: currentSport = getSportFromPath($page.url.pathname);
	$: currentSportPath = currentSport.id;

	function toggleDropdown() {
		isDropdownOpen = !isDropdownOpen;
	}

	function toggleMobileMenu() {
		isMobileMenuOpen = !isMobileMenuOpen;
	}

	function selectSport(sportId: string) {
		isDropdownOpen = false;
		goto(`/${sportId}`);
	}

	function closeDropdown() {
		isDropdownOpen = false;
	}

	function closeMobileMenu() {
		isMobileMenuOpen = false;
	}

	function navigateTo(path: string) {
		isMobileMenuOpen = false;
		goto(path);
	}
</script>

<div class="min-h-screen" style="background-color: {THEME.bg};">
	<!-- Header -->
	<header style="background-color: {THEME.cardBg}; border-bottom: 1px solid {THEME.border};">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between items-center h-16">
				<div class="flex items-center space-x-4">
					<a href="/{currentSportPath}" class="flex items-center space-x-2">
						<span class="text-2xl font-bold" style="color: {THEME.text};">
							Momentum Analyzer
						</span>
					</a>

					<!-- Sport Selector Dropdown -->
					<div class="relative">
						<button
							on:click={toggleDropdown}
							class="flex items-center space-x-1 px-3 py-1.5 rounded-md transition-all"
							style="background-color: {isDropdownOpen ? THEME.border : 'transparent'};
								   border: 1px solid {THEME.border};
								   color: {THEME.text};"
						>
							<span class="text-sm font-medium">{currentSport.abbreviation}</span>
							<svg
								class="w-4 h-4 transition-transform"
								style="transform: {isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)'};"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</button>

						<!-- Dropdown Menu -->
						{#if isDropdownOpen}
							<div
								class="absolute top-full left-0 mt-1 rounded-md shadow-lg z-50"
								style="background-color: {THEME.cardBg};
									   border: 1px solid {THEME.border};
									   min-width: 150px;"
							>
								{#each SPORTS as sport}
									<button
										on:click={() => sport.enabled && selectSport(sport.id)}
										class="w-full text-left px-4 py-2 text-sm transition-colors flex items-center space-x-2"
										style="color: {sport.id === currentSport.id ? THEME.accentBlue : sport.enabled ? THEME.text : THEME.textSecondary}; cursor: {sport.enabled ? 'pointer' : 'default'}; opacity: {sport.enabled ? 1 : 0.6};"
										onmouseenter={(e) => {
											if (sport.id !== currentSport.id) {
												e.currentTarget.style.backgroundColor = THEME.border;
											}
										}}
										onmouseleave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
									>
										<span>{sport.icon}</span>
										<span>{sport.name}</span>
										{#if sport.id === currentSport.id}
											<span style="color: {THEME.accentBlue}; margin-left: auto;">✓</span>
										{/if}
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<!-- Desktop Navigation -->
				<nav class="hidden md:flex items-center space-x-6">
					<a
						href="/{currentSportPath}"
						class="transition-colors text-sm font-medium"
						style="color: {$page.url.pathname === `/${currentSportPath}` ? THEME.accentBlue : THEME.textSecondary};"
						onmouseenter={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}`) {
								e.currentTarget.style.color = THEME.text;
							}
						}}
						onmouseleave={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}`) {
								e.currentTarget.style.color = THEME.textSecondary;
							}
						}}
					>
						Games
					</a>
					<a
						href="/{currentSportPath}/stats"
						class="transition-colors text-sm font-medium"
						style="color: {$page.url.pathname === `/${currentSportPath}/stats` ? THEME.accentBlue : THEME.textSecondary};"
						onmouseenter={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/stats`) {
								e.currentTarget.style.color = THEME.text;
							}
						}}
						onmouseleave={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/stats`) {
								e.currentTarget.style.color = THEME.textSecondary;
							}
						}}
					>
						Stats
					</a>
					<a
						href="/{currentSportPath}/teams"
						class="transition-colors text-sm font-medium"
						style="color: {$page.url.pathname === `/${currentSportPath}/teams` ? THEME.accentBlue : THEME.textSecondary};"
						onmouseenter={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/teams`) {
								e.currentTarget.style.color = THEME.text;
							}
						}}
						onmouseleave={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/teams`) {
								e.currentTarget.style.color = THEME.textSecondary;
							}
						}}
					>
						Teams
					</a>
					<a
						href="/{currentSportPath}/search"
						class="transition-colors text-sm font-medium flex items-center space-x-1"
						style="color: {$page.url.pathname === `/${currentSportPath}/search` ? THEME.accentBlue : THEME.textSecondary};"
						onmouseenter={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/search`) {
								e.currentTarget.style.color = THEME.text;
							}
						}}
						onmouseleave={(e) => {
							if ($page.url.pathname !== `/${currentSportPath}/search`) {
								e.currentTarget.style.color = THEME.textSecondary;
							}
						}}
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<span>Search</span>
					</a>
				</nav>

				<!-- Mobile Menu Button -->
				<button
					class="md:hidden p-2"
					on:click={toggleMobileMenu}
					style="color: {THEME.text};"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						{#if isMobileMenuOpen}
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						{:else}
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						{/if}
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Mobile Menu -->
	{#if isMobileMenuOpen}
		<div class="md:hidden" style="background-color: {THEME.cardBg}; border-bottom: 1px solid {THEME.border};">
			<div class="px-4 py-3 space-y-3">
				<button
					class="w-full text-left px-4 py-2 rounded-md transition-colors"
					style="color: {$page.url.pathname === `/${currentSportPath}` ? THEME.accentBlue : THEME.text};
					       background-color: {$page.url.pathname === `/${currentSportPath}` ? THEME.border : 'transparent'};"
					on:click={() => navigateTo(`/${currentSportPath}`)}
				>
					Games
				</button>
				<button
					class="w-full text-left px-4 py-2 rounded-md transition-colors"
					style="color: {$page.url.pathname === `/${currentSportPath}/stats` ? THEME.accentBlue : THEME.text};
					       background-color: {$page.url.pathname === `/${currentSportPath}/stats` ? THEME.border : 'transparent'};"
					on:click={() => navigateTo(`/${currentSportPath}/stats`)}
				>
					Stats
				</button>
				<button
					class="w-full text-left px-4 py-2 rounded-md transition-colors"
					style="color: {$page.url.pathname === `/${currentSportPath}/teams` ? THEME.accentBlue : THEME.text};
					       background-color: {$page.url.pathname === `/${currentSportPath}/teams` ? THEME.border : 'transparent'};"
					on:click={() => navigateTo(`/${currentSportPath}/teams`)}
				>
					Teams
				</button>
				<button
					class="w-full text-left px-4 py-2 rounded-md transition-colors flex items-center space-x-2"
					style="color: {$page.url.pathname === `/${currentSportPath}/search` ? THEME.accentBlue : THEME.text};
					       background-color: {$page.url.pathname === `/${currentSportPath}/search` ? THEME.border : 'transparent'};"
					on:click={() => navigateTo(`/${currentSportPath}/search`)}
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<span>Search</span>
				</button>
			</div>
		</div>
	{/if}

	<!-- Main content -->
	<main>
		<slot />
	</main>

	<!-- Footer -->
	<footer style="background-color: {THEME.cardBg}; border-top: 1px solid {THEME.grid};" class="mt-auto">
		<div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
			<p class="text-center text-sm" style="color: {THEME.textSecondary};">
				NFL Momentum Analyzer - Data from nflfastR
			</p>
		</div>
	</footer>
</div>
