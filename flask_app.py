import os
import click
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import random
from API.mpdforWebapp import player
import numpy as np
from copy import deepcopy

app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , flaskr.py

DATABASE = './database.db'

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
))
app.config['SECRET_KEY'] = 'you never guess'

# def get_db():
# 	db = getattr(g, '_database', None)
# 	if db is None:
# 		db = g._database = sqlite3.connect(DATABASE)
# 	return db

def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db


def connect_db():
	"""Connects to the specific database."""
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv
def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

@app.cli.command('initdb')
def initdb():
	"""Initialize the database."""
	init_db()
	click.echo('Init the db')

@app.teardown_appcontext
def close_db(error):
	"""Closes the database again at the end of the request."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

#database
users={}
# room = 0	# room number
# number = 0	# the random number to generate room number
# score = 0	# the total score of me
# operation = None  # the operation of me
# AI_player=None  # the class of AI
# AI_type = None  # the type of AI
# rm_mate = 0  # the number of people in the room 
# rd_arr = [] # list of the of people,rd_arr[0] is me
# oppo_score = []  # the score of all opponents
# top5=[]
@app.route('/')
def index():
	# init_db()
	return render_template('index.html')

@app.route('/a.html')
def a():
	global users

	# db=get_db()
	# global number
	# global room
	# global score
	# global AI_player
	# global rd_arr
	# global oppo_score
	# global rm_mate
	# global top5
	AI_player = player()
	score = 0
	number = random.randint(0,10000)
	room = number%47
	rm_mate = random.randint(10,20)  # the number of people in the room 
	rd_arr = list((np.random.permutation(rm_mate)+1)) # list of the of people,rd_arr[0] is me
	# print len(rd_arr)
	# print rd_arr
	oppo_score = list(np.zeros(rm_mate+1))  # the score of all opponents
	# print len(oppo_score)
	# print oppo_score
	top5=[]
	users[number]=[room,AI_player,rm_mate,rd_arr,oppo_score,score,-1,0] # room, opponent type, how many roommate, the array of idx of all, opponent scoreboard, oppo idx, if no.1
	session['logged_in']=number
	# print "session", number
	# db.execute('insert into scores (room_num,name1,oper1,delta1,tot1,name2,oper2,delta2,tot2) values (?,?,?,?,?,?,?,?,?)',[c,0,0,0,0,0,0,0,0])
	# db.commit()
	return render_template("a.html",number=rd_arr[0],room=room)

@app.route('/b.html')
def wait():
    return render_template("./b.html")



@app.route('/c.html',methods=['POST','GET'])

def complex():
	# global rd_arr
	# global rm_mate
	# global score
	# global number
	# global AI_player
	# global AI_type
	# global oppo_score
	global users
	number = session['logged_in']
	need_list = users[number]	# [room,AI_player,rm_mate,rd_arr,oppo_score]
	room = need_list[0]
	AI_player = need_list[1]
	rm_mate = need_list[2]  # No. of people in one room
	rd_arr = need_list[3]
	oppo_score = need_list[4]  # need update
	score = need_list[5]  # need update
	check = need_list[7]  # if the usr is No1, always betray, origin 0
	flag = 0
	# render_template('c.html',score=score,operation=operation,oppo=oppo, me = rd_arr[0],top=top5,flag=flag)

	# print "number", number
	top5=[(0,0),(0,0),(0,0),(0,0),(0,0)]
	# idx = random.randint(1,rm_mate-1)
	# oppo = rd_arr[idx]		# my opponent's ID, and my ID is rd_arr[0]
	db=get_db()
	AI_type = AI_player._type
	operation= -1		# opponent operation
	if request.method=='POST':
		idx = need_list[6]
		oppo = rd_arr[idx]
		score_add = 0
		if request.form['bo']=='coop':
			player_action=0		# my operation, 0 is cooperate
			(action, delta_AI, score_add) = AI_player.playwith(player_action,check)	# ai action, ai delta, my score delta
		if request.form['bo']=='betr':
			player_action = 1  # my operation, 1 is betray
			(action, delta_AI, score_add) = AI_player.playwith(player_action,check)
		oppo_score[oppo] += delta_AI
		score += score_add
		operation=action  # opponent operation
	# 	# print operation
		list_scr=[-1,0,2,3]
		for i in range(len(rd_arr)):
			if (i != 0) and (i != idx):
				man = rd_arr[i]

				his_score = random.randint(0,3)
				oppo_score[man] += list_scr[his_score]
		
		
		dic = {rd_arr[0]:score}
		for i in range(len(rd_arr)):
			if i != 0:
				man = rd_arr[i]
				dic[man]=oppo_score[man]
		top5 = sorted(dic.items(),key = lambda x:x[1],reverse = True)[:5]
		users[number][4] = oppo_score
		users[number][5] = score

		
		if (rd_arr[0] ==top5[0][0]) and (int(top5[0][0] != int(top5[1][0]))):
			flag = 1 
			users[number][7] = 1
		else:
			users[number][7] = 0
		db.execute('insert into scores (idx,oppo_type,room_num,name1,oper1,delta1,tot1,name2,oper2,delta2,tot2,ifNo1) values (?,?,?,?,?,?,?,?,?,?,?,?)',[number,AI_type,room,rd_arr[0],player_action,score_add,score,oppo,operation,delta_AI,oppo_score[oppo],check])
		db.commit()
		db.execute('insert into scores (idx,oppo_type,room_num,name1,oper1,delta1,tot1,name2,oper2,delta2,tot2,ifNo1) values (?,?,?,?,?,?,?,?,?,?,?,?)',[number,AI_type,room,oppo,operation,delta_AI,oppo_score[oppo],rd_arr[0],player_action,score_add,score,check])
		db.commit()
		idx = random.randint(1,rm_mate-1)
		users[number][6] = idx
		oppo = rd_arr[idx]
		return render_template('c.html',score=score,operation=operation,oppo=oppo, me = rd_arr[0],top=top5,flag=flag)
		# print "op",operation
		# print 
		# render_template('c.html',score=score,operation=operation,oppo=oppo,top=top5)
	# db.execute('insert into scores (idx,room_num,name1,oper1,delta1,tot1,name2,oper2,delta2,tot2) values (?,?,?,?,?,?,?,?,?,?)',[number,0,0,0,0,0,0,0,0,0])
	# db.commit()
	# return render_template('c.html')

	if request.method=='GET':
		idx = random.randint(1,rm_mate-1)
		users[number][6] = idx
		oppo = rd_arr[idx]
		return render_template('c.html',score=score,operation=operation,oppo=oppo, me = rd_arr[0],top=top5,flag=flag)
	# 	# print "get"
	# 	pass
	return render_template('c.html',score=score,operation=operation,oppo=oppo, me = rd_arr[0],top=top5,flag=flag)

if __name__ == '__main__':
	app.debug = True
	app.run()