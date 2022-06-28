from itsdangerous import BadSignature, Serializer, SignatureExpired, TimedJSONWebSignatureSerializer
from flask import current_app
import time
import traceback
import sys

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

class TokenCode():
  #TODO 創建令牌
  @staticmethod
  def create_token(register_id=None,token_expired=None):
    try:
      if register_id is None or token_expired is None:
        raise Exception("parameter is None")
      else:
        #TODO 參數一是密鑰，搭配flask的話就會使用app.config['SECRET_KEY'],參數二是該令牌的有效時限
        init_key = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=token_expired)
        user_dict_data = {}
        user_dict_data['id'] = register_id
        #TODO 將產生的代碼與使用者ID進行JSON編碼
        token = init_key.dumps(user_dict_data)
        #TODO 將byte格式的字串轉換成字串
        convertion_byte_token = token.decode()
    except Exception as e:
      HandleError(e)
      return None
    return convertion_byte_token
    #TODO 令牌若創建成功則將其傳回

  #TODO 驗證令牌
  @staticmethod
  def verification_token(token):
    try:
        #TODO 參數一是密鑰，搭配flask的話就會使用app.config['SECRET_KEY']
        init_key = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        token_data = init_key.loads(token)
    except SignatureExpired:
        #TODO 當時間超過的時候就會引發SignatureExpired錯誤
        print('SignatureExpired, over time')
        return None,False
    except BadSignature:
        #TODO  當驗證錯誤的時候就會引發BadSignature錯誤
        print('BadSignature, No match')
        return None,False
    except Exception as e:
        HandleError(e)
        return None,False
    return token_data,True
    #TODO 驗證成功則以字典形式返回使用者ID
