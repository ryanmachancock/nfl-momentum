import { writable } from 'svelte/store';
import type { Game, MomentumResponse } from '$lib/api';

// Selected season/week for game picker
export const selectedSeason = writable<number | null>(null);
export const selectedWeek = writable<number | null>(null);

// Current game being viewed
export const currentGame = writable<Game | null>(null);
export const currentMomentum = writable<MomentumResponse | null>(null);

// Loading states
export const isLoading = writable(false);
export const error = writable<string | null>(null);

// Reset state
export function resetGameState() {
	currentGame.set(null);
	currentMomentum.set(null);
	error.set(null);
}
