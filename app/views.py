from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import session

from flask_nav import Nav
from flask_nav.elements import Navbar
from flask_nav.elements import View
from flask_nav.elements import Subgroup
from flask_nav.elements import Link

from flask_login import UserMixin
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_login import LoginManager

from app import app
from cap import *

login_manager = LoginManager()
login_manager.init_app(app)
nav = Nav()
nav.init_app(app)

apisession = connect.APISession()


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.errorhandler(401)
def page_not_found(e):
    feedback = 'Please authenticate first.'
    return render_template('login.html', feedback=feedback)


@nav.navigation()
def preauth():
    return Navbar('cpapi', View('Login', 'login'))


@nav.navigation()
def postauth():
    return Navbar('cpapi', View('Custom', 'custom'), View('Object', 'object'),
                           View('Policy', 'policy'), View('Logout', 'logout'))


@app.before_request
def before_request():
    keepalive_pages = ['custom', 'object', 'policy', 'showobject', 'logout']
    if request.endpoint in keepalive_pages:
        response = apisession.keepalive()
        if response.status_code != 200:
            feedback = 'Previous session expired.'
            return render_template('login.html', feedback=feedback)


@app.route('/')
def index():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        ipaddress = request.form.get('ipaddress')
        username = request.form.get('username')
        password = request.form.get('password')
        domain = request.form.get('domain', None)
        app.logger.info('Login attempt {}@{} > {}'.format(username,
                                                          request.remote_addr,
                                                          ipaddress))
        response = apisession.login(ipaddress, username, password, domain)
        try:
            if response.status_code != 200:
                try:
                    return render_template(
                        'login.html', feedback=response.json()['message'])
                except Exception as e:
                    app.logger.error('{} - {}'.format(type(e).__name__, e))
                    return render_template(
                        'login.html', feedback=response.text)
        # No connection happened so there is no status code
        except AttributeError as e:
            return render_template('login.html', feedback=response)

        app.logger.info('Login Success {}@{} > {}'.format(username,
                                                          request.remote_addr,
                                                          ipaddress))
        apisession.sid = response.json()['sid']
        apisession.ipaddress = ipaddress
        user = User(apisession.sid)
        login_user(user)
        return redirect('/custom')


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    if request.method == 'GET':
        apisession.logout()
        logout_user()
        return redirect('/login')


@app.route('/custom', methods=['GET', 'POST'])
@login_required
def custom():
    if request.method == 'GET':
        all_commands = misc.getallcommands(apisession)
        return render_template('custom.html', allcommands=all_commands)
    if request.method == 'POST':
        all_commands = misc.getallcommands(apisession)
        command = request.form.get('command')
        payload = request.form.get('payload')
        response = misc.customcommand(apisession, command, payload)
        if command != 'logout':
            try:
                if response.status_code == 403 or response.status_code == 404:
                    return (render_template(
                        'custom.html',
                        allcommands=all_commands,
                        lastcomm=command,
                        payload=payload,
                        response=str(response)))
                else:
                    return (render_template(
                        'custom.html',
                        allcommands=all_commands,
                        lastcomm=command,
                        payload=payload,
                        response=response.text))
            except Exception as e:
                response = 'Incorrect payload format.'
                return (render_template(
                    'custom.html',
                    allcommands=all_commands,
                    lastcomm=command,
                    payload=payload,
                    response=response))
        else:
            return redirect('/login')


@app.route('/object', methods=['GET', 'POST'])
@login_required
def object():
    if request.method == 'GET':
        return render_template('object.html')
    if request.method == 'POST':
        if 'hostname' in request.form.keys():
            hostname = request.form.get('hostname')
            hostipaddress = request.form.get('ipaddress')
            section = 'hostform'
            response = objects.add_host(apisession, hostname, hostipaddress)
        if 'netname' in request.form.keys():
            netname = request.form.get('netname')
            network = request.form.get('network')
            netmask = request.form.get('netmask')
            section = 'netform'
            response = objects.add_network(apisession, netname, network,
                                           netmask)
        if 'groupname' in request.form.keys():
            groupname = request.form.get('groupname')
            section = 'groupform'
            response = objects.add_group(apisession, groupname)
        if response.status_code == 200:
            apisession.publish()
        print(section)
        return render_template(
            'object.html',
            response=response.text,
            section=section)


@app.route('/policy', methods=['GET', 'POST'])
@login_required
def policy():
    if request.method == 'GET':
        all_layers = rules.get_all_layers(apisession)
        return render_template('policy.html', alllayers=all_layers)
    if request.method == 'POST':
        all_layers = rules.get_all_layers(apisession)
        layer = request.form.get('layer')
        response = rules.showrulebase(apisession, layer)
        return render_template(
            'policy.html',
            alllayers=all_layers,
            rulebase=response,
            lastlayer=layer)


@app.route('/showobject/<cp_objectuid>', methods=['GET'])
@login_required
def showobject(cp_objectuid):
    response = objects.show_object(apisession, cp_objectuid)
    return render_template('showobject.html', cpobject=response.json())
