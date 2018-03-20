import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
from ChatKit import app

import sqlite3
from flask import jsonify

app.debug = True
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


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
    else:
        #GET - 테스트용
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

@app.route('/delete_food',methods =['POST'])
def delete_food():
    if request.method == 'POST':
        name = request.form['name']
        try:
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("DELETE FROM photo WHERE name=?",(name,))
                con.commit()
        except:
            con.rollback()
            return "ERROR"
        finally:
            con.close()
        return "Good!"

@app.route('/insert_food', methods=['POST'])
def insert_food():
    if request.method == 'POST':
        name = request.form['name']
        try:
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO photo (name, store_date) VALUES (?, DATE('now'))", (name,))
                
                con.commit()
        except:
            con.rollback()
            return "ERROR"
        finally:
            con.close()
        return "Good!"


@app.route('/image/<string:filename>')
def send_image(filename):
    target = os.path.join(APP_ROOT, 'images/')
    image = os.path.join("/".join([target, filename]))
    return  send_file(image)


@app.route('/list_origin')
def list1():
   con = sqlite3.connect("database.db")
   con.row_factory = sqlite3.Row
   
   cur = con.cursor()
   cur.execute("select * from photo")
   
   row = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
   con.close()
   return jsonify(foods=row) 


@app.route('/list')
def list2():
   con = sqlite3.connect("database.db")
   con.row_factory = sqlite3.Row
   
   cur = con.cursor()
   cur.execute("SELECT name, file_name ,store_date, elapse_date\
                FROM (SELECT name, file_name ,store_date , Cast ((\
                    JulianDay('now') - JulianDay(store_date)\
                    ) As Integer) as elapse_date\
                    FROM (SELECT name, file_name, store_date FROM photo))\
                WHERE elapse_date > 6")
   
   r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
   
   con.close()
   return jsonify(foods=r)


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


