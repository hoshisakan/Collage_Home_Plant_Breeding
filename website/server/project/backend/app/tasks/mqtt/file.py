import os

class GetFileWorkingPath():
  @classmethod
  def GetFullPath(cls, **kwargs):
    #TODO 取得當前工作目錄
    working_directory = lambda:os.path.abspath(os.path.join(os.getcwd(), '..'))
    #TODO 取得當前工作目錄並將目錄與檔案名稱結合並回傳
    if kwargs['mode'] == True:
      return os.path.join(working_directory(), kwargs['dirname'],kwargs['filename'])
    #TODO 取得當前工作目錄並將目錄名稱結合並回傳
    else:
      return os.path.join(working_directory(),kwargs['dirname'])

