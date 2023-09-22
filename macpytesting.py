import json
import pyaml
import os
import sys
import argparse
import platform
import subprocess
import re
import shutil
import datetime

timestamp= datetime.datetime.now()
run_id=timestamp.strftime("%Y%m%d%H%M%S")

# *********************************************
# CREATE SIEBELSETTINGS.TXT FROM FLAT FILE
# ********************************************* 


def env_subst_file(sourcefile, hashref_path, destfile, input_path):
    with open(sourcefile, 'r') as file:
        templatecontent = file.readlines()
    with open(hashref_path, 'r') as json_file:
        json_data = json.load(json_file)
    config_data = {}
    new_content = []
    for line in templatecontent:
        line = line.replace('$', '')
        if line.startswith('#'):
            new_content.append(line.strip())
            continue
        if '=' in line:
            key, value = line.strip().split('=')
            config_data[key] = value
            if value in json_data:
                value=json_data[value]
            new_content.append(f"{key}={value}")
        else:
            new_content.append(line.strip())

    with open(destfile, 'w', newline='\n') as output_file:
        output_file.write('\n'.join(new_content))


    with open(input_path, "r") as file:
    	json_data = json.load(file)
    	DY_CHANGEPARAM=json_data["services"]["create"]["siebel"]["DY_CHANGEPARAM"]
    	DY_SUBSYSTEMPARAM=json_data["services"]["create"]["siebel"]["DY_SUBSYSTEMPARAM"]
    # Create COMP list

    
    sections=["CHANGEPARAM","SUBSYSTEMPARAM","COPYCOMP"]
    for comp in sections:
        i=1
        DY_KEY= "DY_"+comp
        DY_COMPPARAM = json_data["services"]["create"]["siebel"][DY_KEY] 
        with open(destfile, 'a', newline='\n') as file:
            for item in DY_COMPPARAM:
                txt= "["+comp+str(i)+"]"
                file.write('\n')
                file.write(txt)
                file.write('\n')
                for key, value in item.items():
                    txt= key+"="+value
                    file.write("{}\n".format(txt))
                i=i+1
                file.write('\n\n')

    


# *********************************************
# CREATE FLAT FILE FOR ENV_SUBST_FILE 
# *********************************************


def traverse(data, parent=None, dy_vars=None):
    if dy_vars is None:
        dy_vars = {}
    if isinstance(data, dict):
        for key, value in data.items():
            traverse(value, key, dy_vars)
    else:
        dy_vars[parent] = data
    return dy_vars

def convert_json(input_path, hashref_path):
    with open(input_path, 'r') as json_file:
        json_data = json.load(json_file)
    
    dy_vars = traverse(json_data)
    
    with open(hashref_path, 'w') as output_file:
        json.dump(dy_vars, output_file, indent=4)




# *********************************************
# COMPOSE FILE CREATION
# *********************************************

