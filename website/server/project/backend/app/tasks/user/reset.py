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

reset = Blueprint('reset', __name__, url_prefix='/reset',
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

exc_time = lambda:datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")

#TODO 若使用者重設的密碼未與原本的相同，則更新其輸入的密碼，並傳回更新結果，大於1則表示成功；反之，則更新失敗
def updateUserPassword(formData=None):
    with DB() as db:
      sql_command = "UPDATE User_data SET user_password = '%s' WHERE user_name = '%s'" % (formData['newPassword'],formData['resetUserName'])
      exc_result = db.execute(sql_command)
      print(exc_time(), exc_result)
    return exc_result

#TODO 取得使用者ID
def getUserID(formData=None):
    if formData is not None:
        with DB() as db:
            sql_command = "SELECT user_id FROM User_data WHERE user_name='%s' AND user_email='%s' " % (formData['username'], formData['email'])
            db.execute(sql_command)
            data = db.fetchall()
            print(data)
        return data[0]['user_id']

#TODO 生成一組重設密碼的令牌，時效為15分鐘
def createResetPasswordToken(applyUserForm=None):
  try:
    if applyUserForm is not None:
      resetUserID = getUserID(applyUserForm)
      reset = {}
      resetPasswordToken = TokenCode.create_token(resetUserID,900)
      reset['token'] = resetPasswordToken
      return reset
  except Exception as e:
      HandleError(e)

#TODO 檢查提交表單的使用者其輸入的註冊資料是否與資料表中的相符
def checkApplyForm(checkFormData=None):
    if checkFormData is not None:
        with DB() as db:
            sql_command = "SELECT user_name,user_email FROM User_data"
            db.execute(sql_command)
            data = db.fetchall()
            temp_check_result = {}

            for tableData in data:
                if tableData['user_name'] == checkFormData['username'] and tableData['user_email'] == checkFormData['email']:
                    temp_check_result['whether_pass'] = True
                    temp_check_result['username_validate'] = True
                    temp_check_result['email_validate'] = True
                    break
                elif tableData['user_name'] == checkFormData['username'] and tableData['user_email'] != checkFormData['email']:
                    temp_check_result['whether_pass'] = False
                    temp_check_result['username_validate'] = True
                    temp_check_result['email_validate'] = False
                    break
                elif tableData['user_name'] != checkFormData['username'] and tableData['user_email'] == checkFormData['email']:
                    temp_check_result['whether_pass'] = False
                    temp_check_result['username_validate'] = False
                    temp_check_result['email_validate'] = True
                    break
                else:
                    temp_check_result['whether_pass'] = False
                    temp_check_result['username_validate'] = False
                    temp_check_result['email_validate'] = False
            return temp_check_result

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

def checkPasswordField(checkFormData):
  if checkFormData is not None:
    with DB() as db:
      sql_command = "SELECT user_password FROM User_data WHERE user_name = '%s'" % (checkFormData['resetUserName'])
      db.execute(sql_command)
      data = db.fetchall()
      temp_check_result = {}

      for tableData in data:
	    #TODO 若重設的密碼未與原本的相同，則返回True
        if password_decrypt(checkFormData['newPassword'],tableData['user_password']) is False:
          temp_check_result['whether_pass'] = True
          temp_check_result['password_validate'] = True
		#TODO 反之，則返回False
        else:
          temp_check_result['whether_pass'] = False
          temp_check_result['password_validate'] = False
      return temp_check_result

#TODO 將輸入的密碼進行加密
def password_encrypt(form_password=None):
    if form_password is None:
        return None
        #TODO 若未收到使用者輸入的密碼，則返回None
    else:
        bcrypt_hash = bcrypt.generate_password_hash(form_password).decode('utf-8')
        return bcrypt_hash
        #TODO 回傳加密後的哈希碼

#TODO 驗證重設密碼頁面使用者所輸入的密碼
@reset.route('/password/validate', methods=['POST'])
def validate_reset_password():
  resetUserName = request.get_json()['resetUserName']
  print(resetUserName)
  newPassword = request.get_json()['newPassword']
  formData = {
    "resetUserName": resetUserName,
    "newPassword": newPassword
  }
  checkResult = checkPasswordField(formData)

  #TODO 若重設輸入的新密碼未與原先的相同，則會更新密碼
  if checkResult['whether_pass'] is True:
    #TODO 將新密碼轉換成哈希碼，並更新原先formData字典的新密碼
    formData['newPassword'] = password_encrypt(newPassword)
	#TODO 呼叫更新密碼的方法，將其更新至資料表中
    resetResult = updateUserPassword(formData)
	#TODO 若更新成功(返回為1)，則設重設密碼的結果為True
    if resetResult > 0:
      checkResult['resetResult'] = True
	#TODO 反之，則設重設密碼的結果為False
    else:
      checkResult['resetResult'] = False
  return checkResult

def getUsername(resetUserID=None):
    with DB() as db:
      sql_command = "SELECT user_name FROM User_data WHERE user_id = %s" % (resetUserID)
      db.execute(sql_command)
      data = db.fetchall()
      print(data)
    return data[0]['user_name']

#TODO 還原重設密碼令牌的內容
def recoveryToken(resetToken=None):
  resetUserName = {'username': ''}
  if resetToken is not None:
    reset_user_id,validate_token_result = TokenCode.verification_token(resetToken)
    if reset_user_id is not None and validate_token_result is True :
	  #TODO 還原後為使用者的ID，用其取使用者的名稱
      resetUserName['username'] = getUsername(reset_user_id['id'])
      resetUserName['allowReset'] = True
    else:
      resetUserName['allowReset'] = False
  return resetUserName

#TODO 使用重設密碼的令牌獲取使用者的名稱
@reset.route('/password/username/get', methods=['POST'])
def get_reset_username():
  resetToken = request.get_json()['resetToken']
  if request.method == 'POST':
    result = {}
    if resetToken is not None:
      result = recoveryToken(resetToken)
    print(result)
    return jsonify(result)

#TODO 處理使用者提交的重設密碼申請，若使用者與其電郵都相符，則寄送重設密碼的驗證信
@reset.route('/password/apply', methods=['POST'])
def reset_password_apply():
  applyUserName = request.get_json()['applyUserName']
  applyUserEmail = request.get_json()['applyUserEmail']
  checkResult = {}

  if applyUserName is not None and applyUserEmail is not None:
    collectFormData = {
      "username":applyUserName,
      "email":applyUserEmail
    }
    checkResult = checkApplyForm(collectFormData)
    if checkResult['whether_pass'] is True:
        getResetToken = createResetPasswordToken(collectFormData)
        if getResetToken.get('token',None) is not None:
          checkResult.update(getResetToken)
    return checkResult
