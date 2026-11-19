from mysqlassist import MYPGuard
import json

gd = MYPGuard.LoadByFile("mysqlassist/cfg/database.json")
myp = MYPGuard.MYP("game")

print(myp.Exec("UPDATE `data_UserAccount` SET `EXP` = 2000 WHERE `UUID` = 1000;;SELECT ROW_COUNT()"))
    
