from argparse import ArgumentParser
import json
import requests
from dateutil import parser
from html import escape
from functools import reduce

class Domjudge:
    def __init__(self, config):
        with open(config) as f:
            self.config = json.load(f)
        self.load_data();

    def API(self, method):
        key = "Basic {0}".format(self.config['key'])
        req_url = self.config['url'] + method
        req_hdr = { 'Authorization': key }
        res = requests.get(req_url, headers=req_hdr)
        return json.loads(res.text)

    def load_data(self):
        self.load_contest_info()
        self.load_groups()
        self.load_teams()
        self.load_submissions()
        self.load_judgements()
        self.load_judgement_types()
        self.load_scoreboard()
        self.load_problems()

    def load_contest_info(self):
        self.contest_info = self.API("")

    def load_groups(self):
        func = lambda group : not group['hidden']
        groups = self.API('/groups')
        self.lgroups, self.dgroups = self.filter(func, groups)

    def load_teams(self):
        group_ids = [group['id'] for group in self.lgroups]
        same = lambda x, y: list(set(x) & set(y))
        func = lambda team: len(same(team['group_ids'], group_ids))
        teams = self.API('/teams')
        self.lteams, self.dteams = self.filter(func, teams)

    def load_submissions(self):
        team_ids = [team['id'] for team in self.lteams]
        func = lambda submission: submission['team_id'] in team_ids
        submissions = self.API('/submissions')
        self.lsubmissions, self.dsubmissions = self.filter(func, submissions)

    def load_judgements(self):
        submission_ids = [submission['id'] for submission in self.lsubmissions]
        func = lambda judgement: judgement['valid'] and judgement['submission_id'] in submission_ids
        judgements = self.API('/judgements')
        self.ljudgements, self.djudgements = self.filter(func, judgements)

    def load_judgement_types(self):
        func = lambda x : True
        judgement_types = self.API('/judgement-types')
        self.ljudgement_types, self.djudgement_types = self.filter(func, judgement_types)

    def load_scoreboard(self):
        self.scoreboard = self.API('/scoreboard')

    def load_problems(self):
        func = lambda x : True
        problems = self.API('/problems')
        self.lproblems, self.dproblems = self.filter(func, problems)

    def filter(self, func, items):
        l = list(filter(func, items))
        d = { item['id'] : item for item in items }
        return l, d

    def export_xml(self):
        with open(self.config['xml'], 'w') as f:
            self.contest_xml(f)
            
    def contest_xml(self, f):
        f.write('<contest>\n')
        self.info_xml(f)
        self.judgements_xml(f)
        self.problems_xml(f)
        self.teams_xml(f)
        self.runs_xml(f)
        self.awards_xml(f)
        self.finalized_xml(f)
        f.write('</contest>\n')

    def info_xml(self, f):
        f.write('<info>\n')
        f.write("  <title>{0}</title>\n".format(self.contest_info['shortname']))
        f.write("  <length>{0}</length>\n".format(self.contest_info['duration']))
        f.write("  <scoreboard-freeze-length>{0}</scoreboard-freeze-length>\n".format(self.contest_info['scoreboard_freeze_duration']))
        f.write("  <starttime>{0}</starttime>\n".format(dtime2timestamp(self.contest_info['start_time'])))
        f.write('</info>\n')

    def judgements_xml(self, f):
        for judgement_type in self.ljudgement_types:
            f.write("<judgement><acronym>")
            f.write(judgement_type['id'])
            f.write("</acronym></judgement>\n")

    def problems_xml(self, f):
        for problem in self.lproblems:
            f.write("<problem><id>{0}</id></problem>\n".format(problem['ordinal'] + 1))

    def teams_xml(self, f):
        for team in self.lteams:
            f.write('<team>\n')
            f.write("  <id>{0}</id>\n".format(team['id']))
            f.write("  <name>{0}</name>\n".format(escape(team['name'])))
            f.write("  <university></university>\n")
            f.write('</team>\n')

    def runs_xml(self, f):
        for submission in self.lsubmissions:
            result = next(judgement['judgement_type_id'] for judgement in self.ljudgements if judgement['submission_id'] == submission['id'])
            judgement_type = self.djudgement_types[result]
            f.write('<run>\n')
            f.write("  <id>{0}</id>\n".format(submission['id']))
            f.write("  <problem>{0}</problem>\n".format(self.dproblems[submission['problem_id']]['ordinal'] + 1))
            f.write("  <team>{0}</team>\n".format(submission['team_id']))
            f.write('  <judged>true</judged>\n')
            f.write("  <result>{0}</result>\n".format(result))
            f.write("  <solved>{0}</solved>\n".format(judgement_type['solved']).lower())
            f.write("  <penalty>{0}</penalty>\n".format(judgement_type['penalty']).lower())
            f.write("  <time>{0}</time>\n".format(ctime2timestamp(submission['contest_time'])))
            f.write('</run>\n')

    def awards_xml(self, f):
        self.top_team(f, 10)
        self.first_solved(f)

    def first_solved(self, f):
        first_solved = [ False for i in range(len(self.lproblems)) ]
        for submission in self.lsubmissions:
            result = next(judgement['judgement_type_id'] for judgement in self.ljudgements if judgement['submission_id'] == submission['id'])
            if result != 'AC':
                continue
            if ctime2timestamp(submission['contest_time']) >= ctime2timestamp(self.contest_info['duration']) - ctime2timestamp(self.contest_info['scoreboard_freeze_duration']):
                continue
            idx = self.dproblems[submission['problem_id']]['ordinal']
            if first_solved[idx]:
                continue
            first_solved[idx] = True
            self.award(f, "first-to-solve-{0}".format(chr(65 + idx)), "First to solve problem {0}".format(chr(65 + idx)), submission['team_id'])
            
            


    def top_team(self, f, n):
        for i in range(n):
            if len(self.scoreboard['rows']) > i:
                self.award(f, make_ordinal(i + 1), "{0} Place".format(make_ordinal(i + 1)), self.scoreboard['rows'][i]['team_id'])

    def award(self, f, id , citation, team_id):
        f.write('<award>\n')
        f.write("  <id>{0}</id>\n".format(id))
        f.write("  <citation>{0}</citation>\n".format(citation))
        f.write('  <show>true</show>\n')
        f.write("  <teamId>{0}</teamId>\n".format(team_id))
        f.write('</award>\n')

    def finalized_xml(self, f):
        f.write("<finalized>\n")
        f.write("  <last-gold>0</last-gold>\n")
        f.write("  <last-silver>0</last-silver>\n")
        f.write("  <last-bronze>0</last-bronze>\n")
        f.write("  <timestamp>0</timestamp>\n")
        f.write("</finalized>\n")


def dtime2timestamp(dtime):
    return parser.parse(dtime).timestamp()

def ctime2timestamp(ctime):
    return reduce(lambda x, y: 60.0 * float(x) + float(y), ctime.split(':'), 0.0)

def make_ordinal(n):
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

def Parser():
    parser = ArgumentParser()
    parser.add_argument('--config', help='config file', default='config.json')
    return vars(parser.parse_args())

def dprint(dict):
    print(json.dumps(dict, indent=4))

def main():
    Domjudge(Parser()['config']).export_xml()
    
if __name__ == '__main__':
    main()
