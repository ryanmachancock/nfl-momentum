<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	// Valid sports
	const VALID_SPORTS = ['nfl', 'nba', 'mlb', 'nhl'];

	$: sport = $page.params.sport;

	onMount(() => {
		// Validate sport parameter
		if (!VALID_SPORTS.includes(sport?.toLowerCase() || '')) {
			goto('/');
		}
	});
</script>

<slot />
