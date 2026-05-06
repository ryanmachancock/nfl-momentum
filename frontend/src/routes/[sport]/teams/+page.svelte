<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getTeamLogoUrl } from '$lib/teamLogos';

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

	// NFL teams - in a real app, this would come from an API
	const NFL_TEAMS = [
		'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
		'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
		'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
		'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
	];

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

	const DIVISIONS: Record<string, string[]> = {
		'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
		'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
		'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
		'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
		'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
		'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
		'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
		'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
	};

	let searchQuery = '';
	let selectedDivision = 'all';

	$: filteredTeams = NFL_TEAMS.filter(team => {
		const matchesSearch = searchQuery.length === 0 ||
			team.toLowerCase().includes(searchQuery.toLowerCase()) ||
			TEAM_NAMES[team].toLowerCase().includes(searchQuery.toLowerCase());

		const matchesDivision = selectedDivision === 'all' ||
			Object.entries(DIVISIONS).find(([div, teams]) =>
				div === selectedDivision && teams.includes(team)
			);

		return matchesSearch && matchesDivision;
	});

	function viewTeam(teamCode: string) {
		goto(`/${sport}/teams/${teamCode}`);
	}
</script>

<svelte:head>
	<title>Teams - {sportName} Momentum</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold mb-2" style="color: {THEME.text};">
			{sportName} Teams
		</h1>
		<p style="color: {THEME.textSecondary};">
			Explore team momentum statistics and game history
		</p>
	</div>

	<!-- Filters -->
	<div class="mb-6 flex flex-col md:flex-row gap-4">
		<!-- Search -->
		<div class="flex-1 relative">
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Search teams..."
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

		<!-- Division Filter -->
		<select
			bind:value={selectedDivision}
			class="px-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
			style="background-color: {THEME.cardBg};
			       color: {THEME.text};
			       border-color: {THEME.border};"
		>
			<option value="all">All Divisions</option>
			{#each Object.keys(DIVISIONS) as division}
				<option value={division}>{division}</option>
			{/each}
		</select>
	</div>

	<!-- Teams Grid -->
	{#if selectedDivision === 'all'}
		<!-- Show by division -->
		<div class="space-y-8">
			{#each Object.entries(DIVISIONS) as [division, teams]}
				{@const divisionTeams = teams.filter(team => filteredTeams.includes(team))}
				{#if divisionTeams.length > 0}
					<div>
						<h2 class="text-xl font-semibold mb-4" style="color: {THEME.text};">
							{division}
						</h2>
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
							{#each divisionTeams as team}
								<button
									class="p-6 rounded-xl border-2 transition-all text-center"
									style="background-color: {THEME.cardBg}; border-color: {THEME.border};"
									on:mouseenter={(e) => {
										e.currentTarget.style.borderColor = THEME.accentBlue;
										e.currentTarget.style.transform = 'translateY(-4px)';
									}}
									on:mouseleave={(e) => {
										e.currentTarget.style.borderColor = THEME.border;
										e.currentTarget.style.transform = 'translateY(0)';
									}}
									on:click={() => viewTeam(team)}
								>
									<img
										src={getTeamLogoUrl(team)}
										alt={team}
										class="w-20 h-20 mx-auto mb-3 object-contain"
										onerror="this.style.display='none'"
									/>
									<div class="font-bold text-lg mb-1" style="color: {THEME.text};">
										{team}
									</div>
									<div class="text-sm" style="color: {THEME.textSecondary};">
										{TEAM_NAMES[team]}
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			{/each}
		</div>
	{:else}
		<!-- Show selected division only -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each filteredTeams as team}
				<button
					class="p-6 rounded-xl border-2 transition-all text-center"
					style="background-color: {THEME.cardBg}; border-color: {THEME.border};"
					on:mouseenter={(e) => {
						e.currentTarget.style.borderColor = THEME.accentBlue;
						e.currentTarget.style.transform = 'translateY(-4px)';
					}}
					on:mouseleave={(e) => {
						e.currentTarget.style.borderColor = THEME.border;
						e.currentTarget.style.transform = 'translateY(0)';
					}}
					on:click={() => viewTeam(team)}
				>
					<img
						src={getTeamLogoUrl(team)}
						alt={team}
						class="w-20 h-20 mx-auto mb-3 object-contain"
						onerror="this.style.display='none'"
					/>
					<div class="font-bold text-lg mb-1" style="color: {THEME.text};">
						{team}
					</div>
					<div class="text-sm" style="color: {THEME.textSecondary};">
						{TEAM_NAMES[team]}
					</div>
				</button>
			{/each}
		</div>
	{/if}

	<!-- No results -->
	{#if filteredTeams.length === 0}
		<div class="rounded-xl p-12 text-center" style="background-color: {THEME.cardBg};">
			<svg class="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {THEME.textSecondary};">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<h3 class="text-lg font-semibold mb-2" style="color: {THEME.text};">
				No teams found
			</h3>
			<p style="color: {THEME.textSecondary};">
				Try a different search term or filter
			</p>
		</div>
	{/if}
</div>
