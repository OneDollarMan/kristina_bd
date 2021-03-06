import hashlib

from flask import url_for, render_template, request, redirect, abort, send_from_directory, g, flash, session
from __init__ import app
import forms
from GarageRepo import *

gr = GarageRepo()


@app.route("/")
def index():
    return render_template('index.html', title="Главная",
                           counts=[gr.get_professions_count(), gr.get_groups_count(), gr.get_users_count(),
                                   gr.get_subjects_count(), gr.get_exams_count()])


@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = gr.login_user(form.login.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        if user:
            flash('Вы авторизовались!')
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[5]
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.RegForm()
    if form.validate_on_submit():
        if gr.register_user(form.username.data, form.fio.data, form.age.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest()):
            flash('Регистрация успешна!')
            return redirect(url_for('index'))
        else:
            flash('Логин уже занят!')
            return redirect(url_for('register'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/professions")
def professions():
    return render_template('professions.html', title="Специальности", prs=gr.get_professions())


@app.route("/professions/add", methods=['POST'])
def professions_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if request.form['name'] and request.form['abbr']:
            gr.add_profession(request.form['name'], request.form['abbr'])
    return redirect(url_for("professions"))


@app.route("/professions/<int:prid>")
def profession(prid):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('profession.html', title="Специальность", pr=gr.get_profession(prid)[0],
                               groups=gr.get_groups_of_pr(prid), sbs=gr.get_subjects_of_profession(prid))
    else:
        return redirect(url_for('professions'))


@app.route("/professions/rm/<int:prid>")
def professions_rm(prid):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if prid:
            gr.rm_profession(prid)
    return redirect(url_for("professions"))


@app.route("/groups")
def groups():
    return render_template('groups.html', title="Группы", groups=gr.get_groups(), prs=gr.get_professions())


@app.route("/groups/add", methods=['POST'])
def groups_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        c = int(request.form['course'])
        if request.form['prid'] and c > 0:
            gr.add_group(request.form['prid'], c)
    return redirect(url_for("groups"))


@app.route("/groups/<int:grid>")
def group(grid):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('group.html', title="Группа", group=gr.get_group(grid)[0],
                               students=gr.get_students_of_group(grid))
    else:
        return redirect(url_for('groups'))


@app.route("/groups/rm/<int:id>")
def groups_remove(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.remove_group(id)
    return redirect(url_for("groups"))


@app.route("/students")
def students():
    return render_template('students.html', title="Студенты", students=gr.get_students(), groups=gr.get_groups(),
                           users=gr.get_all_zero_users())


@app.route("/students/<int:stid>")
def student(stid):
    if session.get('role') == gr.ROLE_SUPERVISOR or session.get('id') == stid:
        return render_template('student.html', title="Студент", student=gr.get_student(stid)[0],
                               exams=gr.get_student_exams(stid), avg=gr.get_average(stid))
    else:
        return redirect(url_for('students'))


@app.route("/students/add", methods=['POST'])
def students_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if request.form['userid'] and request.form['groupid']:
            gr.add_student(int(request.form['userid']), int(request.form['groupid']))
    return redirect(url_for("students"))


@app.route("/students/rm/<int:stid>")
def students_remove(stid):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if stid:
            gr.remove_student(stid)
    return redirect(url_for("students"))


@app.route("/subjects")
def subjects():
    return render_template('subjects.html', title="Предметы", prs=gr.get_professions(), subjects=gr.get_subjects())


@app.route("/subjects/add", methods=['POST'])
def subjects_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        c = int(request.form['course'])
        if request.form['name'] and request.form['prid'] and c > 0:
            gr.add_subject(request.form['name'], request.form['prid'], c)
    return redirect(url_for("subjects"))


@app.route("/subjects/rm/<int:id>")
def subjects_rm(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.remove_subject(id)
    return redirect(url_for("subjects"))


@app.route("/exams")
def exams():
    return render_template('exams.html', title="Экзамены", exams=gr.get_exams(), sts=gr.get_students(),
                           sbs=gr.get_subjects(), prs=gr.get_professions())


@app.route("/exams/add", methods=['POST'])
def exams_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        g = int(request.form['grade'])
        if request.form['date'] and request.form['stid'] and request.form['sbid'] and g > 0:
            gr.add_exam(request.form['date'], int(request.form['stid']), int(request.form['sbid']), g)
    return redirect(url_for("exams"))


@app.route("/exams/rm/<int:id>")
def exams_remove(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.rm_exam(id)
    return redirect(url_for("exams"))


@app.route("/reports/group", methods=['GET', 'POST'])
def reports_group():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if request.method == 'POST':
            g = gr.get_group(int(request.form['grid']))[0]
            p = gr.get_subject(int(request.form['prid']))[0]
            return render_template('reports_group.html', title="%s-%s" % (g[5], g[2]), grid=g[2], prid=p[0], grs=gr.get_groups(), prs=gr.get_subjects(), students=gr.get_exam_grade(int(request.form['grid']), int(request.form['prid'])))
        return render_template('reports_group.html', title="Отчеты", grs=gr.get_groups(), prs=gr.get_subjects())
    else:
        return redirect(url_for("index"))


@app.route("/reports/student", methods=['GET', 'POST'])
def reports_student():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if request.method == 'POST':
            return render_template('reports_student.html', title="Отчеты", c=request.form['cat'], students=gr.get_student_report(int(request.form['cat'])))
        return render_template('reports_student.html', title="Отчеты")
    else:
        return redirect(url_for("index"))


@app.route("/reports/subject", methods=['GET', 'POST'])
def reports_subject():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if request.method == 'POST':
            sb = gr.get_subject(int(request.form['sbid']))[0]
            return render_template('reports_subject.html', title=sb[1], sbid=sb[0], sbs=gr.get_subjects(), students=gr.get_subject_exam(int(request.form['sbid'])))
        return render_template('reports_subject.html', title="Отчеты", sbs=gr.get_subjects())
    else:
        return redirect(url_for("index"))


@app.route("/reports/rating", methods=['GET'])
def reports_rating():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('reports_rating.html', title="Отчеты", students=gr.get_students_rating())
    else:
        return redirect(url_for("index"))


@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
@app.route('/style.css')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
