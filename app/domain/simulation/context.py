from collections import defaultdict, deque


class RollingContext:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.team_history = defaultdict(lambda: deque(maxlen=window_size))

    def update(self, match):
        # store basic info
        self.team_history[match.home_team].append(match)
        self.team_history[match.away_team].append(match)

    def get_recent(self, team):
        return list(self.team_history[team])

    def win_rate(self, team):
        matches = self.get_recent(team)
        if not matches:
            return None

        wins = 0
        for m in matches:
            if m.home_team == team and m.result == "H":
                wins += 1
            elif m.away_team == team and m.result == "A":
                wins += 1

        return wins / len(matches)
