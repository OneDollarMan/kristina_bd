from mysql.connector import connect, Error
import config


class GarageRepo:

    ROLE_USER = 0
    ROLE_STUDENT = 1
    ROLE_SUPERVISOR = 2

    def __init__(self):
        self.host = config.mysql_host
        self.user = config.mysql_user
        self.password = config.mysql_password
        self.database = config.mysql_database
        self.connection = self.get_connect()
        self.cursor = self.connection.cursor()

        self.get_tables = lambda: self.raw_query("SHOW TABLES")

        self.get_user = lambda username: self.raw_query("SELECT * FROM user WHERE username='%s'" % username)
        self.login_user = lambda username, password: self.get_query("SELECT * FROM user WHERE username='%s' AND password='%s'" % (username, password))
        self.add_user = lambda username, fio, age, password: self.write_query("INSERT INTO user SET username='%s', fio='%s', age='%s', password='%s', role=0" % (username, fio, age, password))
        self.get_all_zero_users = lambda: self.raw_query("SELECT * FROM user WHERE role=0")

        self.add_profession = lambda name, abbr: self.write_query("INSERT INTO profession SET name='%s', abbr='%s'" % (name, abbr))
        self.get_professions = lambda: self.raw_query("SELECT * FROM profession")
        self.get_profession = lambda id: self.raw_query("SELECT * FROM profession WHERE id=%d" % id)
        self.rm_profession = lambda id: self.write_query("DELETE FROM profession WHERE id=%d" % id)

        self.add_group = lambda prof, course: self.write_query(
            "INSERT INTO university.group SET profession='%d', course='%d'" % (int(prof), int(course)))
        self.get_groups = lambda: self.raw_query("SELECT * FROM university.group JOIN profession pr ON profession=pr.id")
        self.rm_group = lambda id: self.write_query("DELETE FROM university.group WHERE id=%d)" % int(id))
        self.get_group = lambda id: self.raw_query("SELECT * FROM university.group JOIN profession pr ON profession=pr.id WHERE university.group.id=%d" % id)
        self.get_groups_of_pr = lambda prid: self.raw_query("SELECT * FROM university.group JOIN profession pr ON profession=pr.id='%d'" % int(prid))
        self.get_exam_grade = lambda grid, sbid: self.raw_query("SELECT * FROM user u JOIN exam e ON u.id=e.student WHERE u.group='%d' AND e.subject='%d'" % (grid, sbid))

        self.get_student = lambda id: self.raw_query("SELECT * FROM user JOIN university.group gr, profession pr WHERE user.group=gr.id AND gr.profession=pr.id AND user.id = %d" % id)
        self.get_students = lambda: self.raw_query("SELECT * FROM user JOIN university.group gr, profession pr WHERE user.group=gr.id AND gr.profession=pr.id AND user.role=1")
        self.add_student = lambda userid, groupid: self.write_query(
            "UPDATE user SET role=1, user.group=(SELECT id FROM university.group WHERE id = '%d') WHERE id=%d" % (int(groupid), int(userid)))
        self.get_students_of_group = lambda grid: self.raw_query("SELECT * FROM user WHERE user.group = %d" % grid)
        self.remove_student = lambda stid: self.write_query("UPDATE user SET role=0, user.group=0 WHERE id=%d" % int(stid))
        self.edit_driver = lambda driverid, name, carid: self.write_query(
            "UPDATE user SET fio = '%s', car = %d WHERE iduser = %d" % (name, carid, driverid))
        self.get_student_exams = lambda stid: self.raw_query("SELECT * FROM exam JOIN subject s ON exam.subject=s.id AND student = %d" % stid)

        self.get_subjects = lambda: self.raw_query("SELECT * FROM subject JOIN profession pr ON subject.profession=pr.id")
        self.add_subject = lambda name, prid, course: self.write_query("INSERT INTO subject SET name='%s', profession='%d', course='%d'" % (name, int(prid), int(course)))
        self.rm_subject = lambda gasid: self.write_query("DELETE FROM gas WHERE idgas='%d'" % gasid)
        self.get_subject = lambda prid: self.raw_query("SELECT * FROM subject WHERE id='%d'" % prid)

        self.get_exams = lambda: self.raw_query("SELECT * FROM exam JOIN user u, subject s WHERE exam.student=u.id AND exam.subject=s.id")
        self.get_station = lambda stationid: self.raw_query("SELECT * FROM station WHERE idstation=%d" % stationid)
        self.add_exam = lambda date, stid, sbid, grade: self.write_query("INSERT INTO exam SET date='%s', student='%d', subject='%d', grade='%d'" % (date, int(stid), int(sbid), int(grade)))
        self.rm_station = lambda stationid: self.write_query("DELETE FROM station WHERE idstation='%d'" % stationid)

        self.add_tr = lambda datetime, driverid, gasid, stationid, amount: self.write_query(
            "INSERT INTO transportation SET date='%s', driver='%d', gas=%d, station=%d, gas_amount=%d" %
            (datetime, driverid, gasid, stationid, amount))
        self.get_trs = lambda: self.get_double_list_query(
            "SELECT * FROM transportation JOIN user, gas, station, var WHERE driver=iduser AND gas=idgas AND station=idstation AND status=idvar")
        self.get_tr = lambda trid: self.get_one_list_query("SELECT * FROM transportation JOIN user, gas, station, var WHERE idtransportation=%d AND driver=iduser AND gas=idgas AND station=idstation AND status=idvar" % trid)
        self.edit_tr_status = lambda trid, status: self.raw_query("UPDATE transportation SET status=%d WHERE idtransportation=%d" % (status, trid))

        self.get_vars = lambda: self.raw_query("SELECT * FROM var")

        self.get_professions_count = lambda: self.get_one_query("SELECT COUNT(1) FROM profession")
        self.get_groups_count = lambda: self.get_one_query("SELECT COUNT(1) FROM university.group")
        self.get_users_count = lambda: self.get_one_query("SELECT COUNT(1) FROM user")
        self.get_subjects_count = lambda: self.get_one_query("SELECT COUNT(1) FROM subject")
        self.get_exams_count = lambda: self.get_one_query("SELECT COUNT(1) FROM exam")

    def get_connect(self):
        try:
            c = connect(host=self.host, user=self.user, password=self.password)
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '%s'" % self.database)
            if 1 not in cur.fetchone():
                cur.execute('CREATE DATABASE %s' % self.database)
                cur.execute(open('university.sql').read(), multi=True)
                c.commit()
                c.close()
            return connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Error as e:
            print(e)

    def raw_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def write_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()

    def get_one_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]

    def get_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def remove_profession(self, prid):
        if prid:
            self.write_query("UPDATE university.group SET profession = NULL WHERE profession = %d" % prid)
            self.rm_profession(prid)

    def add_transportation(self, gasid, amount, datetime, driverid, stationid):
        q = self.get_one_query("SELECT remain FROM gas WHERE idgas=%d" % gasid)
        if q >= amount:
            self.add_tr(datetime, driverid, gasid, stationid, amount)
            self.change_gas_amount(gasid=gasid, amount=-amount)

    def register_user(self, username, fio, age, password):
        if not self.get_user(username):
            self.add_user(username, fio, age, password)
            return True
        else:
            return False


