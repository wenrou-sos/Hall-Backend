
class ClubRight():
    def __init__(self, club_id):
        self.club_id = club_id
        # 照順序，詳情設定可見資料表 club_right 註解
        # 館主、一級代理、二級代理、三級代理、四級代理、五級代理、六級代理、管理員、一般成員
        self.visiblemember_ls = [0, 1, 1, 1, 1, 1, 1, 0, 2]
        self.creditfrom_ls = [0, 1, 1, 1, 1, 1, 1, 0, 2]
        self.credittransfer_ls = [1, 1, 1, 1, 1, 1, 1, 0, 1]
        self.transferlimit_ls = [2, 1, 1, 1, 1, 1, 1, 0, 1]
        self.createroom_ls = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.setroom_ls = [1, 0, 0, 0, 0, 0, 0, 1, 0]
        self.joinroom_ls = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.dismissroom_ls = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.invite_ls = [1, 1, 1, 1, 1, 1, 1, 1, 0]
        self.banplaygame_ls = [1, 1, 1, 1, 1, 1, 1, 1, 0]
        self.banchat_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.winloselimit_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.setmembernumber_ls = [1, 0, 0, 0, 0, 0, 0, 1, 0]
        self.kick_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.blacklist_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.setproxy_ls = [1, 2, 3, 4, 5, 6, 0, 1, 0]
        self.allocate_ls = [1, 0, 0, 0, 0, 0, 0, 1, 0]
        self.deleteproxymember_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.betsearch_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.errorbet_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.creditdetail_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]
        self.creditreport_ls = [2, 1, 1, 1, 1, 1, 1, 2, 0]

    def generate_sql_insert_command(self, position):
        insert_column = '''
            club_id, position, visiblemember, creditfrom, credittransfer, 
            transferlimit, createroom, setroom, joinroom, dismissroom, invite, banplaygame, 
            banchat, winloselimit, setmembernumber, kick, blacklist, setproxy, 
            allocate, deleteproxymember, betsearch, errorbet, creditdetail, creditreport
        '''

        insert_value = '''
            "{}", {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, 
            {}, {}, {}, {}, {}
        '''.format(
            self.club_id,
            position,
            self.visiblemember_ls[position],
            self.creditfrom_ls[position],
            self.credittransfer_ls[position],
            self.transferlimit_ls[position],
            self.createroom_ls[position],
            self.setroom_ls[position],
            self.joinroom_ls[position],
            self.dismissroom_ls[position],
            self.invite_ls[position],
            self.banplaygame_ls[position],
            self.banchat_ls[position],
            self.winloselimit_ls[position],
            self.setmembernumber_ls[position],
            self.kick_ls[position],
            self.blacklist_ls[position],
            self.setproxy_ls[position],
            self.allocate_ls[position],
            self.deleteproxymember_ls[position],
            self.betsearch_ls[position],
            self.errorbet_ls[position],
            self.creditdetail_ls[position],
            self.creditreport_ls[position]
        )

        return 'INSERT INTO club_right({}) VALUE({})'.format(insert_column, insert_value)
