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
        self.rm_group = lambda id: self.write_query("DELETE FROM university.group WHERE id=%d" % int(id))
        self.get_group = lambda id: self.raw_query("SELECT * FROM university.group JOIN profession pr ON profession=pr.id WHERE university.group.id=%d" % id)
        self.get_groups_of_pr = lambda prid: self.raw_query("SELECT * FROM university.group JOIN profession pr ON profession=pr.id='%d'" % int(prid))
        self.get_exam_grade = lambda grid, sbid: self.raw_query("SELECT * FROM user u JOIN exam e ON u.id=e.student WHERE u.group='%d' AND e.subject='%d'" % (grid, sbid))

        self.get_student = lambda id: self.raw_query("SELECT * FROM user JOIN university.group gr, profession pr WHERE user.group=gr.id AND gr.profession=pr.id AND user.id = %d" % id)
        self.get_students = lambda: self.raw_query("SELECT * FROM user JOIN university.group gr, profession pr WHERE user.group=gr.id AND gr.profession=pr.id AND user.role=1")
        self.get_students_of_group = lambda grid: self.raw_query("SELECT * FROM user WHERE user.group = %d" % grid)
        self.remove_student = lambda stid: self.write_query("UPDATE user SET role=0, user.group=0 WHERE id=%d" % int(stid))
        self.get_student_exams = lambda stid: self.raw_query("SELECT * FROM exam JOIN subject s ON exam.subject=s.id AND student = %d" % stid)
        self.get_student_marks = lambda stid: self.get_list_query("SELECT grade FROM exam WHERE student='%d'" % stid)
        self.get_average = lambda student: self.get_query("SELECT * FROM average WHERE student='%d'" % student)
        self.get_students_rating = lambda: self.raw_query("SELECT * FROM user JOIN average a ON user.id=a.student WHERE role=1 ORDER BY a.score DESC")
        self.get_3_students = lambda: self.raw_query("SELECT * FROM user WHERE id=(SELECT student FROM exam WHERE exam.grade=3)")
        self.get_5_students = lambda: self.raw_query("SELECT * FROM user WHERE id=(SELECT student FROM average WHERE score=5)")
        self.get_4_students = lambda: self.raw_query("SELECT * FROM user WHERE user.id IN (SELECT exam.student FROM exam WHERE exam.grade = 4) and user.id NOT IN (SELECT exam.student FROM exam WHERE exam.grade = 3)")
        self.rm_student = lambda id: self.write_query("DELETE FROM user WHERE id='%d'" % id)
        self.rm_group_students = lambda id: self.write_query("UPDATE user SET user.group=0, user.role=0 WHERE id='%d'" % id)

        self.get_subjects = lambda: self.raw_query("SELECT * FROM subject JOIN profession pr ON subject.profession=pr.id")
        self.add_subject = lambda name, prid, course: self.write_query("INSERT INTO subject SET name='%s', profession='%d', course='%d'" % (name, int(prid), int(course)))
        self.rm_subject = lambda id: self.write_query("DELETE FROM subject WHERE id='%d'" % id)
        self.get_subject = lambda prid: self.raw_query("SELECT * FROM subject WHERE id='%d'" % prid)
        self.get_subject_exam = lambda sbid: self.raw_query("SELECT * FROM exam JOIN user u, subject s WHERE student=u.id AND exam.subject=s.id AND subject='%d'" % sbid)
        self.get_subjects_of_profession = lambda prid: self.raw_query("SELECT * FROM subject JOIN profession pr ON subject.profession=pr.id WHERE subject.profession='%d'" % prid)

        self.get_exams = lambda: self.raw_query("SELECT * FROM exam JOIN user u, subject s WHERE exam.student=u.id AND exam.subject=s.id")
        self.rm_exam = lambda id: self.write_query("DELETE * FROM exam WHERE id='%d'" % id)
        self.rm_student_exams = lambda id: self.write_query("DELETE FROM exam WHERE student='%d'" % id)

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
            self.cursor.clear_attributes()
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

    def get_list_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return [list[0] for list in self.cursor.fetchall()]

    def register_user(self, username, fio, age, password):
        if not self.get_user(username):
            self.add_user(username, fio, age, password)
            return True
        else:
            return False

    def add_student(self, userid, groupid):
        self.write_query("UPDATE user SET role=1, user.group=(SELECT id FROM university.group WHERE id = '%d') WHERE id=%d" % (int(groupid), int(userid)))
        self.write_query("INSERT INTO average SET student='%d'" % userid)

    def recalc_average(self, student):
        a_list = self.get_student_marks(student)
        a = sum(a_list)/len(a_list)
        self.write_query("UPDATE average SET score='%f' WHERE student='%s'" % (a, student))

    def add_exam(self, date, stid, sbid, grade):
        self.write_query("INSERT INTO exam SET date='%s', student='%d', subject='%d', grade='%d'" % (date, int(stid), int(sbid), int(grade)))
        self.recalc_average(stid)

    def get_student_report(self, cat):
        if cat == 0:
            return self.get_3_students()
        elif cat == 1:
            return self.get_4_students()
        else:
            return self.get_5_students()

    def remove_student(self, id):
        self.rm_student_exams(id)
        self.rm_student(id)

    def remove_subject(self, id):
        self.rm_subject_exams(id)
        self.rm_subject(id)

    def remove_group(self, id):
        self.rm_group_students(id)
        self.rm_group(id)