/**
 * API client for the NFL Momentum backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Game {
	id: number;
	game_id: string;
	season: number;
	week: number;
	game_type: string | null;
	home_team: string;
	away_team: string;
	home_score: number | null;
	away_score: number | null;
	game_date: string | null;
}

export interface MomentumDataPoint {
	play_id: number;
	quarter: number;
	time_remaining: string;
	home_momentum: number;
	away_momentum: number;
	momentum_delta: number;
	home_wp: number | null;
	away_wp: number | null;
	event_description: string | null;
	is_significant: boolean;
	home_score: number | null;
	away_score: number | null;
	yardline_100: number | null;
	down: number | null;
	yards_to_go: number | null;
}

export interface MomentumResponse {
	game: Game;
	data_points: MomentumDataPoint[];
	max_momentum: number;
	min_momentum: number;
	biggest_swing: MomentumDataPoint | null;
}

export interface SeasonWeekResponse {
	seasons: number[];
	weeks_by_season: Record<number, number[]>;
}

export interface ShareResponse {
	share_code: string;
	share_url: string;
	game_id: string;
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
	const response = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options?.headers
		}
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(error.detail || `HTTP ${response.status}`);
	}

	return response.json();
}

// Games API
export async function getSeasons(): Promise<SeasonWeekResponse> {
	return fetchApi('/api/games/seasons');
}

export async function getGames(season: number, week: number): Promise<{ games: Game[]; count: number }> {
	return fetchApi(`/api/games/${season}/${week}`);
}

export async function getGame(gameId: string): Promise<Game> {
	return fetchApi(`/api/games/game/${gameId}`);
}

export async function searchGames(query: string, season?: number): Promise<{ games: Game[]; count: number }> {
	const params = new URLSearchParams({ q: query });
	if (season) params.set('season', season.toString());
	return fetchApi(`/api/games/search?${params}`);
}

// Momentum API
export async function getMomentum(gameId: string): Promise<MomentumResponse> {
	return fetchApi(`/api/momentum/${gameId}`);
}

export async function refreshMomentum(gameId: string): Promise<{ message: string }> {
	return fetchApi(`/api/momentum/${gameId}/refresh`, { method: 'POST' });
}

export function getExportPngUrl(gameId: string): string {
	return `${API_BASE}/api/momentum/${gameId}/export/png`;
}

export function getExportSvgUrl(gameId: string): string {
	return `${API_BASE}/api/momentum/${gameId}/export/svg`;
}

// Share API
export async function createShareLink(gameId: string): Promise<ShareResponse> {
	return fetchApi(`/api/share/${gameId}`, { method: 'POST' });
}

export async function getSharedMomentum(shareCode: string): Promise<MomentumResponse> {
	return fetchApi(`/api/share/${shareCode}`);
}

// Data loading API
export async function getAvailableSeasons(): Promise<{
	all_seasons: number[];
	loaded_seasons: number[];
	available_to_load: number[];
}> {
	return fetchApi('/api/games/available-seasons');
}

export async function loadSeason(season: number): Promise<{
	season: number;
	games_loaded: number;
	plays_loaded: number;
}> {
	return fetchApi(`/api/games/load/${season}`, { method: 'POST' });
}

// Stats API
export interface GameAnalysis {
	game_id: string;
	week: number;
	home_team: string;
	away_team: string;
	home_score: number;
	away_score: number;
	game_date: string | null;
	final_home_momentum: number;
	final_away_momentum: number;
	actual_winner: string;
	momentum_predicted_winner: string;
	predicted_correctly: boolean;
	biggest_swing: number;
	biggest_swing_quarter: number | null;
	biggest_swing_time: string | null;
	average_swing: number;
	total_volatility: number;
}

export interface ValidationMetric {
	metric: string;
	description: string;
	correct_predictions: number;
	total_games: number;
	percentage: number;
}

export interface SeasonStats {
	season: number;
	total_games: number;
	games_analyzed: number;
	validation_comparison: ValidationMetric[];
	best_metric: ValidationMetric | null;
	validation: {
		momentum_predicted_wins: number;
		total_games: number;
		percentage: number;
		method: string;
	};
	games_by_volatility: GameAnalysis[];
	average_swing_per_game: number;
}

export interface TeamStats {
	team: string;
	games_played: number;
	avg_momentum_per_game: number;
	avg_swing_per_game: number;
	biggest_swing: number;
	biggest_swing_game: {
		game_id: string;
		opponent: string;
		week: number;
		swing: number;
	} | null;
}

export interface TeamStatsResponse {
	season: number;
	teams_by_avg_momentum: TeamStats[];
	teams_by_biggest_swing: TeamStats[];
}

export async function getSeasonStats(season: number): Promise<SeasonStats> {
	return fetchApi(`/api/stats/season/${season}`);
}

export async function getTeamStats(season: number): Promise<TeamStatsResponse> {
	return fetchApi(`/api/stats/teams/${season}`);
}

// Top Momentum Games API
export interface TopMomentumGame extends Game {
	max_home_momentum: number;
	min_home_momentum: number;
	max_swing: number;
	total_volatility: number;
	final_home_momentum: number;
	final_away_momentum: number;
}

export interface TopMomentumResponse {
	category: string;
	games: TopMomentumGame[];
	count: number;
}

export interface StatsOverview {
	total_games: number;
	correct_predictions: number;
	accuracy_percentage: number;
	home_wins: number;
	away_wins: number;
	momentum_favored_home: number;
	momentum_favored_away: number;
	season: string | number;
}

export async function getTopMomentumGames(
	category: 'swings' | 'comebacks' | 'blowouts' | 'close' = 'swings',
	season?: number,
	limit: number = 25
): Promise<TopMomentumResponse> {
	const params = new URLSearchParams({ category, limit: limit.toString() });
	if (season) params.set('season', season.toString());
	return fetchApi(`/api/stats/top-momentum?${params}`);
}

export async function getStatsOverview(season?: number): Promise<StatsOverview> {
	const params = season ? `?season=${season}` : '';
	return fetchApi(`/api/stats/overview${params}`);
}
