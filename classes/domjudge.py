import json
import requests
from html import escape
from functools import reduce

from utils.XML import XML_dump
from utils.utils import dtime2timestamp, ctime2timestamp, make_ordinal

class DOMjudge:

    def __init__(self, config):
        self.config = config
        self.load_data()
        self.prep_data()

    def API(self, method):
        key = "Basic %s" % self.config['key']
        req_url = self.config['url'] + method
        print ("[   ] GET %s" % req_url, end='\r')
        req_hdr = { 'Authorization': key }
        res = requests.get(req_url, headers=req_hdr,  verify=False)
        print ("[%d] GET %s" % (res.status_code, req_url))
        return json.loads(res.text)

    def load_data(self):
        self.load_contest_info()
        self.load_groups()
        self.load_organizations()
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
        groups = list(filter(func, groups))
        self.groups = {}
        for group in groups:
            self.groups[group['id']] = group

    def load_organizations(self):
        organizations = self.API("/organizations")
        self.organizations = {}
        for organization in organizations:
            self.organizations[organization['icpc_id']] = organization

    def load_teams(self):
        teams = self.API("/teams")
        group_ids = [group['id'] for group in self.groups.values()]
        same = lambda x, y: list(set(x) & set(y))
        func = lambda team: len(same(team['group_ids'], group_ids))
        self.teams = list(filter(func, teams))
        self.team_to_categories = {}
        for team in self.teams:
            group_id = team['group_ids']
            team_id = team['id']
            self.team_to_categories[team_id] = group_id

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
    
    def export(self, filename):
        self.export_XML(filename + '.xml')
        self.export_result(filename + '.csv')

    def export_XML(self, filename):
        with open(filename, 'w', encoding="utf-8") as f:
           f.write(XML_dump(self.resolver_formatter()))

    def export_result(self, filename):
        return
        with open(filename, 'w', encoding="utf-8") as f:
           f.write(XML_dump(self.resolver_formatter()))

    def resolver_formatter(self):
        return { 'contest': self.resolver_contest_formatter() }

    def resolver_contest_formatter(self):
        return {
            'info': self.resolver_info_formatter(),
            'problem': self.resolver_problem_formatter(),
            'region': self.resolver_group_formatter(),
            'team': self.resolver_team_formatter(),
            'judgement': self.resolver_judgement_formatter(),
            'run': self.resolver_run_formatter(),
            'award': self.resolver_award_formatter(),
            'finalized': self.resolver_finalized_formatter()
        }

    def resolver_group_formatter(self):
        return [{
            'external-id': group['id'],
            'name': group['name']
        } for group in self.groups.values()]
    
    def resolver_info_formatter(self):
        return {
            'contest-id': self.contest_info['id'],
            'title': self.contest_info['name'],
            'short-title': self.contest_info['shortname'],
            'length': self.contest_info['duration'],
            'scoreboard-freeze-length': self.contest_info['scoreboard_freeze_duration'],
            'starttime': dtime2timestamp(self.contest_info['start_time']),
            'penalty': self.contest_info['penalty_time'],
        }

    def resolver_judgement_formatter(self):
        return [{ 
            'acronym': judgement_type['id'] 
        } for judgement_type in self.judgement_types ]

    def resolver_problem_formatter(self):
        return [{ 
            'id': problem['ordinal'] + 1,
            'label': problem['label'],
            'name': problem['name'],
            # 'color': problem['color'],
            # 'rgb': problem['rgb'],
        } for problem in self.problems ]

    def resolver_team_formatter(self):
        return [{
            'id': team['id'],
            'external-id': team['icpc_id'],
            'name': escape(team['name']),
            'university': self.organizations[team['organization_id']]['formal_name'],
            'university-short-name': self.organizations[team['organization_id']]['shortname'],
            'region': self.groups[team['group_ids'][0]]['name'],
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
            self.resolver_award_winner_formatter(),
            self.resolver_award_medal_formatter(),
            self.resolver_award_best_girl_formatter(),
            self.resolver_award_last_AC_formatter()
            # self.resolver_award_first_WA()
        ], [])

    def award(self, id, citation, team_ids):
        return {
            'id': id,
            'citation': citation,
            'show': 'true',
            'teamId': team_ids
        }

    def get_team_categories(self, team_id):
        return self.team_to_categories[team_id][0]

    def resolver_award_first_solved_formatter(self):
        first_solved, first_solved_award = [ False for _ in range(len(self.problems)) ], []
        problem_id2idx = { problem['id']: problem['ordinal'] for problem in self.problems }
        for submission in self.submissions:
            if not submission['judgement_type']['solved']:
                continue
            if self.get_team_categories(submission['team_id']) in self.config['no_occupy_award_categories']:   #打星队伍不评奖
                continue
            if ctime2timestamp(submission['contest_time']) >= ctime2timestamp(self.contest_info['duration']) - ctime2timestamp(self.contest_info['scoreboard_freeze_duration']):
                continue
            idx = problem_id2idx[submission['problem_id']]
            if first_solved[idx]:
                continue
            first_solved[idx] = True
            first_solved_award.append(self.award('first-to-solve-%c' % chr(65 + idx), 'First to solve problem %c' % chr(65 + idx), submission['team_id']))
        return first_solved_award

    def resolver_award_top_team_formatter(self, rank):  #WARNING: 排名相同无法一起评
        buf = [[] for _ in range(rank + 1)]
        cnt = 0
        for row in self.scoreboard['rows']:
            if cnt == rank:
                break
            if self.get_team_categories(row['team_id']) in self.config['no_occupy_award_categories']:
                continue
            cnt += 1
            buf[cnt].append(row['team_id'])
        top_team_award = []
        for idx, team_ids in enumerate(buf):
            top_team_award.append(self.award(f'rank-{idx}', '%s Place' % make_ordinal(idx), team_ids))
        return top_team_award

    def resolver_award_winner_formatter(self):  #WARNING: 排名相同无法一起评
        rank = 1
        buf = [[] for _ in range(rank + 1)]
        cnt = 0
        for row in self.scoreboard['rows']:
            if cnt == rank:
                break
            cnt += 1
            buf[cnt].append(row['team_id'])
        winner_award = []
        for _, team_ids in enumerate(buf):
            winner_award.append(self.award(f'winner', 'World Champion', team_ids))
        return winner_award

    def resolver_award_best_girl_formatter(self):
        best_girls_team_id = -1
        for row in self.scoreboard['rows']:
            if self.get_team_categories(row['team_id']) in self.config['award_best_girl']:
                best_girls_team_id = row['team_id']
                break
            if row['rank'] > self.limited: # 限定最佳女队必得奖牌
                break
        best_girls_award = []    
        if best_girls_team_id != -1:
            best_girls_award.append(self.award(f"group-winner-{self.config['award_best_girl'][0]}", "The Best Girls's Team", best_girls_team_id))
        return best_girls_award

    def resolver_award_medal_formatter(self):
        medal_team_award = []
        # award for gold
        totle = self.config['gold']
        buf = []
        pos = 0
        while totle > 0:
            row = self.scoreboard['rows'][pos]
            if self.get_team_categories(row['team_id']) in self.config['no_occupy_award_categories']:
                totle += 1
            buf.append(row['team_id'])
            totle -= 1
            pos += 1
        medal_team_award.append(self.award("gold-medal", "Gold Medalist", buf))
        # award for silver
        totle = self.config['silver']
        buf = []
        while totle > 0:
            row = self.scoreboard['rows'][pos]
            if self.get_team_categories(row['team_id']) in self.config['no_occupy_award_categories']:
                totle += 1
            buf.append(row['team_id'])
            totle -= 1
            pos += 1
        medal_team_award.append(self.award("silver-medal", "Silver Medalist", buf))
        # award for bronze
        totle = self.config['bronze']
        buf = []
        while totle > 0:
            row = self.scoreboard['rows'][pos]
            if self.get_team_categories(row['team_id']) in self.config['no_occupy_award_categories']:
                totle += 1
            buf.append(row['team_id'])
            totle -= 1
            pos += 1
        medal_team_award.append(self.award("bronze-medal", "Bronze Medalist", buf))
        self.limited = pos - 1
        return medal_team_award

    def resolver_award_last_AC_formatter(self):
        submissions = list(filter(lambda submission: submission['judgement_type']['id'] == "AC", self.submissions))
        if len(submissions) == 0:
            return []
        return [
            self.award("last-AC", "Tenacious Award", submissions[-1]['team_id'])
        ]

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