def generate_docker_compose_config(input_path, yaml_file_path,HOMEDIR,patchsetnum):

    server=[]
    with open(input_path, "r") as file:
        json_data = json.load(file)
        Tasks=json_data["services"]["create"]["siebel"]["Task"]
        pubsubrole=json_data["services"]["create"]["siebel"]["Generic"]["DY_PUBSUBROLE"]

        print(f"Patchset Number: {patchsetnum}")
        if pubsubrole == "PUB":
            print("\n pubsubrole = PUB")
            shutil.copy(os.path.join(HOMEDIR, "siebelconfig","kafka","pub","eventpayloadconfigpub.txt"),os.path.join(HOMEDIR, "siebelconfig","kafka","eventpayloadconfig.txt"))
            shutil.copy(os.path.join(HOMEDIR, "siebelconfig","kafka","pub","aieventconfigpub.txt"),os.path.join(HOMEDIR, "siebelconfig","kafka","aieventconfig.txt"))

        elif pubsubrole == "SUB":
            print("\n pubsubrole =  SUB")
            shutil.copy(os.path.join(HOMEDIR, "siebelconfig","kafka","sub","eventpayloadconfigsub.txt"),os.path.join(HOMEDIR, "siebelconfig","kafka","eventpayloadconfig.txt"))
            shutil.copy(os.path.join(HOMEDIR, "siebelconfig","kafka","sub","aieventconfigsub.txt"),os.path.join(HOMEDIR, "siebelconfig","kafka","aieventconfig.txt"))

        Servers=json_data["services"]["create"]["siebel"]
        for key, value in Tasks.items():
            if value=="true":
                val =key.split("_")
                server.append(val[1])
    print (server)
    i=0
    ostype=platform.platform()
    if "Windows" in ostype:
        slash="\\"
    elif "macOS" in ostype:
        slash="/"
    print (slash)
    yaml_cont={'version': '3'}
    yaml_cont["services"]={}


    year, month = patchsetnum.split('.')
    with open(input_path, 'r') as ipfile:
        lines = ipfile.readlines()
    replacement_string = f'ip{year}ps{month}'
    modified_lines = [re.sub(r'ip\d+ps\d+', replacement_string, line) for line in lines]
    with open(input_path, 'w') as opfile:
        opfile.writelines(modified_lines)
    runid=run_id
    basedir=json_data["services"]["service_genric"]["DY_BASEDIR"]
    network=json_data["services"]["service_genric"]["DY_NETWORK_NAME"]
    for x in server:
        for keys,values in Servers.items():
            if x==keys:
                name="DY_"+x+"_NAME"
                container_name=json_data["services"]["create"]["siebel"][keys][name]
                yaml_cont["services"][container_name]={}
                for keys1, values2 in values.items():
                    if "DY_"+x+"_IMAGE" in keys1:
                        yaml_cont["services"][container_name]["image"]=values2
                    if "DY_"+x+"_NAME" in keys1:
                        yaml_cont["services"][container_name]["container_name"]=values2
                    if "DY_"+x+"_HOSTNAME" in keys1:
                        yaml_cont["services"][container_name]["hostname"]=values2
                        yaml_cont["services"][container_name]["networks"]=[network]
                    if "DY_"+x+"_HOSTPORTNUM" in keys1 or "DY_"+x+"_CONTAINERDBPORT" in keys1:
                        hostport=values2
                    if  "DY_"+x+"_CONTAINERPORTNUM" in keys1 or "DY_"+x+"_DBPORT" in keys1:
                        containerport=values2
                        ports=hostport+":"+containerport
                        yaml_cont["services"][container_name]["ports"]=[ports]                
                if x!= "PDB" and x!= "KAFKA" and x!= "ZOOKEEPER":
                    homedir = json_data["services"]["create"]["siebel"][keys]["DY_CONT_HOMEDIR"]
                    aihostname= json_data["services"]["create"]["siebel"]["AI"]["DY_AI_HOSTNAME"]
                    seshostname= json_data["services"]["create"]["siebel"]["SES"]["DY_SES_HOSTNAME"]
                    gwhostname= json_data["services"]["create"]["siebel"]["GW"]["DY_GW_HOSTNAME"]
                    industry= json_data["services"]["create"]["siebel"]["AI1"]["DY_AI1_INDUSTRY"]
                    aiindustry= json_data["services"]["create"]["siebel"]["AI"]["DY_AI_INDUSTRY"]
                    yaml_cont["services"][container_name]["environment"]=["DY_AI_HOSTNAME="+aihostname,"DY_SES_HOSTNAME="+seshostname,"DY_GW_HOSTNAME="+gwhostname,"DY_INDUSTRY="+industry,"DY_AIINDUSTRY="+aiindustry,"SETTINGSFILE=/home/siebel/autoinstall/siebelsettings.txt"]
                    hosts="DY_"+x+"_ETCHOSTALIAS"
                    extrahosts=json_data["services"]["create"]["siebel"][keys][hosts]
                    yaml_cont["services"][container_name]["extra_hosts"]=extrahosts
                    yaml_cont["services"][container_name]["volumes"]=[]
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelfs"+slash+"siebelfs1:"+homedir+"/fs")
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"lb:"+homedir+"/lb")             
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"autoinstall:"+homedir+"/autoinstall")
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"autoinstallLogs:"+homedir+"/logs/autoinstallLogs")
                    if "AI" in keys1:
                        z=x.lower()
                        val = basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"aicfgtoollogs:"+homedir+"/ai/cfgtoollogs/cfg"
                        yaml_cont["services"][container_name]["volumes"].append(val)
                        val = basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"aitomcatlogs:"+homedir+"/ai/applicationcontainer_external/logs"
                        yaml_cont["services"][container_name]["volumes"].append(val)
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"demo"+slash+"files:"+homedir+"/ai/applicationcontainer_external/siebelwebroot/files/custom")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"demo"+slash+"images:"+homedir+"/ai/applicationcontainer_external/siebelwebroot/images/custom")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"demo"+slash+"scripts:"+homedir+"/ai/applicationcontainer_external/siebelwebroot/scripts/siebel/custom")
                    if "AI2" in x:
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"kafka"+slash+"aieventconfig.txt:"+homedir+"/ai/applicationcontainer_external/webapps/aieventconfig.txt")
                    if "GW" in keys1:
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"gtwylogs:"+homedir+"/gw/gtwysrvr/log")    
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"cgcfgtoollogs:"+homedir+"/gw/cfgtoollogs/cfg")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"cgtomcatlogs:"+homedir+"/gw/applicationcontainer_internal/logs")
                        
                    if "SES" in keys1:
                        z=x.lower()
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"sescfgtoollogs:"+homedir+"/ses/cfgtoollogs/cfg")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"seslogarchive:"+homedir+"/ses/siebsrvr/enterprises/siebel/s"+container_name+"/logarchive")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"seslogs:"+homedir+"/ses/siebsrvr/enterprises/siebel/s"+container_name+"/log")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+z+slash+"sestomcatlogs:"+homedir+"/ses/applicationcontainer_internal/logs")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"demo"+slash+"dbdata:"+homedir+"/demo")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"kafka"+slash+"eventpayloadconfig.txt:"+homedir+"/ses/siebsrvr/eventconfig/eventpayloadconfig.txt")
                    if "SES" in keys1 or "GW" in keys1:
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"kwd:"+homedir+"/ses/siebsrvr/kwd")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"upt:"+homedir+"/ses/siebsrvr/upt")
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebellogs"+slash+"siebellogs"+runid+slash+"xsd:"+homedir+"/ses/siebsrvr/xsd")
                    if "CONFIG" not in keys1:
                        yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+".skipconfig:/tmp/.skipconfig")    
                    if "CONFIG" in x:
                        dependson=""
                        yaml_cont["services"][container_name]["depends_on"]={}
                        for container in server:
                            if "CONFIG"  not in container:
                                cont_name="DY_"+container+"_NAME"
                                dependson=json_data["services"]["create"]["siebel"][container][cont_name]
                                yaml_cont["services"][container_name]["depends_on"][dependson]={'condition': 'service_started'}
                elif x=="PDB" and x!= "KAFKA" and x!= "ZOOKEEPER":
                    sid= json_data["services"]["create"]["siebel"]["PDB"]["DY_CDB_SID"]
                    pdb= json_data["services"]["create"]["siebel"]["PDB"]["DY_PDB_PDB"]
                    pwd= json_data["services"]["create"]["siebel"]["PDB"]["DY_PDB_PWD"]
                    charset= json_data["services"]["create"]["siebel"]["PDB"]["DY_PDB_CHARACTERSET"]
                    yaml_cont["services"][container_name]["volumes"]=[]
                    yaml_cont["services"][container_name]["environment"]=["ORACLE_SID="+sid,"ORACLE_PDB="+pdb,"ORACLE_PWD="+pwd,"ORACLE_CHARACTERSET="+charset]
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebeldb"+slash+"pdb1:/opt/oracle/oradata")
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"siebelconfig"+slash+"sqlscripts:/opt/oracle/scripts/startup")
                elif x== "KAFKA":
                    KAFKA_SSL_KEYSTORE_FILENAME= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_SSL_KEYSTORE_FILENAME"]
                    KAFKA_ADVERTISED_LISTENERS= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_ADVERTISED_LISTENERS"]
                    KAFKA_LISTENERS= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_LISTENERS"]
                    KAFKA_SSL_KEY_CREDENTIALS= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_SSL_KEY_CREDENTIALS"]
                    KAFKA_SSL_KEYSTORE_CREDENTIALS= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_SSL_KEYSTORE_CREDENTIALS"]
                    KAFKA_HEAP_OPTS= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_HEAP_OPTS"]
                    KAFKA_INTER_BROKER_LISTENER_NAME= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_INTER_BROKER_LISTENER_NAME"]
                    KAFKA_ZOOKEEPER_CONNECT= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_ZOOKEEPER_CONNECT"]
                    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR= json_data["services"]["create"]["siebel"]["KAFKA"]["KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR"]
                    yaml_cont["services"][container_name]["environment"]=["KAFKA_SSL_KEYSTORE_FILENAME="+KAFKA_SSL_KEYSTORE_FILENAME,"KAFKA_ADVERTISED_LISTENERS="+KAFKA_ADVERTISED_LISTENERS,"KAFKA_LISTENERS="+KAFKA_LISTENERS,"KAFKA_SSL_KEY_CREDENTIALS="+KAFKA_SSL_KEY_CREDENTIALS,"KAFKA_SSL_KEYSTORE_CREDENTIALS="+KAFKA_SSL_KEYSTORE_CREDENTIALS,"KAFKA_HEAP_OPTS="+KAFKA_HEAP_OPTS,"KAFKA_INTER_BROKER_LISTENER_NAME="+KAFKA_INTER_BROKER_LISTENER_NAME,"KAFKA_ZOOKEEPER_CONNECT="+KAFKA_ZOOKEEPER_CONNECT,"KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR="+KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR]
                    homedir = json_data["services"]["create"]["siebel"][keys]["DY_CONT_HOMEDIR"]
                    yaml_cont["services"][container_name]["volumes"]=[]
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"kafka"+slash+"kafkaconfig"+slash+"secrets:/etc/kafka/secrets")
                    yaml_cont["services"][container_name]["volumes"].append(basedir+slash+"kafka"+slash+"kafkaconfig:/etc/kafka")    
                yaml_cont["services"][container_name]["healthcheck"]={'interval': '30s','retries': 450,'timeout': '30s'}
                dyrunid="dy.runid="+runid
                yaml_cont["services"][container_name]["labels"]=[dyrunid]
                

    yaml_cont["networks"]={}
    yaml_cont["networks"][network]={}
    yaml_cont["networks"][network]["name"]=network
    yamlpath=os.path.join(HOMEDIR, patchsetnum)
    new_yaml_file_path= os.path.join(HOMEDIR, patchsetnum ,"docker-compose.yml")
    if not os.path.exists(yamlpath):
        os.makedirs(yamlpath)
    print (new_yaml_file_path)
    with open(new_yaml_file_path, "w") as file:
        yaml_string=pyaml.dump(yaml_cont)
        file.write(yaml_string)


