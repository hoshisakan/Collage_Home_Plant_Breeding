from flask import jsonify, request, Blueprint, current_app
import sys
import os
from tasks.module.database_connection import DataBase as DB
from tasks.module.validate_token import TokenCode
import traceback
import datetime
from flask_bcrypt import Bcrypt

def GetStaticPath(dirname=None):
    static_file_path = os.path.abspath(os.path.join(os.getcwd(),'../../..'))
    full_path = os.path.join(static_file_path, dirname)
    return full_path

login = Blueprint('login', __name__, url_prefix='/login',
                  static_folder=GetStaticPath('frontend/dist/static'),
                  template_folder=GetStaticPath('frontend/dist'))

#TODO 初始化套件於當前的應用
bcrypt = Bcrypt(current_app)

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

#TODO 將輸入的密碼進行解密驗證
def password_decrypt(form_password=None, hash_password=None):
    if form_password is None or hash_password is None:
        return None
        #TODO 若未收到使用者輸入的密碼或未獲取該使用者資料庫中的密碼，則返回None
    else:
        check_result = bcrypt.check_password_hash(
            hash_password, form_password)
        #TODO 檢查輸入的密碼是否符合資料庫中的密碼，第一個參數是資料庫儲存的該使用者之密碼(哈希碼)，第二個參數則是使用者輸入的密碼
        return check_result
        #TODO 以布林值回傳驗證的結果，True為相符，False則為不相符

#TODO 若使用者電郵正確，則依據其從資料庫中取出相對應的使用者名稱
def get_login_username(user_email=None):
  if user_email is not None:
    with DB() as db:
      sql_command = "SELECT user_name FROM User_data WHERE user_email = '%s'" % (user_email)
      db.execute(sql_command)
      data = db.fetchall()
    return data[0]['user_name']

#TODO 核對表單輸入的使用者名稱或電郵，以及使用者密碼是否正確
def check_user(formData=None):
  if formData is not None:
    with DB() as db:
      sql_command = "SELECT user_name,user_email,user_password FROM User_data"
      db.execute(sql_command)
      data = db.fetchall()
      temp_check_result = {}

    #TODO 迭代資料庫的使用者帳號、電郵，以及密碼
      for tableData in data:
        #TODO 如果使用者名稱正確，且密碼亦正確，則允許登入，並返回一組時效為1小時的令牌
        if tableData['user_name'] == formData['username'] and password_decrypt(formData['password'],tableData['user_password']) is True:
            temp_check_result['login_token'] = TokenCode.create_token(formData['username'],1800)
            temp_check_result['username_validate'] = True
            temp_check_result['password_validate'] = True
            temp_check_result['login_allow'] = True
            break
         #TODO 如果使用者電郵正確，且密碼亦正確，則允許登入，並返回一組時效為1小時的令牌
        elif tableData['user_email'] == formData['username'] and password_decrypt(formData['password'],tableData['user_password']) is True:
            temp_check_result['login_token'] = TokenCode.create_token(get_login_username(formData['username']),1800)
            temp_check_result['username_validate'] = True
            temp_check_result['password_validate'] = True
            temp_check_result['login_allow'] = True
            break
        #TODO 如果使用者名稱或使用者電郵正確，但密碼不正確，則不允許登入
        elif tableData['user_name'] == formData['username'] or tableData['user_email'] == formData['username'] and password_decrypt(formData['password'],tableData['user_password']) is False:
            temp_check_result['username_validate'] = True
            temp_check_result['password_validate'] = False
            temp_check_result['login_allow'] = False
            break
        #TODO 如果使用者名稱與使用者電郵皆不正確，則不允許登入
        else:
            temp_check_result['username_validate'] = False
            temp_check_result['password_validate'] = False
            temp_check_result['login_allow'] = False
      return temp_check_result
    return False
  return None

#TODO 取得登入的使用者名稱，將使用者登入獲取的令牌還原成一組使用者名稱
@login.route('/user/name/get', methods=['POST'])
def get_user_name():
  if request.method == 'POST':
    authToken = request.get_json()['authToken']
    login_username,validate_token_result = TokenCode.verification_token(authToken)
    if login_username is not None and validate_token_result is True:
      result = {"username": login_username['id']}
    else:
      result = {"username": ''}
    print(result)
    return jsonify(result)

#TODO 驗證客戶端於表單輸入的使用者名稱或電郵，以及其密碼
@login.route('/user/validate', methods=['POST'])
def validateUser():
  if request.method == 'POST':
    username = request.get_json()['username']
    password = request.get_json()['password']
    form_data = {'username': username, 'password': password}
    #TODO 呼叫核對身份的方法，並暫存檢查的結果
    checkResult = check_user(form_data)
    return jsonify(checkResult)
