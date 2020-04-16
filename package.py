import os, sys, argparse, pathlib, json, subprocess, shutil, distutils.dir_util, requests

parser = argparse.ArgumentParser()
parser.add_argument("-s", action="store", required=True, dest="sm")
args = parser.parse_args()

cwd = pathlib.Path(os.getcwd())

sm_scripting = os.path.join(args.sm,"scripting")
sm_include = os.path.join(sm_scripting,"include")
sm_gamedata = os.path.join(args.sm,"gamedata")
spcomp = os.path.join(sm_scripting,"spcomp")
game = pathlib.Path(args.sm).parent.parent

pak = os.path.join(cwd,"package")
pak_sm = os.path.join(pak,"addons/sourcemod")
pak_scripting = os.path.join(pak_sm,"scripting")
pak_include = os.path.join(pak_scripting,"include")
pak_plugins = os.path.join(pak_sm,"plugins")
pak_gamedata = os.path.join(pak_sm,"gamedata")

base_sp_includes = [
	sm_scripting,
	sm_include,
	os.path.join(cwd,"tmp/include"),
]

base_sp_exec = spcomp + " -O2 -v0 -z9"

def handle_sp_folder(folder, extra_includes, sp_pak_info, gitfolder):
	folder = pathlib.Path(folder)
	for file in folder.glob("*.sp"):
		file_basename = os.path.basename(file)
		print("Compiling " + file_basename + " from " + os.path.basename(gitfolder) + "\n")
		code = ""
		newfile_path = os.path.join(cwd,"tmp",file_basename)
		with open(file,"r") as newfile:
			code = newfile.read()
		commit = subprocess.check_output("git rev-parse HEAD", shell=True,cwd=os.getcwd())
		commit = commit[:-1]
		commit = commit.decode("utf-8")
		code = code.replace("$$GIT_COMMIT$$", commit)
		with open(newfile_path,"w") as newfile:
			newfile.write(code)
		file_folder = file.parent
		file_basename = os.path.splitext(file_basename)[0]
		includes = [file_folder]
		for extra in folder.glob("*"):
			if extra.is_file():
				continue
			includes.append(str(extra))
		includes += extra_includes + base_sp_includes
		includes_str = ""
		for inc in includes:
			includes_str += "-i \"" + str(inc) + "\" "
		if sp_pak_info:
			if "name_append" in sp_pak_info:
				file_basename = sp_pak_info["name_append"] + file_basename
		output_path = os.path.join(pak_plugins,file_basename+".smx")
		os.makedirs(pathlib.Path(output_path).parent, exist_ok=True)
		exec = base_sp_exec + " \"" + str(newfile_path) + "\" -o \"" + output_path + "\" " + includes_str
		subprocess.run(exec, shell=True,cwd=os.getcwd())
		os.remove(newfile_path)
		print("")

def handle_sp_includes(name, extra_includes):
	folder = pathlib.Path(os.path.join(cwd,name))
	for extra in folder.glob("addons/sourcemod/scripting/*"):
		if extra.is_file():
			continue
		extra_includes.append(str(extra))

def copy_folder(src, dst):
	if os.path.exists(src):
		src = pathlib.Path(src)
		for folder in src.glob("*"):
			base_name = os.path.basename(folder)
			if base_name == ".git":
				continue
			if folder.is_file():
				continue
			newdst = os.path.join(dst,base_name)
			os.makedirs(newdst,exist_ok=True)
			#shutil.copytree(str(folder),newdst,dirs_exist_ok=True)
			distutils.dir_util.copy_tree(str(folder),newdst)

def handle_wget(url):
	file_path = os.path.join(cwd,"tmp/include",os.path.basename(url))
	if not os.path.exists(file_path):
		with requests.get(url) as file_request:
			with open(file_path,"wb+") as file:
				file.write(file_request.content)

os.makedirs(os.path.join(cwd,"tmp/include"),exist_ok=True)
shutil.rmtree(pak,ignore_errors=True)

for folder in cwd.glob("*"):
	if folder.is_file():
		continue
	if folder == "package":
		continue
	if folder == "scripts":
		continue
	addons = os.path.join(folder,"addons")
	if os.path.exists(addons):
		os.chdir(folder)
		
		copy_folder(folder, pak)
		
		sp_pak_info = None
		sp_pak_info_path = os.path.join(folder,".sp_pak_info")
		extra_includes = []
		if os.path.exists(sp_pak_info_path):
			with open(sp_pak_info_path,"r") as file:
				sp_pak_info = json.load(file)
				if "depends" in sp_pak_info:
					for depend in sp_pak_info["depends"]:
						if "http" not in depend:
							handle_sp_includes(depend, extra_includes)
						else:
							handle_wget(depend)
		
		handle_sp_folder(os.path.join(addons,"sourcemod/scripting"), extra_includes, sp_pak_info, folder)
	
shutil.rmtree(os.path.join(cwd,"tmp"),ignore_errors=True)

copy_folder(pak,game)