# *********************************************
# EXTRACT PATCHSET
# *********************************************


def extract_patchset_versions(image_names):
    version_pattern = r'ip(\d+)ps(\d+)'
    versions = set()

    for image_name in image_names:
        match = re.search(version_pattern, image_name)
        if match:
            yy, mm = match.groups()
            versions.add(f"{yy}.{mm}")

    return sorted(versions)

# *********************************************
#  Docker Compose Down - CLEANUP
# *********************************************

def docker_compose_cleanup(patchset_version, HOMEDIR):
    path = os.path.join(HOMEDIR, patchset_version)
    compose_file = os.path.join(path, 'docker-compose.yml')
    
    if os.path.exists(compose_file):
        try:
            subprocess.run(['docker-compose', '-f', compose_file, 'down'], cwd=path, check=True)
            print(f"Executed 'docker-compose down' in '{path}'")
        except subprocess.CalledProcessError as e:
            print(f"Error running 'docker-compose down' in '{path}':", e)
    else:
        print(f"No docker-compose.yml found in '{path}'")

# *********************************************************
# DOCKER COMPOSE WRAPPER (extract PS, cleanup and create)
# *********************************************************

def docker_compose_wrapper(input_path, yaml_file_path, HOMEDIR,  cleanup=None, patchsetnum):
    try:
        docker_ps_output = subprocess.check_output(['docker', 'ps', '-a'], universal_newlines=True)
        image_names = re.findall(r'dymensions/siebel:ip\d+ps\d+\w*', docker_ps_output)

        patchset_versions = extract_patchset_versions(image_names)
        print("Extracted Patchset Versions:", ", ".join(patchset_versions))

        if cleanup == "all":
            for patchset_version in patchset_versions:
                docker_compose_cleanup(patchset_version, HOMEDIR)
        elif cleanup:
            cleanup_list = cleanup.split(",")
            for patchset in cleanup_list:
                if patchset.strip() in patchset_versions:
                    docker_compose_cleanup(patchset.strip(), HOMEDIR)
                else:
                    print(f"Invalid patchset number '{patchset.strip()}' or no cleanup required.")


        generate_docker_compose_config(input_path, yaml_file_path,HOMEDIR,patchsetnum)

    except subprocess.CalledProcessError as e:
        print("Error running 'docker ps -a':", e)

