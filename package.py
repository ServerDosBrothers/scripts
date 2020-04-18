import os, sys, argparse, pathlib, json, subprocess, shutil, distutils.dir_util, requests
from clone import clone

parser = argparse.ArgumentParser()
parser.add_argument("-s", action="store", required=True, dest="sm")
parser.add_argument("-d", action="store",nargs="*",required=False, dest="defi")
parser.add_argument("-p", action="store",nargs="*",required=False, dest="plu")
args = parser.parse_args()

defines = ""
if args.defi:
	for d in args.defi:
		defines += d + ' '

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
]

base_sp_exec = spcomp + " -O2 -v0 -z9"

def handle_sp_folder(folder, extra_includes, sp_pak_info):
	folder = pathlib.Path(folder)
	gitfolder = os.path.basename(os.getcwd())
	for file in folder.glob("*.sp"):
		file_basename = os.path.basename(file)
		if sp_pak_info:
			if "ignore_plugins" in sp_pak_info:
				if file_basename in sp_pak_info["ignore_plugins"]:
					continue
		print("Compiling " + file_basename + " from " + gitfolder + "\n")
		code = ""
		newfile_path = os.path.join(cwd,"tmp",file_basename)
		with open(file,"r") as newfile:
			code = newfile.read()
		commit = ""
		if os.path.exists(os.path.join(os.getcwd(), ".git")):
			commit = subprocess.check_output("git rev-parse HEAD", shell=True,cwd=os.getcwd())
			commit = commit[:-1]
			commit = commit.decode("utf-8")
		else:
			commit = "Unknown"
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
		if "SVB-" in gitfolder:
			file_basename = "svb/" + file_basename
		else:
			file_basename = "thirdparty/" + file_basename
		extra_flags = ""
		if sp_pak_info:
			if "name_append" in sp_pak_info:
				file_basename = sp_pak_info["name_append"] + file_basename
			if "disable_warnings" in sp_pak_info:
				for warn in sp_pak_info["disable_warnings"]:
					extra_flags += "-w" + str(warn) + ' '
			if "warning_errors" in sp_pak_info:
				if sp_pak_info["warning_errors"] == True:
					extra_flags += "-E "
			if "defines" in sp_pak_info:
				for define, value in sp_pak_info["defines"].items():
					extra_flags += define + '=' + value + ' '
		output_path = os.path.join(pak_plugins,file_basename+".smx")
		os.makedirs(pathlib.Path(output_path).parent, exist_ok=True)
		exec = base_sp_exec + " \"" + str(newfile_path) + "\" -o \"" + output_path + "\" " + includes_str + extra_flags
		exec += defines
		subprocess.run(exec, shell=True,cwd=os.getcwd())
		os.remove(newfile_path)
		print("")

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

def handle_git_repo(dep, dep_path, extra_includes):
	if "addons/sourcemod" in dep:
		extra_includes += [os.path.join(dep["addons/sourcemod"], "include")]

def handle_wget(url, folder):
	file_path = os.path.join(folder,os.path.basename(url))
	if not os.path.exists(file_path):
		with requests.get(url) as file_request:
			os.makedirs(folder,exist_ok=True)
			with open(file_path,"wb+") as file:
				file.write(file_request.content)

def handle_depends(depends, extra_includes, compile_later):
	for depend in depends:
		is_root_repo = True
		if sp_pak_type:
			if depend in sp_pak_type:
				dep = sp_pak_type[depend]
				type = dep["type"]
				dep_path = os.path.join(thirdparty,depend)
				is_root_repo = False
				if type == "wget":
					handle_wget(dep["url"], dep_path)
					extra_includes += [dep_path]
				elif type == "git":
					clone(dep["url"], dep_path)
					if "path_map" in dep:
						path_map = dep["path_map"]
						if "addons/sourcemod/scripting/include" in path_map:
							extra_includes += [os.path.join(dep_path, path_map["addons/sourcemod/scripting/include"])]
					compile_later += [(dep,dep_path)]
		if is_root_repo:
			extra_includes += [os.path.join(cwd,depend,"addons/sourcemod/scripting/include")]

thirdparty = os.path.join(cwd,"thirdparty")
os.makedirs(thirdparty,exist_ok=True)
os.makedirs(os.path.join(cwd,"tmp"),exist_ok=True)
shutil.rmtree(pak,ignore_errors=True)

sp_pak_type = None
sp_pak_type_path = os.path.join(cwd,"scripts/.sp_pak_type")
if os.path.exists(sp_pak_type_path):
	with open(sp_pak_type_path,"r") as file:
		sp_pak_type = json.load(file)

def handle_plugin(folder):
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
					handle_depends(sp_pak_info["depends"], extra_includes, compile_later)
		
		handle_sp_folder(os.path.join(addons,"sourcemod/scripting"), extra_includes, sp_pak_info)

compile_later  =[]

if args.plu:
	for folder in args.plu:
		folder = os.path.join(cwd,folder)
		handle_plugin(folder)
else:
	for folder in cwd.glob("*"):
		if folder.is_file():
			continue
		if folder == "package":
			continue
		if folder == "scripts":
			continue
		handle_plugin(folder)
	
def handle_compile_later(compile_later):
	compile_later2 = []
	for dep, dep_path in compile_later:
		extra_includes = []
		sp_pak_info = None
		
		os.chdir(dep_path)
		
		path_map = None
		if "path_map" in dep:
			path_map = dep["path_map"]
		
		if path_map:
			if "addons/sourcemod/plugins" in path_map:
				folder = os.path.join(dep_path,path_map["addons/sourcemod/plugins"])
				shutil.rmtree(folder,ignore_errors=True)
			if "copy" in path_map:
				for key, value in path_map["copy"].items():
					folder = os.path.join(dep_path,key)
					target = os.path.join(pak,value)
					copy_folder(folder, target)
		
		if "sp_pak_info" in dep:
			sp_pak_info = dep["sp_pak_info"]
			if "depends" in sp_pak_info:
				handle_depends(sp_pak_info["depends"], extra_includes, compile_later2)
				
		if path_map:
			if "addons/sourcemod/scripting" in path_map:
				handle_sp_folder(os.path.join(dep_path,path_map["addons/sourcemod/scripting"]), extra_includes, sp_pak_info)
				
	if compile_later2:
		handle_compile_later(compile_later2)
	
handle_compile_later(compile_later)
	
shutil.rmtree(os.path.join(cwd,"tmp"),ignore_errors=True)

copy_folder(pak,game)
