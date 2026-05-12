/**
 * NFL Team Logo URLs using ESPN CDN
 * These are publicly accessible logo images from ESPN's CDN
 */

// ESPN team ID mapping
const ESPN_TEAM_IDS: Record<string, string> = {
	ARI: '22', ATL: '1', BAL: '33', BUF: '2',
	CAR: '29', CHI: '3', CIN: '4', CLE: '5',
	DAL: '6', DEN: '7', DET: '8', GB: '9',
	HOU: '34', IND: '11', JAX: '30', KC: '12',
	LA: '14', LAR: '14', LAC: '24', LV: '13', MIA: '15',
	MIN: '16', NE: '17', NO: '18', NYG: '19',
	NYJ: '20', PHI: '21', PIT: '23', SEA: '26',
	SF: '25', TB: '27', TEN: '10', WAS: '28',
	// Legacy abbreviations
	SD: '24', STL: '14', OAK: '13'
};

/**
 * Get the ESPN logo URL for a team
 * @param team - Team abbreviation (e.g., "KC", "BAL")
 * @param size - Logo size (default 100)
 * @returns URL to the team's logo
 */
export function getTeamLogoUrl(team: string, size: number = 100): string {
	const teamId = ESPN_TEAM_IDS[team];
	if (!teamId) {
		// Return a placeholder for unknown teams
		return `https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/nfl.png`;
	}
	return `https://a.espncdn.com/i/teamlogos/nfl/500/${team.toLowerCase()}.png`;
}

/**
 * Get team full name from abbreviation
 */
export const TEAM_NAMES: Record<string, string> = {
	ARI: 'Arizona Cardinals',
	ATL: 'Atlanta Falcons',
	BAL: 'Baltimore Ravens',
	BUF: 'Buffalo Bills',
	CAR: 'Carolina Panthers',
	CHI: 'Chicago Bears',
	CIN: 'Cincinnati Bengals',
	CLE: 'Cleveland Browns',
	DAL: 'Dallas Cowboys',
	DEN: 'Denver Broncos',
	DET: 'Detroit Lions',
	GB: 'Green Bay Packers',
	HOU: 'Houston Texans',
	IND: 'Indianapolis Colts',
	JAX: 'Jacksonville Jaguars',
	KC: 'Kansas City Chiefs',
	LA: 'Los Angeles Rams',
	LAC: 'Los Angeles Chargers',
	LV: 'Las Vegas Raiders',
	MIA: 'Miami Dolphins',
	MIN: 'Minnesota Vikings',
	NE: 'New England Patriots',
	NO: 'New Orleans Saints',
	NYG: 'New York Giants',
	NYJ: 'New York Jets',
	PHI: 'Philadelphia Eagles',
	PIT: 'Pittsburgh Steelers',
	SEA: 'Seattle Seahawks',
	SF: 'San Francisco 49ers',
	TB: 'Tampa Bay Buccaneers',
	TEN: 'Tennessee Titans',
	WAS: 'Washington Commanders'
};

export function getTeamName(team: string): string {
	return TEAM_NAMES[team] || team;
}
