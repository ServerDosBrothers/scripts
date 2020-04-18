import re, os, sys, argparse, pathlib, json, subprocess, shutil, distutils.dir_util, requests, copy, clone

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

remove_tmp = True
remove_pak = False
copy_pak = True
copy_game = False
gen_info = True

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

tmp_dir = os.path.join(cwd,"tmp")

base_sp_includes = [
	sm_scripting,
	sm_include,
]

base_sp_exec = spcomp + " -O2 -v0 -z9 "

base_update_url = "https://raw.githubusercontent.com/ServerDosBrothers/package/master"
post_update_url = "?token="

def find_define_value(code, define):
	pattern = "#\s*define\s+{}\s*".format(define)
	p = re.finditer(pattern, code)
	if p:
		for m in p:
			start = m.span()[1]
			if code[start] == '"':
				start += 1
				
			tpstr = ""
			i = start

			while True:
				if code[i:i-1] != "\\\"":
					if code[i] == '"':
						break
				tpstr += code[i]
				i += 1
				
			if code[i] == '"':
				return (tpstr,(start, i))
			else:
				return find_define_value(code, tpstr)
	return None

def replace_updateurl(code, gitfolder, plugin, update_url):
	code = code.replace("$$UPDATE_URL$$", update_url)
	p = re.finditer("Updater_AddPlugin\s*\(.*?,\s*", code)
	if p:
		for m in p:
			start = m.span()[1]
			quoted = False
			if code[start] == '"':
				quoted = True
			
			tpstr = ""
			i = start
			end = i
			while True:
				if quoted:
					if code[i:i-1] != "\\\"":
						if code[i] == '"':
							break
				else:
					if code[i] == ' ' or code[i] == '\t' or code[i] == '\r' or code[i] == '\n':
						i += 1
						continue
					if code[i] == ')':
						break
				tpstr += code[i]
				i += 1
				end = i
				
			was_define = False
				
			if quoted:
				tpstr = tpstr[1:-1]
			else:
				tpstr = find_define_value(code, tpstr)
				if tpstr is not None:
					was_define = True
					start = tpstr[1][0]
					end = tpstr[1][1]
					tpstr = tpstr[0]
				
			if tpstr is not None:
				if "SVB-" in gitfolder:
					tpstr = update_url
					code = code[:start] + tpstr + code[end:]
				plugin["update_url"] = tpstr
				
			if was_define:
				break
			else:
				print("not implemented")
				exit(1)
	return code

def replace_version(code, gitfolder, commit, plugin):
	was_commit = False
	if "$$GIT_COMMIT$$" in code:
		code = code.replace("$$GIT_COMMIT$$", commit)
		was_commit = True
	p = re.search("public\s+Plugin\s+myinfo\s*=\s*{(\s|.)*?version\s+=\s+", code)
	if p:
		start = p.span()[1]
		quoted = False
		if code[start] == '"':
			start += 1
			quoted = True
		
		tpstr = ""
		i = start
		end = i
		while True:
			if quoted:
				if code[i:i-1] != "\\\"":
					if code[i] == '"':
						break
			else:
				if code[i] == ' ' or code[i] == '\t' or code[i] == '\r' or code[i] == '\n':
					i += 1
					continue
				if code[i] == ',':
					break
			tpstr += code[i]
			i += 1
			end = i
			
		if quoted:
			tpstr = tpstr[1:-1]
		else:
			tpstr = find_define_value(code, tpstr)
			if tpstr is not None:
				start = tpstr[1][0]
				end = tpstr[1][1]
				tpstr = tpstr[0]
				
		if "SVB-" in gitfolder and tpstr is not None and not was_commit:
			if tpstr:
				tpstr = tpstr + "-" + commit
			else:
				tpstr = commit
			code = code[:start] + tpstr + code[end:]
			
		if tpstr is not None:
			plugin["version"] = tpstr
	return code

