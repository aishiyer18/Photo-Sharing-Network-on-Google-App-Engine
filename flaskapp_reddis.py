from flask import Flask, request, render_template, session, redirect, url_for, make_response
import MySQLdb, hashlib, os, redis

app = Flask(__name__)
app.secret_key = "1|D0N'T|W4NT|TH15|T0|3E|R4ND0M"

@app.route('/', methods=['POST','GET'])
def register():
	if 'username' in session:
		return render_template('index.html', username = session['username'])
		
	if request.method == 'POST':
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		username = request.form['username']
		password = request.form['password']
		if(username == '' or password == ''):
			return render_template('register.html')
			
		sql = "select username from users where username='"+username+"'"
		cursor.execute(sql)
		if cursor.rowcount == 1:
			return render_template('register.html')
		
		sql = "insert into users (username, password) values ('"+username+"','"+hashlib.md5(password).hexdigest()+"')"
		cursor.execute(sql)
		db.commit()
		cursor.close()
		return render_template('login.html')
	else:
		return render_template('register.html')

		
@app.route('/login', methods=['POST','GET'])
def login():
	if 'username' in session:
		return render_template('index.html', username = session['username'])
		
	if request.method == 'POST':
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		username = request.form['username']
		password = request.form['password']
		
		sql = "select username from users where username = '"+username+"' and password = '"+hashlib.md5(password).hexdigest()+"'"
		cursor.execute(sql)
		if cursor.rowcount == 1:
			results = cursor.fetchall()
			for row in results:
				session['username'] = username
				return render_template('index.html', username = session['username'])
		else:
			return render_template('login.html')
	else:
		return render_template('login.html')


@app.route('/logout', methods=['POST','GET'])
def logout():
	if 'username' in session:
		session.pop('username', None)
	return redirect(url_for('register'))

	
@app.route('/upload', methods=['POST','GET'])
def upload():
	if request.method == 'POST':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		
		file = request.files['file']
		file_contents = file.read()
		hash = hashlib.md5(file_contents).hexdigest()
		
		sql = "select name from images where username = '"+session['username']+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		if cursor.rowcount > 0:
			return render_template('index.html', username = session['username'])
		
		sql = "insert into images (username, hash, name) values ('"+session['username']+"','"+hash+"','"+file.filename+"')"
		cursor.execute(sql)
		db.commit()
		cursor.close()
		
		key = session['username']+"_"+hash
		r.set(key,file_contents)
		
		return redirect(url_for('list'))
	else:
		return render_template('index.html', username = session['username'])


@app.route('/list', methods=['POST','GET'])
def list():
	if 'username' not in session:
		return render_template('register.html')

	if request.method == 'GET':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()

		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		
		sql = "select hash, name from images where username = '"+session['username']+"'"
		cursor.execute(sql)
		results = cursor.fetchall()
		list = '<br><center><a href="login">Back</a></center><br>'
		list += '<table border="1"><col width="200"><col width="325"><col width="200"><col width="250"><th>Name</th><th>Image</th><th>Owner</th><th>Options</th>'
		for row in results:
			hash = row[0]
			name = row[1]
			key = session['username']+"_"+hash
			image = r.get(key)
			image = image.encode("base64")
			list += "<tr><td>"+name+"</td>"
			list += "<td><center><img src='data:image/jpeg;base64,"+image+"' height='75%' width='75%'/></center></td>"
			list += "<td><center>"+session['username']+"</center></td>"
			list += "<td><a href='view?id="+hash+"&u="+session['username']+"'>View</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			list += "<a href='delete?id="+hash+"&u="+session['username']+"'>Delete</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			list += "<a href='download?id="+hash+"&u="+session['username']+"'>Download</a></td></tr>"
		list += '</table>'
		cursor.close()
		return '''<html><head><title>Instagram</title><link rel="stylesheet" href="static/stylesheets/style.css"></head><body>'''+list+'''</body></html>'''
	else:
		return render_template('index.html', username = session['username'])
		
		
