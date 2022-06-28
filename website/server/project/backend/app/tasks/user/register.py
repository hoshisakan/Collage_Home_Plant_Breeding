from flask import jsonify,request,Blueprint,current_app
import traceback
import datetime
import sys
import os
from flask_bcrypt import Bcrypt
from tasks.module.database_connection import DataBase as DB
from tasks.module.validate_token import TokenCode

def GetStaticPath(dirname=None):
    static_file_path = os.path.abspath(os.path.join(os.getcwd(),'../../..'))
    full_path = os.path.join(static_file_path, dirname)
    return full_path

register = Blueprint('register', __name__, url_prefix='/register',
                  static_folder=GetStaticPath('frontend/dist/static'),
                  template_folder=GetStaticPath('frontend/dist'))

#TODO 初始化套件於當前的應用
bcrypt = Bcrypt(current_app)

update_data_count = 0

def HandleError(exp_object=None):
    error_class = exp_object.__class__.__name__
    # TODO 例外類型
    detail = exp_object.args[0]
    # TODO 引發例外原因
    cl, exc, tb = sys.exc_info()
    lastCallStack = traceback.extract_tb(tb)[-1]
    fileName = lastCallStack[0]
    lineNumber = lastCallStack[1]
    funcName = lastCallStack[2]
    errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(
            fileName, lineNumber, funcName, error_class, detail)
    print(errMsg)

exc_time = lambda:datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")

#TODO 若產品辨識碼正確，且使用者帳密與電郵沒有重複，則更新使用者的資料
def updateUserData(**kwargs):
    # global update_data_count
    try:
        # print(args[0],args[1],args[2],args[3])
        # print(type(args[0]))
        result = {}
        with DB() as cursor:
            print(kwargs.items())
            sql_command = "SELECT * FROM User_data WHERE user_name = '%s' OR user_email = '%s';" % (kwargs['username'],kwargs['email'])
            query_res = cursor.execute(sql_command)
            row_count = cursor.rowcount
            
            result['row_count'] = row_count
            if row_count > 0:
                result['register_status'] = False
            else:
                sql_command = "INSERT INTO User_data (user_name, user_email, user_password) VALUES ('%s','%s','%s')" % (kwargs['username'],kwargs['email'],kwargs['password'])
                query_res = cursor.execute(sql_command)
                result['register_status'] = True
                result['add_query_res'] = query_res
        return result
    except Exception as e:
        HandleError(e)

#TODO 將輸入的密碼進行加密
def password_encrypt(form_password=None):
    if form_password is None:
        return None
        #TODO 若未收到使用者輸入的密碼，則返回None
    else:
        bcrypt_hash = bcrypt.generate_password_hash(form_password).decode('utf-8')
        return bcrypt_hash
        #TODO 回傳加密後的哈希碼

#TODO 檢查前端表單提交的資料是否與資料表中的數據重複，若無重複則更新數據；反之，返回False
def checkFieldData(**kwargs):
    try:
        response_check_result = {}
        result = updateUserData(
                    # kwargs['form_identity_code'],
                    username=kwargs['form_username'],
                    password=password_encrypt(kwargs['form_password']),
                    email=kwargs['form_email'])
        response_check_result['query_res'] = result

        return response_check_result
    except Exception as e:
        HandleError(e)

#TODO 接收表單的使用者註冊資料
@register.route('/user/confrim',methods=['POST'])
def register_confirm():
  if request.method == 'POST':
    username = request.get_json()['username']
    password = request.get_json()['password']
    email = request.get_json()['email']
    # identity_code = request.get_json()['identity_code']
    check_result = checkFieldData(
    #   form_identity_code=identity_code,
      form_username=username,
      form_password=password,
      form_email=email
    )
    return jsonify(check_result)



