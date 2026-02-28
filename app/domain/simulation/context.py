from collections import defaultdict, deque


class RollingContext:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.team_history = defaultdict(lambda: deque(maxlen=window_size))

    def update(self, match):
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

    def points(self, team):
        matches = self.get_recent(team)
        if not matches:
            return None

        pts = 0
        for m in matches:
            if m.home_team == team:
                if m.result == "H":
                    pts += 3
                elif m.result == "D":
                    pts += 1
            else:  # away
                if m.result == "A":
                    pts += 3
                elif m.result == "D":
                    pts += 1
        return pts

    def goal_diff(self, team):
        matches = self.get_recent(team)
        if not matches:
            return None

        gd = 0
        for m in matches:
            if m.home_team == team:
                gd += m.home_goals - m.away_goals
            else:
                gd += m.away_goals - m.home_goals
        return gd

    def features_for_match(self, match):
        hw = self.win_rate(match.home_team)
        aw = self.win_rate(match.away_team)
        hp = self.points(match.home_team)
        ap = self.points(match.away_team)
        hgd = self.goal_diff(match.home_team)
        agd = self.goal_diff(match.away_team)

        # return None-safe diffs
        def diff(a, b):
            if a is None or b is None:
                return None
            return a - b

        return {
            # basic
            "home_win_rate": hw,
            "away_win_rate": aw,
            "home_points": hp,
            "away_points": ap,
            "home_goal_diff": hgd,
            "away_goal_diff": agd,
            # diffs
            "points_diff": diff(hp, ap),
            "goal_diff_diff": diff(hgd, agd),
        }