@app.route('/list_all', methods=['POST','GET'])
def list_all():
	if 'username' not in session:
		return render_template('register.html')
		
	if request.method == 'GET':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()

		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		
		sql = "select hash, name, username from images"
		cursor.execute(sql)
		results = cursor.fetchall()
		list = '<br><center><a href="login">Back</a></center><br>'
		list += '<table border="1"><col width="200"><col width="325"><col width="200"><col width="250"><th>Name</th><th>Image</th><th>Owner</th><th>Options</th>'
		for row in results:
			hash = row[0]
			name = row[1]
			username = row[2]
			key = username+"_"+hash
			image = r.get(key)
			image = image.encode("base64")
			list += "<tr><td>"+name+"</td>"
			list += "<td><center><img src='data:image/jpeg;base64,"+image+"' height='75%' width='75%'/></center></td>"
			list += "<td><center>"+username+"</center></td>"
			list += "<td><a href='view?id="+hash+"&u="+username+"'>View</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			if username == session['username']:
				list += "<a href='delete?id="+hash+"&u="+username+"'>Delete</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			list += "<a href='download?id="+hash+"&u="+username+"'>Download</a></td></tr>"
		list += '</table>'
		cursor.close()
		return '''<html><head><title>Instagram</title><link rel="stylesheet" href="static/stylesheets/style.css"></head><body>'''+list+'''</body></html>'''
	else:
		return render_template('index.html', username = session['username'])
		

@app.route('/view', methods=['GET'])
def view():
	if request.method == 'GET':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		
		hash = request.args.get('id')
		username = request.args.get('u')
		
		sql = "select hash, name from images where username = '"+username+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		results = cursor.fetchall()
		
		view = '<br><center><a href="list">Back</a></center><br>'
		view += '<table border="1"><col width="200"><col width="325"><th>Name</th><th>Image</th>'
		for row in results:
			hash = row[0]
			name = row[1]
			key = username+"_"+hash
			image = r.get(key)
			image = image.encode("base64")
			view += "<tr><td>"+name+"</td>"
			view += "<td><center><img src='data:image/jpeg;base64,"+image+"' height='75%' width='75%'/></center></td></tr>"
		view += '</table><br><hr><br>'
		
		view += "<div><form action='comment' method='post'><center>Comment on the image<br><br><textarea name='comment' rows='3' cols='50'></textarea><br><br><input type='hidden' name='username' value= '"+username+"'><input type='hidden' name='hash' value= '"+hash+"'><input type='submit' value='Comment'></center></form></div>"
		
		sql = "select username, comment from comments where owner = '"+username+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		results = cursor.fetchall()
		
		view += '<table border="1"><col width="100"><col width="500"><th>Username</th><th>Comment</th>'
		for row in results:
			username = row[0]
			comment = row[1]
			
			view += "<tr><td>"+username+"</td>"
			view += "<td>"+comment+"</td></tr>"
		
		view += '</table><br><hr><br>'
		cursor.close()
		return '''<html><head><title>Instagram</title><link rel="stylesheet" href="static/stylesheets/style.css"></head><body>'''+view+'''</body></html>'''
	else:
		return render_template('index.html', username = session['username'])


@app.route('/comment', methods=['POST','GET'])
def comment():
	if request.method == 'POST':
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		owner = request.form['username']
		hash = request.form['hash']
		username = session['username']
		comment = request.form['comment']
		
		sql = "insert into comments (username, hash, owner, comment) values ('"+username+"','"+hash+"','"+owner+"','"+comment+"')"
		cursor.execute(sql)
		db.commit()
		cursor.close()
		return redirect(url_for('view', id = hash, u = owner))
		
@app.route('/download', methods=['GET'])
def download():
	if request.method == 'GET':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		
		hash = request.args.get('id')
		username = request.args.get('u')
		
		sql = "select name from images where username = '"+username+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		results = cursor.fetchall()
		for row in results:
			name = row[0]
			key = username+"_"+hash
			file_contents = r.get(key)
			
		response = make_response(file_contents)
		response.headers["Content-Disposition"] = "attachment; filename="+name
		
		cursor.close()
		return response
	else:
		return render_template('index.html', username = session['username'])
		
		
@app.route('/delete', methods=['GET'])
def delete():
	if request.method == 'GET':			
		db = MySQLdb.connect("localhost","root","root","instagram")
		cursor = db.cursor()
		
		hash = request.args.get('id')
		username = request.args.get('u')
		
		sql = "delete from images where username = '"+username+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		db.commit()
		
		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		key = username+"_"+hash
		r.delete(key)
		
		sql = "delete from comments where owner = '"+username+"' and hash = '"+hash+"'"
		cursor.execute(sql)
		db.commit()
		
		cursor.close()
		return redirect(url_for('list'))
		
if __name__ == '__main__':
	app.run(debug=True)