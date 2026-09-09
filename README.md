# BetFriends

A small Flask web app for running a **friends-only cricket prediction game**. During a
match window, friends log in and pick which team they think will win each upcoming
game. After the real results come in, the app scores everyone's picks and keeps a
running "who called it right" leaderboard for the season.

It was built for the IPL 2024 season and deployed on an AWS EC2 instance so a group
of friends could play along.

> **Note:** "betting" here means picks/predictions for fun among friends — there is no
> real money, payments, or gambling integration. The "profit" numbers are just a
> points model (see [Scoring](#scoring)).

---

## How it works

1. **Admin opens a poll window.** From the admin dashboard, the admin adds a
   `start_date`–`end_date` range. Only one window is active at a time.
2. **Friends make picks.** While the window is active, a player goes to `/poll`,
   selects their name (or adds a new one), and chooses a winner for every match
   scheduled inside the window.
3. **Real results are pulled in.** A helper script fetches completed match results
   from [CricAPI](https://cricapi.com/) and stores them in `match_standing.json`.
4. **Scores update.** Each player's pick is compared against the actual winner. A
   correct pick scores `1`, a wrong pick scores `0`.
5. **Leaderboard.** The home page and the player-inputs page show each player's
   record and net points across the season.

## Scoring

Scoring is a simple pot model, calculated per match in
`functions/calculation_functions.py`:

- Every player "stakes" 1 unit on each match they pick.
- Wrong picks lose their stake; the losing stakes for that match are split evenly
  among the players who picked correctly.
- A correct pick returns `1 + (losers / winners)`; a wrong pick returns `0`.
- **Net profit** for a player = total returns − total staked, summed over all matches.

So a player who is right more often than the group average ends the season positive.

---

## Routes

| Route | Who | Purpose |
|-------|-----|---------|
| `/login`, `/logout` | everyone | Session login (username + password) |
| `/` | player | Home: latest match result + season leaderboard |
| `/poll` | player | Make picks for the active window (shows `poll_closed` if none) |
| `/submit_poll` | player | `POST` target for the pick form |
| `/schedule` | player | Full season fixture list |
| `/player_inputs` | player | Per-player breakdown of picks vs. actual winners |
| `/admin_dashboard` | admin | Create / view poll windows |
| `/delete_date` | admin | Remove a poll window |

Admin vs. player is decided by the `role` field in `users_login.json`.

## Data storage

There is **no database**. All state is JSON stored in an **AWS S3 bucket**, read and
written through `functions/s3_file_manager.py`:

| File (S3 key) | Contents |
|---------------|----------|
| `data/users_login.json` | Usernames, passwords, roles |
| `data/ipl_schedule.json` | Season fixture list |
| `data/poll_date.json` | Poll windows and which one is active |
| `data/poll.json` | Every player's submitted picks |
| `data/match_standing.json` | Actual match results (from CricAPI) |
| `data/players_stats.json` | Derived per-player scoring |

The `data/` folder in this repo holds sample/seed copies of these files.

## Helper scripts (`debug/`)

Ad-hoc scripts, run by hand, not part of the web server:

- `call_api.py` — fetch finished match results from CricAPI into `match_standing.json`
- `poll_stop.py` — mark the current poll window inactive (close voting)
- `update_poll_dates.py` — roll the active window forward to the next set of dates
- `read_from_mg.py`, `write_to_db.py`, `mongo_functions.py` — leftovers from an
  earlier MongoDB version (see [Project history](#project-history))

---

## Configuration

All secrets and environment-specific values are read from environment variables
(loaded from a local `.env` file via `config.py`). Nothing sensitive is committed.

```bash
cp .env.example .env      # then edit .env
```

| Variable | Used by | Purpose |
|----------|---------|---------|
| `S3_BUCKET` | web app + debug scripts | Bucket holding the `data/*.json` files |
| `FLASK_SECRET_KEY` | web app | Session signing key |
| `CRICAPI_KEY` | `debug/call_api.py` | CricAPI auth |
| `CRICAPI_SERIES_ID` | `debug/call_api.py` | Which tournament to pull results for |
| `MONGO_URI` | `debug/read_from_mg.py`, `debug/write_to_db.py` | Only the leftover Mongo scripts |

AWS credentials for boto3 come from the standard sources (`~/.aws/credentials`, an
EC2 instance role, or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` /
`AWS_DEFAULT_REGION`).

## Running locally

Requirements: Python 3.11, an AWS account with an S3 bucket, and a CricAPI key.

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in real values
python main.py            # serves on http://0.0.0.0:5000
```

Before first run, upload the seed files from `data/` to `s3://<your-bucket>/data/`
(and set real passwords in `users_login.json` first — the committed copy has
placeholders).

## Deployment

Ran directly on an AWS EC2 instance (`python main.py` behind the instance's
security group). No container or PaaS.

---

## Project history

This app went through three iterations of the same idea:

| Iteration | Storage | Notes |
|-----------|---------|-------|
| `cricket_testing` | MongoDB Atlas | First prototype |
| `betfriends` | Local JSON files | Second pass, no auth |
| **`betfriends_aws`** (this one) | AWS S3 + login/roles | The version that was actually deployed |

The two earlier versions live in the original monorepo alongside this folder.

## Tech

Flask · Jinja templates · Bootstrap 5 (CDN) · boto3 / AWS S3 · CricAPI

## Known rough edges

This was a personal hobby project. A few things a fresh build would fix:

- Passwords are stored and compared in plaintext (in `users_login.json` on S3).
- No CSRF protection on forms. `FLASK_SECRET_KEY` should be set in `.env`; if it
  isn't, a random key is used and sessions drop on every restart.
- `debug/compare_teams` parsing relies on the exact phrasing of CricAPI status
  strings ("X won by N runs/wkts").
- Concurrent poll submissions can race (read-modify-write on a single S3 JSON file).

## Security / secrets

The working tree has been scrubbed: secrets now live only in `.env` (git-ignored),
and `data/api_data.json` / `data/users_login.json` hold placeholders.

**However**, earlier commits in this project's history still contain the real
CricAPI key, RapidAPI key, MongoDB Atlas connection string, and app passwords.
Before this code is made public you must:

1. Revoke/rotate the CricAPI key, the RapidAPI key, and the MongoDB Atlas password.
2. Either publish from a fresh repository (no history) or rewrite the existing
   history (`git filter-repo` / BFG) — removing the files from the current commit
   is not enough.
