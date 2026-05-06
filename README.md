# NFL Momentum Analyzer

Analyze NFL game momentum through play-by-play data visualization.

## Features

- **Event-based momentum calculation** - Touchdowns, turnovers, sacks, and big plays all contribute to momentum shifts
- **Interactive charts** - Visualize momentum swings throughout the game
- **Shareable links** - Create links to share momentum graphs with others
- **Export options** - Download as PNG or SVG

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: SvelteKit + TailwindCSS + Chart.js
- **Database**: PostgreSQL
- **Data Source**: nflfastR via nfl_data_py

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your database credentials

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Load NFL Data

```bash
cd backend

# Load a specific season
python -m app.scripts.backfill --seasons 2024

# Or load last 5 years
python -m app.scripts.backfill --all-recent
```

## API Endpoints

### Games
- `GET /api/games/seasons` - Get available seasons and weeks
- `GET /api/games/{season}/{week}` - Get games for a week
- `GET /api/games/game/{game_id}` - Get game details

### Momentum
- `GET /api/momentum/{game_id}` - Get momentum data
- `GET /api/momentum/{game_id}/export/png` - Download PNG
- `GET /api/momentum/{game_id}/export/svg` - Download SVG

### Sharing
- `POST /api/share/{game_id}` - Create share link
- `GET /api/share/{share_code}` - Get shared graph

## Momentum Algorithm

The momentum score is calculated based on play-by-play events:

| Event | Points |
|-------|--------|
| Passing/Rushing TD | +15 |
| Defensive/Return TD | +25 |
| Interception | +12 |
| Fumble Lost | +10 |
| Sack | +5 |
| 4th Down Conversion | +5 |
| 4th Down Stop | +6 |
| Explosive Play (20+ yds) | +6 |
| Safety | +15 |

**Decay**: Momentum loses ~8% per play to reflect recency
**Streak Bonus**: Consecutive positive events multiply momentum (up to 1.5x)

## Deployment

### Railway (Backend + PostgreSQL)

1. Create a new Railway project
2. Add PostgreSQL database
3. Deploy backend from GitHub
4. Set `DATABASE_URL` from Railway's PostgreSQL

### Vercel (Frontend)

1. Import repository to Vercel
2. Set root directory to `frontend`
3. Add environment variable `VITE_API_URL` pointing to Railway backend

## License

MIT
