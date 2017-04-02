"""
Routes and views for the flask application.
"""
import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
from FlaskWebProject1 import app

import sqlite3
from flask import jsonify

app.debug = True
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_image_info(filename):
    try:     
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO photo (file_name, store_date) VALUES (?, DATE('now'))", (filename,) )
            
            con.commit()
            print("Record successfully added")
    except:
        con.rollback()
        print("error in insert operation")
        return "ERROR"
    finally:
        con.close()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print('post!')
        # check if the post request has the file part
        if 'file' not in request.files:
            print('not in request.files')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print('save file!')
            target = os.path.join(APP_ROOT, 'images/')
            if not os.path.isdir(target):
                os.mkdir(target)
            filename = secure_filename(file.filename)
            file.save(os.path.join("/".join([target, filename])))
            insert_image_info(filename)
            return 'good!'
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
@app.route('/update_name', methods=['POST'])
def update_name():
    if request.method == 'POST':
        name = request.form['name']
        id = request.form['id']
        print(name)
        try:     
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("UPDATE photo SET name=? WHERE id=?", (name, id) )
                
                con.commit()
                print("Record successfully updated")
        except:
            con.rollback()
            print("error in update operation")
            return "ERROR"
        finally:
            con.close()
        return "Good!"
@app.route('/image/<string:filename>')
def send_image(filename):
    target = os.path.join(APP_ROOT, 'images/')
    image = os.path.join("/".join([target, filename]))
    return  send_file(image)#send_from_directory("images", filename)

@app.route('/list_origin')
def list1():
   con = sqlite3.connect("database.db")
   con.row_factory = sqlite3.Row
   
   cur = con.cursor()
   cur.execute("select * from photo")
   
   r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
   #rows = cur.fetchall()
   con.close()
   return jsonify(foods=r) #render_template("list.html", rows = rows) #

@app.route('/list')
def list2():
   con = sqlite3.connect("database.db")
   con.row_factory = sqlite3.Row
   
   cur = con.cursor()
   cur.execute("SELECT name, store_date, elapse_date\
                FROM (SELECT name, store_date , Cast ((\
                    JulianDay('now') - JulianDay(store_date)\
                    ) As Integer) as elapse_date\
                    FROM (SELECT name, store_date FROM photo))\
                WHERE elapse_date > 6")
   
   r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
   
   #rows = cur.fetchall()
   con.close()
   return jsonify(foods=r)#render_template("list2.html", rows = rows) #

@app.route('/clear')
def clear():
    try:     
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("DELETE FROM photo")
            
            con.commit()
            print("Record successfully added")
    except:
        con.rollback()
        print("error in insert operation")
        return "ERROR"
    finally:
        con.close()
        return "Delete all food"



# @app.route('/home')
# def home():
    
#     """Renders the home page."""
#     return render_template(
#         'index.html',
#         title='Home Page',
#         year=datetime.now().year,
#     )

# @app.route('/contact')
# def contact():
#     """Renders the contact page."""
#     return render_template(
#         'contact.html',
#         title='Contact',
#         year=datetime.now().year,
#         message='Your contact page.'
#     )

# @app.route('/about')
# def about():
#     """Renders the about page."""
#     return render_template(
#         'about.html',
#         title='About',
#         year=datetime.now().year,
#         message='Your application description page.'
#     )