# *********************************************
# GIT CLONE
# *********************************************

def gitclone(HOMEDIR):
    
    repo_dir = os.path.join(HOMEDIR,"dy-siebel-ip17")
    github_token="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"
    if not os.path.exists(repo_dir):

        clone_url="https://prajwalpatojoshi:" + github_token + "@github.com/Dymensions/dy-siebel-ip17.git"
        os.system("git clone " + clone_url + " " + repo_dir)
        print("git clone " + clone_url + " " + repo_dir)
        os.chdir(repo_dir)
        #print ("Pull complete")
    else:
        os.chdir(repo_dir)
        os.system("git reset --hard origin/master")
        os.system("git checkout " + "master")
        os.system("git pull origin master")
        #print ("Pull complete")

    folders_to_copy = ["siebelconfig"]

    for folder_name in folders_to_copy:
        source_folder = os.path.join(repo_dir, folder_name)
        destination_folder = os.path.join(HOMEDIR, folder_name)

        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        shutil.copytree(source_folder, destination_folder)
    
    fs1path=os.path.join(HOMEDIR, "siebelfs","siebelfs1")
    if not os.path.exists(fs1path):
        os.makedirs(fs1path)
    shutil.copy2(os.path.join(repo_dir,"siebelfs", "p19285025_121020_LINUX.zip"), os.path.join(fs1path, "p19285025_121020_LINUX.zip"))
    shutil.copy2(os.path.join(repo_dir,"siebelfs", "wallets.zip"), os.path.join(fs1path, "wallets.zip"))
    


