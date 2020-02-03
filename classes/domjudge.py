import json
import requests
from html import escape
from functools import reduce

from utils.XML import XML_dump
from utils.utils import dtime2timestamp, ctime2timestamp, make_ordinal

class DOMjudge:

    def __init__(self, url, key):
        self.url, self.key = url, key
        self.load_data()
        self.prep_data()

    def API(self, method):
        key = "Basic %s" % self.key
        req_url = self.url + method
        print ("[   ] GET %s" % req_url, end='\r')
        req_hdr = { 'Authorization': key }
        res = requests.get(req_url, headers=req_hdr)
        print ("[%d] GET %s" % (res.status_code, req_url))
        return json.loads(res.text)

    def load_data(self):
        self.load_contest_info()
        self.load_groups()
        self.load_teams()
        self.load_submissions()
        self.load_judgements()
        self.load_judgement_types()
        self.load_problems()
        self.load_scoreboard()

    def load_contest_info(self):
        self.contest_info = self.API("/")

    def load_groups(self):
        groups = self.API("/groups")
        func = lambda group : not group['hidden']
        self.groups = list(filter(func, groups))

    def load_teams(self):
        teams = self.API("/teams")
        group_ids = [group['id'] for group in self.groups]
        same = lambda x, y: list(set(x) & set(y))
        func = lambda team: len(same(team['group_ids'], group_ids))
        self.teams = list(filter(func, teams))

    def load_submissions(self):
        submissions = self.API('/submissions')
        team_ids = [team['id'] for team in self.teams]
        func = lambda submission: submission['team_id'] in team_ids
        self.submissions = list(filter(func, submissions))

    def load_judgements(self):
        judgements = self.API('/judgements')
        submission_ids = [submission['id'] for submission in self.submissions]
        func = lambda judgement: judgement['valid'] and judgement['submission_id'] in submission_ids
        self.judgements = list(filter(func, judgements))

    def load_judgement_types(self):
        self.judgement_types = self.API('/judgement-types')

    def load_problems(self):
        self.problems = self.API('/problems')

    def load_scoreboard(self):
        self.scoreboard = self.API('/scoreboard')

    def prep_data(self):
        self.submission_judgement_type()
        self.scoreboard_rank()

    def submission_judgement_type(self):
        id2idx = { submission['id']: idx for idx, submission in enumerate(self.submissions) }
        judgement_types = { judgement_type['id']: judgement_type for judgement_type in self.judgement_types }
        for judgement in self.judgements:
            idx = id2idx[judgement['submission_id']]
            self.submissions[idx]['judgement_type'] = judgement_types[judgement['judgement_type_id']]

    def scoreboard_rank(self):
        for row in self.scoreboard['rows']:
            team_solved_func = lambda submission: submission['team_id'] == row['team_id'] and submission['judgement_type']['solved']
            team_submissions = list(filter(team_solved_func, self.submissions))
            max_submission_id, problems = 0, set()
            for submission in team_submissions:
                if submission['problem_id'] in problems:
                    continue
                problems.add(submission['problem_id'])
                max_submission_id = max(max_submission_id, int(submission['id']))
            row['score']['max_submission_id'] = max_submission_id
        self.scoreboard['rows'].sort(key = lambda x: (-x['score']['num_solved'], x['score']['total_time'], x['score']['max_submission_id']))
        self.scoreboard['rows'][0]['rank'] = 1
        for idx in range(len(self.scoreboard['rows']) - 1):
            self.scoreboard['rows'][idx + 1]['rank'] = idx + 2
            if self.scoreboard['rows'][idx]['score'] == self.scoreboard['rows'][idx + 1]['score']:
                self.scoreboard['rows'][idx + 1]['rank'] = self.scoreboard['rows'][idx]['rank']

    def export_XML(self, filename):
        with open(filename, 'w') as f:
           f.write(XML_dump(self.resolver_formatter()))

    def resolver_formatter(self):
        return { 'contest': self.resolver_contest_formatter() }

    def resolver_contest_formatter(self):
        return {
            'info': self.resolver_info_formatter(),
            'judgement': self.resolver_judgement_formatter(),
            'problem': self.resolver_problem_formatter(),
            'team': self.resolver_team_formatter(),
            'run': self.resolver_run_formatter(),
            'award': self.resolver_award_formatter(),
            'finalized': self.resolver_finalized_formatter()
        }
    
    def resolver_info_formatter(self):
        return {
            'title': self.contest_info['shortname'],
            'length': self.contest_info['duration'],
            'scoreboard-freeze-length': self.contest_info['scoreboard_freeze_duration'],
            'starttime': dtime2timestamp(self.contest_info['start_time']),
        }

    def resolver_judgement_formatter(self):
        return [{ 
            'acronym': judgement_type['id'] 
        } for judgement_type in self.judgement_types ]

    def resolver_problem_formatter(self):
        return [{ 
            'id': problem['ordinal'] + 1
        } for problem in self.problems ]

    def resolver_team_formatter(self):
        return [{
            'id': team['id'],
            'name': escape(team['name']),
            'university': ''
        } for team in self.teams ]

    def resolver_run_formatter(self):
        problems = { problem['id']: problem for problem in self.problems }
        return [{
            'id': submission['id'],
            'problem': problems[submission['problem_id']]['ordinal'] + 1,
            'team': submission['team_id'],
            'judged': "true",
            'result': submission['judgement_type']['id'],
            'solved': str(submission['judgement_type']['solved']).lower(),
            'penalty': str(submission['judgement_type']['penalty']).lower(),
            'time': ctime2timestamp(submission['contest_time'])
        } for submission in self.submissions ]

    def resolver_award_formatter(self):
        return reduce(lambda x, y: x + y, [
            self.resolver_award_first_solved_formatter(),
            self.resolver_award_top_team_formatter(3),
            self.resolver_award_first_WA()
        ], [])

    def award(self, id, citation, team_ids):
        return {
            'id': id,
            'citation': citation,
            'show': 'true',
            'teamId': team_ids
        }

    def resolver_award_first_solved_formatter(self):
        first_solved, first_solved_award = [ False for i in range(len(self.problems)) ], []
        problem_id2idx = { problem['id']: problem['ordinal'] for problem in self.problems }
        for submission in self.submissions:
            if not submission['judgement_type']['solved']:
                continue
            if ctime2timestamp(submission['contest_time']) >= ctime2timestamp(self.contest_info['duration']) - ctime2timestamp(self.contest_info['scoreboard_freeze_duration']):
                continue
            idx = problem_id2idx[submission['problem_id']]
            if first_solved[idx]:
                continue
            first_solved[idx] = True
            first_solved_award.append(self.award('first-to-solve-%c' % chr(65 + idx), 'First to solve problem %c' % chr(65 + idx), submission['team_id']))
        return first_solved_award

    def resolver_award_top_team_formatter(self, rank):
        buf = [[] for i in range(rank + 1)]
        for row in self.scoreboard['rows']:
            if row['rank'] > rank:
                break
            buf[row['rank']].append(row['team_id'])
        top_team_award = []
        for idx, team_ids in enumerate(buf):
            top_team_award.append(self.award(make_ordinal(idx), '%s Place' % make_ordinal(idx), team_ids))
        return top_team_award

    def resolver_award_first_WA(self):
        submissions = list(filter(lambda submission: submission['judgement_type']['id'] == "WA", self.submissions))
        if len(submissions) == 0:
            return []
        return [
            self.award("first-WA", "First WA", submissions[0]['team_id'])
        ]

    def resolver_finalized_formatter(self):
        return {
            'last-gold': 0,
            'last-silver': 0,
            'last-bronze': 0,
            'timestamp': 0
        }