def handle_sp_folder(folder, extra_includes, sp_pak_info):
	folder = pathlib.Path(folder)
	gitfolder = os.path.basename(os.getcwd())
	plugins = []
	for file in folder.glob("*.sp"):
		file_basename = os.path.basename(file)
		if sp_pak_info:
			if "ignore_plugins" in sp_pak_info:
				if file_basename in sp_pak_info["ignore_plugins"]:
					continue
		plugin = {}
		print("Compiling " + file_basename + " from " + gitfolder)
		code = ""
		newfile_path = os.path.join(tmp_dir,file_basename)
		file_basename = os.path.splitext(file_basename)[0]
		if sp_pak_info:
			if "name_append" in sp_pak_info:
				file_basename = sp_pak_info["name_append"] + file_basename
		with open(file,"r") as newfile:
			code = newfile.read()
		commit = ""
		if os.path.exists(os.path.join(os.getcwd(), ".git")):
			commit = subprocess.check_output("git rev-parse HEAD", shell=True,cwd=os.getcwd())
			commit = commit[:-1]
			commit = commit.decode("utf-8")
			note = subprocess.check_output("git log -1 --pretty=format:%B", shell=True,cwd=os.getcwd())
			note = note[:-1]
			note = note.decode("utf-8")
			plugin["note"] = note
		else:
			commit = "Unknown"
		code = replace_version(code, gitfolder, commit, plugin)
		update_url = os.path.join(base_update_url, file_basename + ".txt") + post_update_url
		code = replace_updateurl(code, gitfolder, plugin, update_url)
		with open(newfile_path,"w") as newfile:
			newfile.write(code)
		file_folder = file.parent
		includes = [file_folder]
		for extra in folder.glob("*"):
			if extra.is_file():
				continue
			includes.append(extra)
		includes += extra_includes + base_sp_includes
		includes_str = ""
		for inc in includes:
			includes_str += "-i \"" + str(inc) + "\" "
		extra_path = ""
		if "SVB-" in gitfolder:
			extra_path = os.path.join(extra_path,"svb")
		else:
			extra_path = os.path.join(extra_path,"thirdparty")
		extra_flags = ""
		if sp_pak_info:
			if "path_append" in sp_pak_info:
				extra_path = os.path.join(extra_path,sp_pak_info["path_append"])
			if "disable_warnings" in sp_pak_info:
				for warn in sp_pak_info["disable_warnings"]:
					extra_flags += "-w" + str(warn) + ' '
			if "warning_errors" in sp_pak_info:
				if sp_pak_info["warning_errors"] == True:
					extra_flags += "-E "
			if "defines" in sp_pak_info:
				for define, value in sp_pak_info["defines"].items():
					extra_flags += define + '=' + value + ' '
		plugin["name"] = file_basename
		output_path = os.path.join(pak_plugins,extra_path,file_basename+".smx")
		plugin["path"] = output_path
		if not os.path.exists(output_path):
			tmp_path = output_path
		else:
			tmp_path = os.path.join(tmp_dir,extra_path,file_basename+".smx")
		os.makedirs(pathlib.Path(tmp_path).parent, exist_ok=True)
		exec = base_sp_exec + "\"" + str(newfile_path) + "\" -o \"" + tmp_path + "\" " + includes_str + extra_flags
		exec += defines
		stdout = subprocess.check_output(exec, shell=True,cwd=os.getcwd())
		stdout = stdout[:-1]
		stdout = stdout.decode("utf-8")
		idx = stdout.find("Code size:")
		if idx:
			stdout = stdout[:idx-1]
			print(stdout)
		if tmp_path != output_path:
			changed = True
			'''
			with open(output_path, "rb") as old_file:
				old_data = old_file.read()
				with open(tmp_path, "rb") as new_file:
					new_data = new_file.read()
					i = 0
					while True:
						if i >= len(old_data) or i >= len(new_data):
							break
						print(old_data[i] == new_data[i])
						i += 1
			'''
			if changed:
				os.remove(output_path)
				shutil.copy(tmp_path, output_path)
		if remove_tmp:
			os.remove(newfile_path)
		plugins.append(plugin)
	return plugins

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
					clone.clone(dep["url"], dep_path)
					if "path_map" in dep:
						path_map = dep["path_map"]
						if "addons/sourcemod/scripting/include" in path_map:
							extra_includes += [os.path.join(dep_path, path_map["addons/sourcemod/scripting/include"])]
					compile_later += [(dep,dep_path)]
		if is_root_repo:
			extra_includes += [os.path.join(cwd,depend,"addons/sourcemod/scripting/include")]