def gitcloneexe(HOMEDIR):
    
    repo_dir = os.path.join(HOMEDIR,"dy-cicd-exe")
    github_token="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"
    if not os.path.exists(repo_dir):

        clone_url="https://prajwalpatojoshi:" + github_token + "@github.com/Dymensions/dy-cicd-exe.git"
        os.system("git clone -b dy-cicd-src-inhouse_STAGE " + clone_url + " " + repo_dir)
        print("git clone " + clone_url + " " + repo_dir)
        os.chdir(repo_dir)
        #print ("Pull complete")
    else:
        os.chdir(repo_dir)
        os.system("git reset --hard origin/dy-cicd-src-inhouse_STAGE")
        os.system("git checkout " + "dy-cicd-src-inhouse_STAGE")
        os.system("git pull origin dy-cicd-src-inhouse_STAGE")
        #print ("Pull complete")

    source_file = os.path.join(repo_dir, "autoinstall")
    destination_folder = os.path.join(HOMEDIR, "siebelconfig", "autoinstall") 
    shutil.copy2(source_file, os.path.join(destination_folder, "autoinstall"))

    print("autoinstall file copied to the destination folder, overwriting if necessary.")


# *********************************************************
# DOCKER COMPOSE CLEANUP (extract PS, cleanup)
# *********************************************************

