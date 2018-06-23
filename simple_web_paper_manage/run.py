# -*- coding: utf-8 -*-
import os
import ast
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from flask import Flask,render_template,request,url_for,send_file
app = Flask(__name__)



################数据库
# 检测数据库是否存在
def check_database():
	database_state = os.path.isfile(db_name)
	if database_state == False:
		return '0'
	elif database_state == True:
		return '1'

# 建立数据库；仅在检测不到数据库时执行。
def build_database(database_state):
	if database_state == '0':
		print ('数据库不存在，正在尝试创建数据库')
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		c.execute('''CREATE TABLE webdoc (doc_type TEXT,doc_id TEXT,doc_extension TEXT,doc_title TEXT,doc_author TEXT,doc_reference TEXT,doc_abstract TEXT,dir_parent TEXT,uploader TEXT,upload_time TEXT,title_translation TEXT,translate_time TEXT,translator TEXT,content_translation TEXT);''')
		conn.commit()
		conn.close()
		print ('创建成功')
		return '1'
	else:
		print ('数据库已载入')
		return '0'

def insert_database(tup):
	if tup:
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		c.execute("insert into webdoc values (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tup)
		conn.commit()
		conn.close()
		print ('插入成功')
		return '1'
	else:
		print ('插入失败')
		return '0'

def all_database():
	try:
		container = []
		conn = sqlite3.connect(db_name)
		cursor = conn.cursor()
		cuser = cursor.execute("SELECT doc_id,doc_title,dir_parent,uploader,upload_time FROM webdoc order by upload_time desc")

		for row in cuser:
			container.append(row)

		cursor.close()
		conn.commit()
		conn.close()
		return container
	except:
		return '0'


def all_databas_with_trans():
	try:
		container = []
		conn = sqlite3.connect(db_name)
		cursor = conn.cursor()
		cuser = cursor.execute("SELECT doc_type,doc_id,doc_title,dir_parent,title_translation,translate_time,translator,content_translation FROM webdoc order by doc_id desc")

		for row in cuser:
			container.append(row)

		cursor.close()
		conn.commit()
		conn.close()
		return container
	except:
		return '0'

def select_by_id_database(doc_id):
	try:
		doc_id = doc_id
		container = []
		conn = sqlite3.connect(db_name)
		cursor = conn.cursor()
		cuser = cursor.execute("SELECT * FROM webdoc where doc_id = '%s';"%(doc_id))

		for row in cuser:
			container.append(row)

		cursor.close()
		conn.commit()
		conn.close()
		return container
	except:
		return '0'

def select_column_database(column):
	try:
		column = column
		container = []
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		cuser = c.execute("SELECT %s FROM webdoc;"%(column))
		for row in cuser:
			container.append(row)
		conn.commit()
		conn.close()
		return container
	except:
		return '0'


def delete_from_database(doc_id):
	try:
		doc_id = doc_id
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		cuser = c.execute("DELETE from webdoc where doc_id = '%s';"%(doc_id))
		conn.commit()
		conn.close()
		return '1'
	except:
		return '0'

def search_from_database(column,word):
	try:
		column = column
		word = '%'+word+'%'
		execute_word = '''SELECT doc_id,doc_title,dir_parent,uploader,upload_time FROM webdoc WHERE %s like '%s' order by doc_id desc;''' % (column,word)
		container = []
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		cuser = c.execute(execute_word)
		for row in cuser:
			container.append(row)
		conn.commit()
		conn.close()
		return container
	except:
		return '0'


#####################################
# 格式化时间成2016-03-20 11:45:39形式
def now_time():
	now_time = time.strftime("%Y%m%d", time.localtime())
	return now_time


#把以*分割的非标准路径标准化
def get_beautiful_path(ugly_path):
	#格式化数据库位置
	seperate_ugly_path = ugly_path.split('*')
	beautiful_path = '.'
	for i in range (len (seperate_ugly_path) ):
		beautiful_path = os.path.join(beautiful_path,seperate_ugly_path[i])
	return beautiful_path

#tup = (doc_type,doc_id,doc_title,doc_author,doc_reference,doc_abstract,dir_parent,uploader,upload_time,title_translation,translate_time,translator,content_translation)

#####################################构建页面

@app.route('/',methods=['GET','POST'])
def index_page():
	if request.method == 'POST':
		word = request.form['word']
		column = 'doc_title'
		values = search_from_database(column,word)
		return render_template('index.html', values = values)

	else:
		if request.args.get('type',''):
			word = request.args.get('type','')
			column = 'dir_parent'
			values = search_from_database(column,word)
			return render_template('index.html', values = values)

		if request.args.get('uploader',''):
			word = request.args.get('uploader','')
			column = 'uploader'
			values = search_from_database(column,word)
			return render_template('index.html', values = values)

		if request.args.get('translator',''):
			word = request.args.get('translator','')
			column = 'translator'
			values = search_from_database(column,word)
			return render_template('index.html', values = values)

		values = all_database()
		return render_template('index.html', values = values)



@app.route('/surport',methods=['GET'])
def surport():
	return render_template('surport.html')

@app.route('/translate',methods=['GET'])
def translate():
	all_database = all_databas_with_trans()

	no_trans = []
	have_trans = []

	for i in range(len(all_database)):
		row = all_database[i]
		if row[0] == 'en_doc':
			if len(row[-1]) < 2:
				no_trans.append(row)
			else:
				have_trans.append(row)

	return render_template('translate.html',no_trans=no_trans,have_trans=have_trans)


@app.route('/change_translate/<doc_id>', methods=['GET'])
def change_translate(doc_id):

	values = select_by_id_database(doc_id)[0]

	doc_id = values[1]
	doc_title = values[3]

	content_translation = values[-1].replace('<br/>','\n')
	translator = values[-2]
	translate_time = values[-3]
	if translate_time == '':
		translate_time = now_time()
	title_translation = values[-4]
	tup = (doc_id,doc_title,title_translation,content_translation,translate_time,translator)

	return render_template('change_translate.html',doc_info=tup)


@app.route('/function_changetranslate', methods=['POST'])
def function_changetranslate():
	if request.method == 'POST':
		try:
			doc_id = request.form['doc_id']
			# 第一步，接收信息
			values = select_by_id_database(doc_id)[0]
			doc_type = values[0]
			doc_id = values[1]
			doc_extention = values[2]
			doc_title = values[3]
			doc_author = values[4]
			doc_reference = values[5]
			doc_abstract = values[6]
			dir_parent = values[7]
			uploader = values[8]
			upload_time = values[9]


			title_translation = request.form['title_translation']
			content_translation = request.form['content_translation'].replace('\n','<br/>').replace('\r','')
			translator = request.form['translator']
			translate_time = request.form['translate_time']
			
			tup = (doc_type,doc_id,doc_extention,doc_title,doc_author,doc_reference,doc_abstract,dir_parent,uploader,upload_time,title_translation,translate_time,translator,content_translation)

			#第二步，写入数据库
			delete_from_database(doc_id)
			insert_database(tup)
			
			return render_template('reflash.html',gotourl='/translate',note='翻译提交成功')
		except:
			return '修改失败，建议后退并重新提交'



@app.route('/manage',methods=['GET'])
def manage_page():
	values = all_database()
	return render_template('manage.html', values = values)


@app.route('/manage_delete/<doc_id>',methods=['GET'])
def manage_delete_page(doc_id):
	return render_template('auth.html', doc_id = doc_id,note='删除不可逆，谨慎操作',gotourl='/function_remove_doc')


@app.route('/function_remove_doc',methods=['POST'])
def function_remove_doc():
	if request.form['password'] == '123456':
		try:
			delete_from_database(request.form['doc_id'])
			file_save_name = request.form['doc_id'] + '.pdf'
			file_path = get_beautiful_path('static*docs') 
			file_save_path = os.path.join(file_path,file_save_name)
			os.remove(file_save_path) 
			return render_template('reflash.html',gotourl='/manage',note='删除成功')
		except:
			file_save_name = request.form['doc_id'] + '.pdf'
			file_path = get_beautiful_path('static*docs') 
			file_save_path = os.path.join(file_path,file_save_name)
			os.remove(file_save_path) 
			return render_template('reflash.html',gotourl='/manage',note='部分删除成功')
	else:
		return render_template('reflash.html',gotourl='/manage',note='密码错误')


@app.route('/manage_change/<doc_id>',methods=['GET'])
def manage_change_page(doc_id):
	values = select_by_id_database(doc_id)[0]

	doc_id = values[1]
	doc_extention = values[2]
	doc_title = values[3]
	doc_author = values[4]
	doc_reference = values[5]
	doc_abstract = values[6].replace('<br/>','\n')
	dir_parent = values[7]
	uploader = values[8]
	upload_time = values[9]
	doc_info = []
	doc_info.append(doc_id)
	doc_info.append(doc_extention)
	doc_info.append(doc_title)
	doc_info.append(doc_author)
	doc_info.append(doc_reference)
	doc_info.append(doc_abstract)
	doc_info.append(dir_parent)
	doc_info.append(uploader)
	doc_info.append(upload_time)

	global doc_upload_select_list
	#doc_upload_select_list = list(set(select_column_database('dir_parent')))
	return render_template('change.html',doc_info=doc_info,values=doc_upload_select_list)



@app.route('/function_change', methods=['POST'])
def function_change():
	if request.method == 'POST':
		try:

			# 第一步，接收信息
		
			doc_extention = request.form['doc_extention']
			doc_id =  request.form['doc_id']
			dir_parent = request.form['dir_parent']
			upload_time = request.form['upload_time']
			doc_title = request.form['doc_title']
			doc_author = request.form['doc_author']
			doc_reference = request.form['doc_reference']
			doc_abstract = request.form['doc_abstract'].replace('\n','<br/>').replace('\r','')
			doc_type = request.form['doc_type']
			uploader = request.form['uploader']

			title_translation = ''
			content_translation = ''
			translator = ''
			translate_time = ''
			if doc_type == 'en_doc':
				values = select_by_id_database(doc_id)[0]
				content_translation = values[-1]
				translator = values[-2]
				translate_time = values[-3]
				title_translation = values[-4]
			tup = (doc_type,doc_id,doc_extention,doc_title,doc_author,doc_reference,doc_abstract,dir_parent,uploader,upload_time,title_translation,translate_time,translator,content_translation)
			#第二步，写入数据库
			delete_from_database(doc_id)
			insert_database(tup)

			return render_template('reflash.html',gotourl='/',note='修改成功')
		except:
			return render_template('reflash.html',gotourl='/',note='修改失败，建议后退并重新提交')


@app.route('/upload',methods=['GET'])
def upload():
	global doc_upload_select_list
	#doc_upload_select_list = list(set(select_column_database('dir_parent')))
	return render_template('upload.html',values = doc_upload_select_list)


@app.route('/function_upload', methods=['POST'])
def function_upload():
	if request.method == 'POST':

		# 第一步，保存文件
		file = request.files['file']
		doc_extention = os.path.splitext(str(file.filename))[-1].split('.')[-1]

		time_stamp = str(time.time())
		file_save_name = time_stamp +'.'+ doc_extention
		file_path = get_beautiful_path('static*docs') 
		file_save_path = os.path.join(file_path,file_save_name)
		file.save(file_save_path)

		#第二步，写入数据库
		doc_id = time_stamp
		dir_parent = request.form['dir_parent']
		upload_time = now_time()
		doc_title = request.form['doc_title']
		doc_author = request.form['doc_author']
		doc_reference = request.form['doc_reference']
		doc_abstract = request.form['doc_abstract'].replace('\n','<br/>')
		doc_type = request.form['doc_type']
		uploader = request.form['uploader']
		title_translation = ''
		content_translation = ''
		translator = ''
		translate_time = ''
		tup = (doc_type,doc_id,doc_extention,doc_title,doc_author,doc_reference,doc_abstract,dir_parent,uploader,upload_time,title_translation,translate_time,translator,content_translation)
		insert_database(tup)
		return render_template('reflash.html',gotourl='/',note='上传成功')


@app.route('/detail/<doc_id>',methods=['GET'])
def function_download_file(doc_id):
	values = select_by_id_database(doc_id)[0]
	
	doc_id = values[1]
	doc_extention = values[2]
	doc_title = values[3]
	doc_author = values[4]
	doc_reference = values[5]
	doc_abstract = values[6].replace('\n','<br/>').replace('<br/><br/><br/>','')
	dir_parent = values[7]
	uploader = values[8]
	upload_time = values[9]
	doc_info = []
	doc_info.append(doc_id)
	doc_info.append(doc_extention)
	doc_info.append(doc_title)
	doc_info.append(doc_author)
	doc_info.append(doc_reference)
	doc_info.append(doc_abstract)
	doc_info.append(dir_parent)
	doc_info.append(uploader)
	doc_info.append(upload_time)

	content_translation = values[-1]
	translator = values[-2]
	translate_time = values[-3]
	trans = []
	trans.append(content_translation)
	trans.append(translator)
	trans.append(translate_time)
	if values[0] == 'zh_doc':
		return render_template('detail.html',doc_info=doc_info)
	else:
		return render_template('detail.html',doc_info=doc_info,trans=trans)


@app.route('/statistic',methods=['GET'])
def statistic_page():
	# 统计总数
	total_count = len(all_database())
	word = 'zh_doc'
	column = 'doc_type'
	values = search_from_database(column,word)
	zh_count = len(values)
	en_count = total_count - zh_count
	count = []
	count.append(total_count)
	count.append(zh_count)
	count.append(en_count)

	# 趋势分析
	# 收集分析
	all_date = select_column_database('upload_time')
	tendency = []
	set_date = list(set(all_date))
	set_date = sorted(set_date)
	for i in set_date:
		a = []
		a.append(i[0])
		a.append(all_date.count(i))
		tendency.append(a)

	# 翻译分析
	all_date2 = select_column_database('translate_time')
	trans_tendency = []

	set_date2 = list(set(all_date2))
	set_date2 = sorted(set_date2)
	for i in set_date2:
		if i[0] != '':
			a = []
			a.append(i[0])
			a.append(all_date2.count(i))
			trans_tendency.append(a)

	# 翻译人分析
	all_date3 = select_column_database('translator')
	translator_tendency = []
	set_date3 = list(set(all_date3))
	set_date3 = sorted(set_date3)
	for i in set_date3:
		if i[0] != '':
			a = []
			a.append(i[0])
			a.append(all_date3.count(i))
			translator_tendency.append(a)

	# 上传者分析
	all_date4 = select_column_database('uploader')
	uploader_tendency = []
	set_date4 = list(set(all_date4))
	set_date4 = sorted(set_date4)
	for i in set_date4:
		a = []
		a.append(i[0])
		a.append(all_date4.count(i))
		uploader_tendency.append(a)

	return render_template('statistic.html',count=count,tendency=tendency,trans_tendency=trans_tendency,translator_tendency=translator_tendency,uploader_tendency=uploader_tendency)

@app.route('/api_get_reference',methods=['GET'])
def baiduxueshu_page():
	try:
		doc_title = request.args.get('title','')
		if doc_title == '':
			return '请先输入标题'
		r = requests.get('http://xueshu.baidu.com/s?wd=%s'%(doc_title)).text
		soup = BeautifulSoup(r,'html.parser')
		info_box = soup.find_all('a',attrs={"class":"sc_q"})[0]
		datalink = info_box['data-link']
		datasign = info_box['data-sign']
		reference_url = 'http://xueshu.baidu.com/u/citation?&sign=%s&url=%s&t=cite'%(datasign,datalink)
		reference_r = requests.get(reference_url).text
		reference_list = ast.literal_eval(str(reference_r))
		doc_reference = reference_list['sc_GBT7714']
		return doc_reference
	except:
		return '自动获取失败，请手动复制到此处'

@app.route('/get_doc/<doc_id>',methods=['GET'])
def get_doc_page(doc_id):
		
	values = select_by_id_database(doc_id)[0]
	doc_id = values[1]
	doc_extention = values[2]
	doc_title = values[3]
	doc_author = values[4]
	attachment_filename = doc_title+'_'+doc_author+'.'+doc_extention
	print (attachment_filename)

	path = 'static/docs/'
	file_name =path+doc_id+'.'+doc_extention
	return send_file(file_name, mimetype=None, as_attachment=True, attachment_filename=attachment_filename, add_etags=True, cache_timeout=None, conditional=False, last_modified=None)


@app.errorhandler(404)
def page_not_found(e):
	note = '404'
	return render_template('reflash.html',note=note,gotourl='/')


@app.errorhandler(500)
def internal_server_error(e):
	note = '500'
	return render_template('reflash.html',note=note,gotourl='/')



if __name__ == '__main__':
	# 定义数据库名称并检测是否存在
	db_name = 'webdoc_database.db'
	if check_database() == '0':
		build_database(check_database())

	# 定义文献类型
	doc_upload_select_list = ['测试','test']

	#关闭debug
	app.run(threaded=True,host='0.0.0.0',port=80)
	#开启debug
	#app.run(threaded=True,debug=True,host='0.0.0.0',port=8090)