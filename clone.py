import os, sys, argparse, requests, json, pathlib, subprocess, package

cwd = pathlib.Path(os.getcwd())

def clone(url, path):
	old_cwd = os.getcwd()
	if os.path.exists(path):
		os.chdir(path)
		subprocess.run("git fetch", shell=True,cwd=os.getcwd())
		subprocess.run("git reset --hard", shell=True,cwd=os.getcwd())
		subprocess.run("git clean --force -d", shell=True,cwd=os.getcwd())
		os.chdir(old_cwd)
	else:
		os.makedirs(path,exist_ok=True)
		os.chdir(path)
		os.system("git clone --recursive \""+url+"\" \"" + path + "\"")
		os.chdir(old_cwd)

def handle_wget(url, folder):
	file_path = os.path.join(folder,os.path.basename(url))
	if not os.path.exists(file_path):
		with requests.get(url) as file_request:
			os.makedirs(folder,exist_ok=True)
			with open(file_path,"wb+") as file:
				file.write(file_request.content)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", action="store", required=True, dest="toke")
	parser.add_argument("-u", action="store", required=True, dest="user")
	args = parser.parse_args()

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
			clone(clone_url, path)

	if os.path.exists(package.sp_pak_type_path):
		with open(package.sp_pak_type_path,"r") as file:
			sp_pak_type = json.load(file)
			for name in sp_pak_type:
				dep = sp_pak_type[name]
				type = dep["type"]
				url = dep["url"]
				dep_path = os.path.join(package.thirdparty,name)
				if type == "wget":
					handle_wget(url, dep_path)
				elif type == "git":
					clone(url, dep_path)
