import os, sys, argparse, pathlib, json, subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-s", action="store", required=True, dest="sm")
args = parser.parse_args()

cwd = pathlib.Path(os.getcwd())

sm_scripting = os.path.join(args.sm,"scripting")
sm_include = os.path.join(sm_scripting,"include")
spcomp = os.path.join(sm_scripting,"spcomp")

pak = os.path.join(cwd,"package")
pak_sm = os.path.join(pak,"addons/sourcemod")
pak_scripting = os.path.join(pak_sm,"scripting")
pak_include = os.path.join(pak_scripting,"include")
pak_plugins = os.path.join(pak_sm,"plugins")

base_sp_includes = [
	sm_scripting,
	sm_include,
]

base_sp_exec = spcomp + " -O2 -v0 -z9"

def handle_sp_folder(folder, extra_includes, sp_pak_info):
	folder = pathlib.Path(folder)
	for file in folder.glob("*.sp"):
		file_basename = os.path.basename(file)
		code = ""
		newfile_path = os.path.join(cwd,"tmp",file_basename)
		with open(file,"r") as newfile:
			code = newfile.read()
		commit = subprocess.check_output("git rev-parse HEAD", shell=True,cwd=os.getcwd())
		commit = commit[:-1]
		commit = commit.decode("utf-8")
		#print(commit)
		code = code.replace("$$GIT_COMMIT$$", commit)
		#print(code)
		with open(newfile_path,"w") as newfile:
			newfile.write(code)
		file_folder = file.parent
		file_basename = os.path.splitext(file_basename)[0]
		includes = base_sp_includes + extra_includes + [file_folder]
		for extra in folder.glob("*"):
			if extra.is_file():
				continue
			if os.path.basename(extra) == ".git":
				continue
			includes.append(str(extra))
		includes_str = ""
		for inc in includes:
			includes_str += "-i \"" + str(inc) + "\" "
		if sp_pak_info:
			if "name_append" in sp_pak_info:
				file_basename = sp_pak_info["name_append"] + file_basename
		output_path = os.path.join(pak_plugins,file_basename+".smx")
		#print(pathlib.Path(output_path).parent)
		os.makedirs(pathlib.Path(output_path).parent, exist_ok=True)
		exec = base_sp_exec + " \"" + str(newfile_path) + "\" -o \"" + output_path + "\" " + includes_str
		#print(file)
		#print(exec)
		os.system(exec)
		os.remove(newfile_path)

def handle_sp_copy():
	pass

def handle_sp_includes(name, extra_includes):
	folder = pathlib.Path(os.path.join(cwd,name))
	if os.path.exists(os.path.join(folder,"addons")):
		for extra in folder.glob("addons/sourcemod/scripting/*"):
			if extra.is_file():
				continue
			extra_includes.append(str(extra))
	else:
		for extra in folder.glob("*"):
			if extra.is_file():
				continue
			if os.path.basename(extra) == ".git":
				continue
			if os.path.basename(extra) == "gamedata":
				continue
			extra_includes.append(str(extra))

os.mkdir(os.path.join(cwd,"tmp"))

for folder in cwd.glob("*"):
	if folder.is_file():
		continue
	if folder == "package":
		continue
	tmp = ""
	
	os.chdir(folder)
	
	sp_pak_info = None
	sp_pak_info_path = os.path.join(folder,".sp_pak_info")
	extra_includes = []
	if os.path.exists(sp_pak_info_path):
		with open(sp_pak_info_path,"r") as file:
			sp_pak_info = json.load(file)
			if "depends" in sp_pak_info:
				for depend in sp_pak_info["depends"]:
					handle_sp_includes(depend, extra_includes)
	
	#tmp = os.path.join(folder,"include")
	#if os.path.exists(tmp):
	#	os.system("cp" + tmp + )
	#tmp = os.path.join(folder,"gamedata")
	#if os.path.exists(tmp):
	#	os.system("cp" + tmp + )
	#handle_sp_folder(os.path.join(folder,"addons/sourcemod/scripting"), extra_includes, sp_pak_info)
	handle_sp_folder(folder, extra_includes, sp_pak_info)
	
os.rmdir(os.path.join(cwd,"tmp"))