def handle_plugin(folder):
	folder = pathlib.Path(folder)
	addons = os.path.join(folder,"addons")
	if os.path.exists(addons):
		os.chdir(folder)
		
		if copy_pak:
			copy_folder(folder, pak)
		
		files = []
		for file in folder.glob("**/*"):
			if not file.is_file():
				continue
			basename = os.path.basename(file)
			if basename[0] == '.':
				continue
			if basename == "LICENSE":
				continue
			split = os.path.splitext(basename)
			if split[0] == "README":
				continue
			if ".git" in str(file):
				continue
			if split[1] == ".inc" or split[1] == ".sp":
				continue
			files.append(file)
		
		sp_pak_info = None
		sp_pak_info_path = os.path.join(folder,".sp_pak_info")
		extra_includes = []
		if os.path.exists(sp_pak_info_path):
			with open(sp_pak_info_path,"r") as file:
				sp_pak_info = json.load(file)
				if "depends" in sp_pak_info:
					handle_depends(sp_pak_info["depends"], extra_includes, compile_later)
		
		plugins = handle_sp_folder(os.path.join(addons,"sourcemod/scripting"), extra_includes, sp_pak_info)
		if plugins:
			for plugin in plugins:
				newfiles = copy.deepcopy(files)
				smxpath = plugin["path"]
				smxpath = smxpath.replace(pak,"")
				newfiles.append(smxpath)
				plugin_version = ""
				if "version" in plugin:
					plugin_version = plugin["version"]
				plugin_note = ""
				if "note" in plugin:
					plugin_note = plugin["note"]
				updater_str = "\"Updater\"\n{{\n\t\"Information\"\n\t{{\n\t\t\"Version\"\n\t\t{{\n\t\t\t\"Latest\" \"{}\"\n\t\t}}\n\t\t\"Notes\" \"{}\"\n\t}}\n\t\"Files\"\n\t{{\n".format(plugin_version,plugin_note)
				for file in newfiles:
					file = str(file).replace(str(folder), "")
					ext = os.path.splitext(file)[1]
					file_type = ""
					if ext == ".inc" or ext == ".sp":
						file_type = "Source"
					else:
						file_type = "Plugin"
					updater_str += "\t\t\"{}\" \"Path_Mod{}\"\n".format(file_type,file)
				updater_str += "\n\t}\n}"
				update_path = os.path.join(pak,plugin["name"]+".txt")
				with open(update_path,"w") as update:
					update.write(updater_str)
			return plugins
	return None

thirdparty = os.path.join(cwd,"thirdparty")
os.makedirs(thirdparty,exist_ok=True)
os.makedirs(tmp_dir,exist_ok=True)
if remove_pak:
	shutil.rmtree(pak,ignore_errors=True)

sp_pak_type = None
sp_pak_type_path = os.path.join(cwd,"scripts/.sp_pak_type")
if os.path.exists(sp_pak_type_path):
	with open(sp_pak_type_path,"r") as file:
		sp_pak_type = json.load(file)

compile_later = []
all_plugins = []

if args.plu:
	for folder in args.plu:
		folder = os.path.join(cwd,folder)
		plugins = handle_plugin(folder)
		if plugins:
			all_plugins += plugins
else:
	for folder in cwd.glob("*"):
		if folder.is_file():
			continue
		if folder == "package":
			continue
		if folder == "scripts":
			continue
		plugins = handle_plugin(folder)
		if plugins:
			all_plugins += plugins
	
def handle_compile_later(compile_later):
	compile_later2 = []
	all_plugins2 = []
	
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
			if copy_pak:
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
				plugins = handle_sp_folder(os.path.join(dep_path,path_map["addons/sourcemod/scripting"]), extra_includes, sp_pak_info)
				if plugins:
					all_plugins2 += plugins
				
	if compile_later2:
		plugins2 = handle_compile_later(compile_later2)
		if plugins2:
			all_plugins2 += plugins2
			
	if all_plugins2:
		return all_plugins2
	else:
		return None
	
plugins = handle_compile_later(compile_later)
if plugins:
	all_plugins += plugins

shutil.rmtree(os.path.join(pak,"addons/sourcemod/scripting"),ignore_errors=True)

if gen_info:
	info_str = ""
	for plugin in all_plugins:
		info_str += plugin["name"] + '\n'
		info_str += "{\n\t"
		if "version" in plugin:
			info_str += "version: \"" + plugin["version"] + "\""
			info_str += "\n\t"
		if "update_url" in plugin:
			info_str += "update_url: \"" + plugin["update_url"] + "\""
			info_str += "\n\t"
		info_str = info_str[:-2]
		info_str += "\n}\n"
	info_path = os.path.join(pak,"info.txt")
	with open(info_path,"w") as info:
		info.write(info_str)

if remove_tmp:
	shutil.rmtree(tmp_dir,ignore_errors=True)

if copy_game:
	copy_folder(pak,game)
