from flask import (
    Flask, 
    render_template, 
    request, 
    session, 
    redirect,
    jsonify,
)
from flask_mobility import Mobility # detect mobile browsers
from flask_cors import CORS
from markdown2 import markdown # quicker and more accurate than markdown
import os, json, uuid, re

# db code
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import cryptobaker as cb
import os, json, base64

def from_env(name):
    enc = os.getenv(name)
    if enc:
        dec = base64.b64decode(enc).decode()
        conf = json.loads(dec)
        return credentials.Certificate(conf)

class DB(object):
    def __init__(self, creds):
        self.app = firebase_admin.initialize_app(creds)
        self.firestore = firestore.client(self.app)
        self.users = self.firestore.collection('users')
        self.links = self.firestore.collection('links')
        self.counters = self.firestore.collection('counters')
    
    def get_user(self, id):
        u = self.users.document(id)
        if u.get().exists:
            return u
    
    def hash(self, password: str):
        a = (cb.Dish(password) + 'lamee').apply(cb.toMD5)
        b = a.apply(cb.encode).apply(cb.toAscii85)
        return b.apply(cb.toSHA384).raw
    
    def date(self):
        return datetime.now()
    
    def get_links(self, user_id):
        return self.links.where('user', '==', user_id)
# /end db code

app = Flask(__name__)
CORS(app)
Mobility(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = DB(from_env('CONF'))

LINKS = '''
<link rel='stylesheet' href='/static/styles.css'>
<link rel='stylesheet' href='/static/code.css'>

<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.0/milligram.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
<script src='/static/notify.min.js'></script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src='/static/request.js'></script>
<script defer src='https://analytics.marcusj.org/analytics.js'></script>
'''

MARKDOWN_EXTRAS = [
    'spoiler',
    'strike',
    'task_list',
    'fenced-code-blocks',
    'header-ids',
    'markdown-in-html',
    'target-blank-links',
    'tables',
    'footnotes',
]

def embed_script(js):
    uid = str(uuid.uuid4())
    sp = '<span id="%s"></span>' % uid
    js = '<script>document.getElementById("%s").innerHTML = eval("%s")</script>' % (uid, js)
    return sp + js

def make_counterbutton(txt=''):
    uid = str(uuid.uuid4())
    doc = db.counters.document(uid)
    doc.set({'clicks': 0})
    btn = '''<button onclick="doPOST('/click', {'id':'%s'}, function(res) { document.getElementById('%s').innerText = res['count'] } )"><span id='%s'>x</span> %s</button>''' % (
        uid, uid, uid, txt
    )
    return btn

expressions = {
    'date': lambda: str(db.date()).split(' ')[0],
    'time': lambda: str(db.date()).split(' ')[1],
    'js': embed_script,
    'counter': make_counterbutton,
    'gist': lambda g: '<script src="https://gist.github.com/{}.js"></script>'.format(g),
    'repl': lambda r: '<iframe height="400px" width="100%" src="https://replit.com/{}?lite=true" scrolling="no" frameborder="no" allowtransparency="true" allowfullscreen="true" sandbox="allow-forms allow-pointer-lock allow-popups allow-same-origin allow-scripts allow-modals"></iframe>'.format(r)
}

def parse_note(body):
    exps = re.findall('\{\{ (.*?) \}\}', body) # {{ anything }}
    for e in exps:
        try:
            if '|' in e:
                fn, arg = e.split('|')
                if fn in expressions:
                    body = body.replace('{{ ' + e + ' }}', expressions[fn](arg))
            if e in expressions:
                body = body.replace('{{ ' + e + ' }}', expressions[e]())
        except Exception as err:
            print('error parsing:',e,'-',err)
    return body

def notes_to_dict(notes):
    res = {}
    for note in notes:
#        lnks = db.links.where('path', '==', note.reference).get()
#        if len(lnks) > 0:
#            links = [ln.id for ln in lnks][0]
#        else:
#            links = False
        res[note.id] = {
            'body': note.get('body'),
            'date': str(note.get('date')),
#            'link': links,
        }
    return res

def escape(text):
    for sym, rep in {
        '`': '|bt|',
        '<': '|lt|',
        '>': '|gt|',
    }.items():
        text = text.replace(sym, rep)
    return text
def unescape(text):
    for sym, rep in {v:k for k,v in {
        '`': '|bt|',
        '<': '|lt|',
        '>': '|gt|',
    }.items()}.items():
        text = text.replace(sym, rep)
    return text

@app.before_request
def app_check_loggedin():
    if any(map(request.path.endswith, ['/login', '/signup'])):
        if session.get('user'):
            return redirect('/notes')
    if any(map(request.path.endswith, ['/notes', '/delete/account', '/links', '/logout'])):
        if not session.get('user'):
            return redirect('/login')

@app.route('/')
def app_index():
    return render_template('index.html')

@app.route('/features')
def app_features():
    return redirect('/link/demo#changelog-and-features')

@app.route('/signup', methods=['GET', 'POST'])
def app_signup():
    if request.method == 'GET':
        return render_template('signup.html', reason=None)
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('signup.html', reason='missing_field')

        if db.get_user(username):
            return render_template('signup.html', reason='username_exists')

        user = db.users.document(username)
        user.set({'password':db.hash(password)})
        session['user'] = user.id
        return redirect('/notes')

@app.route('/login', methods=['GET', 'POST'])
def app_login():
    if request.method == 'GET':
        return render_template('login.html', reason=None)
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', reason='missing_field')
        
        user = db.get_user(username)
        if not user:
            return render_template('login.html', reason='no_user')
        
        if not db.hash(password) == user.get().get('password'):
            return render_template('login.html', reason='bad_pass')
        
        session['user'] = user.id
        return redirect('/notes')

@app.route('/replauth')
def app_replauth():
    if session.get('user'):
        return render_template('error.html', msg='You are already signed in', redir='/logout')
    user_name = request.headers.get('X-Replit-User-Name')
    user = db.users.document(user_name)
    if user.get().exists:
        if user.get().get('password') == 'replauth':
            session['user'] = user_name
            return redirect('/notes')
        return render_template('error.html', msg='Sorry, but your username is already taken. Please create an account', redir='/signup')
    user.set({
        'password': 'replauth'
    })
    session['user'] = user_name
    return redirect('/notes')

@app.route('/click', methods=['POST'])
def app_btn_click():
    id = request.json.get('id')
    doc = db.counters.document(id)
    data = doc.get()
    if data.exists:
        doc.set({'clicks': data.get('clicks') + 1})
    return jsonify({'count': data.get('clicks') + 1})

@app.route('/logout')
def app_logout():
    if session.get('user'):
        del session['user']
    return redirect('/')

@app.route('/delete/account', methods=['GET', 'POST'])
def app_delete_account():
    if request.method == 'GET':
        return render_template('delete.html')
    
    user = db.get_user(session.get('user'))
    password = request.form.get('password')
    if user.get().get('password') == db.hash(password):
        user.delete()
        return redirect('/logout')
    return redirect('/login')

@app.route('/delete/note', methods=['POST'])
def app_delete_note():
    user = db.get_user(session.get('user'))
    note = request.json.get('id')
    if not user: return redirect('/login')
    if not note: return 'none'
    doc = user.collection('notes').document(note)
    if not doc.get().exists: return 'gone'
    doc.delete()
    return 'ok'

@app.route('/notes', methods=['GET', 'POST'])
def app_notes():
    username = session.get('user')
    if not username:
        return redirect('/login')
    
    user = db.get_user(username)
    notes = user.collection('notes')

    if request.method == 'GET':
        notesd = notes_to_dict(notes.get())
        notesj = escape(json.dumps(notesd))
        if request.MOBILE:
            return render_template('mobile_notes.html', user=user, notesj=notesj)
        return render_template('notes.html', user=user, notes=notesd, notesj=notesj)
    elif request.method == 'POST':
        notesd = request.json
        ts = db.date()

        for note, body in notesd.items():
            while type(body) == dict:
                body = body['body']
            doc = notes.document(note);
            nd = {'body': parse_note(body), 'date': ts}
            doc.set(nd)
        return 'ok'

@app.route('/makelink', methods=['POST'])
def app_makelink():
    user = db.get_user(session.get('user'))
    if not user:
        return render_template('error.html', msg='You are not logged in. Please create an account or log in to yours', redir='/')
    noteid = request.json.get('id')
    render = request.json.get('render', False)
    note = user.collection('notes').document(noteid)
    if not note.get().exists:
        return render_template('error.html', msg='A note with that title does not exist. Make sure to save your notes before creating a link', redir='/notes')
    
    uid = request.json.get('link') or str(uuid.uuid4()).replace('-','')
    link = db.links.document(uid)
    if not link.get().exists:
        link.set({
            'path': note,
            'render': render,
            'user': user.id,
        })
        return jsonify({'url':f'/link/{uid}'})
    return jsonify({'url': '#', 'err':'exists'})

@app.route('/link/<uid>')
def app_link(uid):
    link = db.links.document(uid).get()
    if not link.exists:
        return '', 404
    note = link.get('path').get()
    if not note.exists:
        return render_template('error.html', msg='This note has been deleted', redir='/#')
    raw = note.get('body')
    render = request.args.get('render')
    if render in ['false', '0', 0, 'no', 'off']: render = False
    elif render in ['true', '1', 1, 'on', 'yes']: render = True
    else: render = link.get('render')
    if render:
        return LINKS + '<br>' + markdown(unescape(raw), extras=MARKDOWN_EXTRAS)
    else:
        return unescape(raw)

@app.route('/links')
def app_links():
    user = db.get_user(session.get('user'))
    if user:
        links_ = db.get_links(user.id).get()
        links = {lnk.id:lnk.get('path').id for lnk in links_}
        return render_template('links.html', links=links)
    else:
        return render_template('error.html', msg='You are not signed in', redir='/')

@app.route('/delete/link', methods=['POST'])
def app_delete_link():
    user = db.get_user(session.get('user'))
    if user:
        uid = request.json.get('link')
        link = db.links.document(uid)
        if link.get().exists:
            if link.get().get('user') == user.id:
                link.delete()
                return redirect('/links')
            else:
                return render_template('error.html', msg='That link does not belong to you', redir='/links')
        else:
            return render_template('error.html', msg='That link does not exist', redir='/links')
    return render_template('error.html', msg='You are not signed in', redir='/')

@app.route('/links/public', methods=['GET','POST'])
def app_links_public():
    if request.method == 'POST':
        user = db.get_user(session.get('user'))
        if user:
            uid = request.json.get('link')
            link = db.links.document(uid)
            if link.get().exists:
                link.set({'public': request.json.get('public', True)}, merge=True)
                return redirect('/links/public')
            return render_template('error.html', msg='Link does not exist', redir='/links')
        return render_template('error.html', msg='Not logged in', redir='/')
    elif request.method == 'GET':
        links_ = db.links.where('public', '==', True).get()
        links = {lnk.id:{'title':lnk.get('path').id,'user':lnk.get('user')} for lnk in links_}
        return render_template('public_links.html', links=links)

@app.route('/demo')
def app_demo():
    return render_template('demo.html')