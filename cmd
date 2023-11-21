1cmd
122ms
1DY-INAFX,1DY-INAFY,1DY-INAFZ



curl  --write-out "HTTPCODE:%{http_code}\n" -u SADMIN:Dymensions -X GET -H Content-Type:application/json https://dymensions22.dymensions.io:9001/siebel/v1.0/data/Automation%20Master%20Suite/Automation%20Master%20Suite/1DY-INAFX --data-urlencode PageSize=100 --data-urlencode "" --data-urlencode "" --connect-timeout 30 -k -g -S -G --silent