def docker_compose_remove(input_path, yaml_file_path, HOMEDIR,  cleanup=None):
    try:
        docker_ps_output = subprocess.check_output(['docker', 'ps', '-a'], universal_newlines=True)
        image_names = re.findall(r'dymensions/siebel:ip\d+ps\d+\w*', docker_ps_output)

        patchset_versions = extract_patchset_versions(image_names)
        print("Extracted Patchset Versions:", ", ".join(patchset_versions))

        if cleanup == "all":
            for patchset_version in patchset_versions:
                docker_compose_cleanup(patchset_version, HOMEDIR)
        elif cleanup:
            cleanup_list = cleanup.split(",")
            for patchset in cleanup_list:
                if patchset.strip() in patchset_versions:
                    docker_compose_cleanup(patchset.strip(), HOMEDIR)
                else:
                    print(f"Invalid patchset number '{patchset.strip()}' or no cleanup required.")



    except subprocess.CalledProcessError as e:
        print("Error running 'docker ps -a':", e)


    

# *********************************************
# MAIN
# *********************************************

def main():
    parser = argparse.ArgumentParser(description="Script for performing various tasks.")
    parser.add_argument("function_name", choices=["convert_json", "env_subst_file", "generate_docker_compose_config","gitclone","docker_compose_wrapper","docker_compose_remove"], help="Name of the function to run")
    parser.add_argument("path", help="Path to the directory")
    parser.add_argument("--cleanup", help="Cleanup option: 'all' or comma-separated '<patchsetnumber(s)>'")
    parser.add_argument("patchset", help="patchset number")

    args = parser.parse_args()
    HOMEDIR=args.path
    patchsetnum=args.patchset

    input_path = os.path.join(HOMEDIR, "siebelconfig", "autoconfig", "release_configure_110.json")
    hashref_path = os.path.join(HOMEDIR, "siebelconfig", "autoconfig", "release_configure_110.json.flat")
    sourcefile = os.path.join(HOMEDIR, "siebelconfig", "autoinstall", "siebelsettingspro.txt.template")
    destfile = os.path.join(HOMEDIR, "siebelconfig", "autoinstall", "siebelsettings.txt")
    yaml_file_path = os.path.join(HOMEDIR,"docker-compose.yml")


    if args.function_name == "convert_json":
        convert_json(input_path, hashref_path)
        print("convert_json executed successfully")
    elif args.function_name == "env_subst_file":
        env_subst_file(sourcefile, hashref_path, destfile, input_path)
        print("env_subst_file executed successfully")
    elif args.function_name == "gitclone":
        gitclone(HOMEDIR)
        gitcloneexe(HOMEDIR)
        print("gitclone executed ")
    elif args.function_name == "docker_compose_wrapper":
        docker_compose_wrapper(input_path, yaml_file_path, HOMEDIR, args.cleanup,patchsetnum)
        print("docker_compose_wrapper executed successfully")
    elif args.function_name == "docker_compose_remove":
        docker_compose_remove(input_path, yaml_file_path, HOMEDIR, args.cleanup)
        print("docker_compose_remove executed successfully")
    elif args.function_name == "generate_docker_compose_config":
        generate_docker_compose_config(input_path, yaml_file_path,HOMEDIR,patchsetnum)
        print("generate_docker_compose_config executed successfully")
    else:
        print("Function not found or not callable")

if __name__ == "__main__":
    main()