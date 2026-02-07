class Developer:
    def __init__(self):
        self.team = None

    def set_team(self, team):
        self.team = team

class Team:
    def __init__(self):
        self.devs = []

    def add_dev(self, dev: Developer):
        self.devs.append(dev)

class User:
    def __init__(self):
        self.groups = []
    
class Group:
    def __init__(self):
        self.users = []