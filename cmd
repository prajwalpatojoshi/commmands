1cmd
122ms
1DY-INAFX,1DY-INAFY,1DY-INAFZ



curl  --write-out "HTTPCODE:%{http_code}\n" -u SADMIN:Dymensions -X GET -H Content-Type:application/json https://dymensions22.dymensions.io:9001/siebel/v1.0/data/Automation%20Master%20Suite/Automation%20Master%20Suite/1DY-INAFX --data-urlencode PageSize=100 --data-urlencode "" --data-urlencode "" --connect-timeout 30 -k -g -S -G --silent


https://dymensionsinc.webhook.office.com/webhookb2/ee4cd025-a3df-4644-9a51-55694c7e3b8b@59dce64b-c88b-4e51-8422-b9c6dedf4cbe/IncomingWebhook/97db81b200fb45a08098235ade14794f/2e9ca0f0-4100-4d0b-9b6b-9ce4f3d7cafd

D:\EMPLOYEES\Prajwal_Patojoshi\sonar-scanner-5.0.1.3006-windows\bin\sonar-scanner -Dsonar.projectKey=testprojwin -Dsonar.projectName=testprojwin -Dsonar.sources="D:\EMPLOYEES\Prajwal_Patojoshi\outputsif" -Dsonar.login=sqa_9fcf7837af15c04500e029d3d76adf47f2748595
D:\Dymensions\pipeline.exe getactiveworkspace D:\Dymensions\config_dymensions_win.json DEV "11" 290 SIEBEL sadmin Dymensions "int_dy_inspire_dev"


PRODUCT NAMES    
"Redwood UX for Siebel CRM": "Siebel UI Framework",
    "Modern Siebel CRM Observability - Monitoring and Log Analytics": "Siebel Core - Server Framework",
    "CTMS Mobile SmartScript": "Siebel Apps - Clinical",
    "Web Tools - Applet Format Toolbar": "Siebel UI Framework",
    "UCM using Event Driven Architecture": "Siebel Apps - UCM"
CATEGORY NAMES
    "Redwood UX for Siebel CRM": "Siebel UI Framework",
    "Modern Siebel CRM Observability - Monitoring and Log Analytics": "Siebel Core - Server Framework",
    "CTMS Mobile SmartScript": "Siebel Apps - Clinical",
    "Web Tools - Applet Format Toolbar": "Siebel UI Framework",
    "UCM using Event Driven Architecture": "Siebel Apps - UCM"


{
  "getActiveWorkspaceDetailsWithName": "getActiveWorkspaceGitBranch",
  "exportsifwrapper": "getActiveWorkspaceGitBranch",
  "uploadtobitbucket": "getActiveWorkspaceGitBranch",
  "getactiveworkspace": "getActiveWorkspaceGitBranch",
  "deliverworkspacewithname": "DeliverMergeWorkspaceGit",
  "CreateAZPullRequestMerge": "DeliverMergeWorkspaceGit",
  "checkifazgitbranchExist": "getActiveWorkspaceGitBranch",
  "abandonPR": "PostCompletion",
  "mergestreamandoverwrite":"DeliverMergeWorkspaceGit",
  "createAzPullRequest": "PreApproval"
}


{"status":"error","error":"Repository must be upgraded to use this feature"}HTTPCODE:200


source /home/siebel/.bashrc && source /home/siebel/ses/siebsrvr/siebenv.sh && /home/siebel/ses/siebsrvr/bin/RRCleanup -t SIEBEL -u $sadminuser -p $sadminpassword -r \"Migrated Repository\" -o siebel_DSN  -s /home/siebel/ses/siebsrvr -b B -d Oracle
