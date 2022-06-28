# uwsgi --emperor /server/vassal
##但此方法的缺點為指令必須加在後面，若日後指令變多，則會難以維護，因此還是建議使用第二種方法。
uwsgi emperor.ini
##由uwsgi服務讀取emperor.ini檔中加入的設定，例如作為副屬的服務檔案其所在的位置，以及主設定檔emperor.ini的日誌檔輸出之目錄
# 兩種用法皆可
# 第一種直接使用指令開啟皇帝模式管轄其所屬的臣子資料夾中的.ini之uwsgi的服務
# 第二種則是撰寫emperor.ini作為啟動皇帝模式的主要檔案，一樣會將其管轄的臣子服務都啟動
# uwsgi app.ini
