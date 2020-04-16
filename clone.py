import os, sys, argparse, requests, json, pathlib, subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-t", action="store", required=True, dest="toke")
parser.add_argument("-u", action="store", required=True, dest="user")
args = parser.parse_args()

cwd = pathlib.Path(os.getcwd())

api_url="https://api.github.com/orgs/ServerDosBrothers/repos?per_page=999"
with requests.get(api_url, auth=(args.user,args.toke)) as request:
	json_response = json.loads(request.text)
	
	#print(json.dumps(json_response, indent=4, sort_keys=True))
	
	if isinstance(json_response, dict):
		json_response = [json_response]
	for repo_entry in json_response:
		clone_url = repo_entry["clone_url"]
		if clone_url == None:
			continue
		name = repo_entry["name"]
		path = os.path.join(cwd,name)
		if os.path.exists(path):
			os.chdir(path)
			subprocess.run("git fetch origin", shell=True,cwd=os.getcwd())
			subprocess.run("git reset --hard origin", shell=True,cwd=os.getcwd())
			subprocess.run("git clean --force -d", shell=True,cwd=os.getcwd())
		else:
			os.chdir(cwd)
			os.system("git clone --recursive "+clone_url)
