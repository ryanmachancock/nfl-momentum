/**
 * Sport configuration system for NFL Momentum
 * Supports multi-sport expansion (NFL, NBA, MLB, etc.)
 */

import { writable } from 'svelte/store';

export interface Sport {
	id: string;
	name: string;
	abbreviation: string;
	fullName: string;
	icon: string;
	primaryColor: string;
	enabled: boolean;
	apiPrefix: string;
}

/**
 * Available sports configuration
 * NFL is currently enabled, others marked as coming soon
 */
export const SPORTS: Sport[] = [
	{
		id: 'nfl',
		name: 'NFL',
		abbreviation: 'NFL',
		fullName: 'National Football League',
		icon: '🏈',
		primaryColor: '#58a6ff', // Using accent-blue from theme
		enabled: true,
		apiPrefix: '/api'
	},
	{
		id: 'nba',
		name: 'NBA',
		abbreviation: 'NBA',
		fullName: 'National Basketball Association',
		icon: '🏀',
		primaryColor: '#d29922', // Using accent-yellow from theme
		enabled: false,
		apiPrefix: '/api/nba'
	},
	{
		id: 'mlb',
		name: 'MLB',
		abbreviation: 'MLB',
		fullName: 'Major League Baseball',
		icon: '⚾',
		primaryColor: '#3fb950', // Using accent-green from theme
		enabled: false,
		apiPrefix: '/api/mlb'
	}
];

/**
 * Get a sport by its ID
 * @param id - Sport identifier (e.g., 'nfl', 'nba', 'mlb')
 * @returns Sport object or undefined if not found
 */
export function getSportById(id: string): Sport | undefined {
	return SPORTS.find(sport => sport.id === id);
}

/**
 * Get all enabled sports
 * @returns Array of enabled sports
 */
export function getEnabledSports(): Sport[] {
	return SPORTS.filter(sport => sport.enabled);
}

/**
 * Writable store for the currently selected sport
 * Defaults to NFL as it's the only enabled sport
 */
const defaultSport = SPORTS.find(sport => sport.id === 'nfl') || SPORTS[0];

function createCurrentSportStore() {
	const { subscribe, set, update } = writable<Sport>(defaultSport);

	return {
		subscribe,
		set: (sport: Sport) => {
			if (!sport.enabled) {
				console.warn(`Sport ${sport.name} is not enabled yet`);
				return;
			}
			set(sport);
		},
		setById: (id: string) => {
			const sport = getSportById(id);
			if (!sport) {
				console.warn(`Sport with id "${id}" not found`);
				return;
			}
			if (!sport.enabled) {
				console.warn(`Sport ${sport.name} is not enabled yet`);
				return;
			}
			set(sport);
		},
		reset: () => set(defaultSport)
	};
}

export const currentSport = createCurrentSportStore();

/**
 * Default sport (NFL)
 */
export const DEFAULT_SPORT = SPORTS.find(sport => sport.id === 'nfl') || SPORTS[0];

/**
 * Extract sport from URL path
 * @param pathname - URL pathname (e.g., '/nfl/game/123', '/nba/stats')
 * @returns Sport object, defaults to NFL if not found or invalid
 */
export function getSportFromPath(pathname: string): Sport {
	// Remove leading slash and split path
	const parts = pathname.replace(/^\//, '').split('/');

	// First part should be the sport ID
	if (parts.length > 0 && parts[0]) {
		const sport = getSportById(parts[0]);
		if (sport) {
			return sport;
		}
	}

	// Default to NFL
	return DEFAULT_SPORT;
}
