import re, os, sys, argparse, pathlib, json, subprocess, shutil, distutils.dir_util, package

cwd = pathlib.Path(os.getcwd())

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", action="store", required=False, dest="cpl")
	parser.add_argument("-uf", action="store_true", required=False, dest="cuf")
	parser.add_argument("-l4d2", action="store_true",required=False, dest="L4D2")
	args = parser.parse_args()
	
	vscode_dir = os.path.join(cwd,"vscode")
	repo_info_path = os.path.join(vscode_dir,".repo_info")
	
	if args.cpl is not None:
		if os.path.exists(repo_info_path):
			with open(repo_info_path,"r") as file:
				repo_info = json.load(file)
				file_basename = os.path.basename(args.cpl)
				if file_basename in repo_info:
					repo = repo_info[file_basename]
					cmd = "python \"" + os.path.join(cwd,"scripts/setup_server.py") + "\" -p " + repo + " -c -nc "
					if args.L4D2:
						cmd += "-l4d2 "
					if args.cuf:
						cmd += "-pf " + file_basename
					subprocess.run(cmd, shell=True,cwd=os.getcwd())
				else:
					print(file_basename + " not found")
	else:
		repo_info = {}
		for folder in cwd.glob("*"):
			if folder.is_file():
				continue
			folder_str = str(folder)
			for bad in package.bad_folders:
				if folder_str == os.path.join(cwd,bad):
					continue
			addons = os.path.join(folder,"addons")
			if os.path.exists(addons):
				for file in folder.glob("addons/**/*"):
					if not file.is_file():
						continue
					newpath = str(file).replace(folder_str,"")
					newpath = newpath[1:]
					newpath = os.path.join(vscode_dir,"files",newpath)
					file_basename = os.path.basename(file)
					repo_info[file_basename] = os.path.basename(folder)
					os.makedirs(pathlib.Path(newpath).parent,exist_ok=True)
					if not os.path.exists(newpath):
						os.symlink(file,newpath)
		
		with open(repo_info_path, "w") as file:
			repo_info = json.dumps(repo_info)
			file.write(repo_info)
		
		with open(os.path.join(vscode_dir,"svb.code-workspace"), "w") as file:
			json_data = {}
			json_data["folders"] = [
				{"path": "files"},
			]
			json_data["settings"] = {}
			if args.L4D2:
				inc_dir = os.path.join(cwd,"server/serverfiles-l4d2/left4dead2/addons/sourcemod/scripting/include")
			else:
				inc_dir = os.path.join(cwd,"server/serverfiles-tf/tf/addons/sourcemod/scripting/include")
			json_data["settings"]["sourcepawnLanguageServer.sourcemod_home"] = inc_dir
			json_data = json.dumps(json_data)
			file.write(json_data)
			
		os.makedirs(os.path.join(vscode_dir,"files/.vscode"),exist_ok=True)
		with open(os.path.join(vscode_dir,"files/.vscode/tasks.json"), "w") as file:
			json_data = {}
			json_data["version"] = "2.0.0"
			json_data["tasks"] = [
				{
					"label": "setup_server",
					"type": "shell",
					"options": {
						"cwd": str(cwd),
					},
					"group": {
						"kind": "build",
						"isDefault": True,
					}
				}
			]
			extra_args = ""
			if args.L4D2:
				extra_args += "-l4d2 "
			if args.cuf:
				extra_args += "-uf "
			json_data["tasks"][0]["command"] = "python \"" + os.path.join(cwd,"scripts/vs_code.py") + "\" -c \"${file}\" " + extra_args
			json_data = json.dumps(json_data)
			file.write(json_data)
