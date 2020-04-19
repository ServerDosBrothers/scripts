import os, sys, argparse, pathlib, subprocess, clone, package

cwd = pathlib.Path(os.getcwd())

def configure(args=""):
	tmp_cwd = os.getcwd()
	build_dir = os.path.join(tmp_cwd,"build")
	os.makedirs(build_dir,exist_ok=True)
	os.chdir(build_dir)
	subprocess.run("python ../configure.py " + args,shell=True,cwd=os.getcwd(),env=os.environ)
	return build_dir
	
def build_ambuild2(args=""):
	build_dir = configure(args)
	os.chdir(build_dir)
	subprocess.run("ambuild",shell=True,cwd=os.getcwd(),env=os.environ)
	os.chdir(cwd)

def build_ambuild1(args=""):
	build_dir = configure(args)
	os.chdir(build_dir)
	subprocess.run("python build.py",shell=True,cwd=os.getcwd(),env=os.environ)
	os.chdir(cwd)

def clone_repo(repo):
	url = repo[0]
	name = os.path.splitext(os.path.basename(url))[0]
	branch = "master"
	if len(repo) >= 3:
		name = repo[2]
	if len(repo) >= 2:
		branch = repo[1]
	path = os.path.join(sources,name)
	clone.clone(url,path,branch)

def handle_ext(ext):
	repo = None
	steamworks_dir = os.path.join(sources,"steamworks_sdk")
	if ext == "SteamWorks":
		if not os.path.exists(os.path.join(steamworks_dir,"sdk")):
			#url="https://partner.steamgames.com/downloads/steamworks_sdk.zip"
			#clone.handle_wget(url, steamworks_dir)
			#name = os.path.basename(url)
			name = "steamworks_sdk_148a.zip"
			zip=os.path.join(steamworks_dir,name)
			if not os.path.exists(zip):
				print("tem q baixar o sdk separado no url acima")
				exit(1)
			os.chdir(steamworks_dir)
			subprocess.run("unzip -q \""+zip+"\"",shell=True,cwd=os.getcwd())
			
		repo = ("https://github.com/KyleSanderson/SteamWorks.git",)
	elif ext == "metamod-source":
		repo = ("https://github.com/alliedmodders/metamod-source.git",)
	elif ext == "sourcemod":
		repo = ("https://github.com/alliedmodders/sourcemod.git",)
	elif ext == "sendproxy":
		repo = ("https://github.com/TheByKotik/sendproxy.git",)
	elif ext == "sm-ripext":
		repo = ("https://github.com/ErikMinekus/sm-ripext.git",)
	elif ext == "TF2Items":
		repo = ("https://github.com/asherkin/TF2Items.git",)
	elif ext == "dhooks2-dynhooks":
		repo = ("https://github.com/PerfectLaugh/dhooks2-dynhooks.git",)
	
	if repo is None:
		return

	clone_repo(repo)
	
	sourcemod_src_dir = os.path.join(sources,"sourcemod")
	mmsource_src_dir = os.path.join(sources,"metamod-source")
	hl2sdk_dir = os.path.join(sources,"hl2sdk-tf2")
		
	os.environ["SOURCEMOD14"] = sourcemod_src_dir
	os.environ["SOURCEMOD16"] = sourcemod_src_dir
	os.environ["SOURCEMOD"] = sourcemod_src_dir
	os.environ["SMCENTRAL"] = sourcemod_src_dir
	
	os.environ["MMSOURCE19"] = mmsource_src_dir
	os.environ["MMSOURCE18"] = mmsource_src_dir
	os.environ["MMSOURCE10"] = mmsource_src_dir
	os.environ["MMSOURCE110"] = mmsource_src_dir
	os.environ["MMSOURCE_DEV"] = mmsource_src_dir
	
	os.environ["HL2SDK"] = hl2sdk_dir
	os.environ["HL2SDKOB"] = hl2sdk_dir
	os.environ["HL2SDKOBVALVE"] = hl2sdk_dir
	os.environ["HL2SDKTF2"] = hl2sdk_dir
	os.environ["HL2SDK2013"] = hl2sdk_dir
	
	os.environ["STEAMWORKS"] = os.path.join(steamworks_dir,"sdk")
	
	os.environ["CC"] = "gcc"
	os.environ["CXX"] = "g++"
	os.environ["CFLAGS"] = "-w -Wno-error -Wno-format-truncation -Wno-stringop-overflow -Wno-stringop-truncation -Wno-expansion-to-defined -Wno-address-of-packed-member"
	os.environ["CXXFLAGS"] = "-fpermissive -Wno-class-memaccess"
	
	os.chdir(os.path.join(sources,"ambuild"))
	#subprocess.run("sudo python setup.py install",shell=True,cwd=os.getcwd(),env=os.environ)
	
	optimize_flag = "--enable-debug" if debug else "--enable-optimize"
	
	base_args = optimize_flag + " --sdks=tf2 --hl2sdk-root=\"" + sources + "\" "
	base_args_ext = base_args + "--mms-path=\"" + mmsource_src_dir + "\" --sm-path=\"" + sourcemod_src_dir + "\" "
	base_args_ext_nogame = optimize_flag + " --mms-path=\"" + mmsource_src_dir + "\" --sm-path=\"" + sourcemod_src_dir + "\" "

	if ext == "sourcemod":
		os.chdir(sourcemod_src_dir)
		build_ambuild2(base_args + "--mms-path=\"" + mmsource_src_dir + "\" --no-mysql --disable-auto-versioning")
		package.copy_folder(os.path.join(sourcemod_src_dir,"build/package"),game)
	elif ext == "metamod-source":
		os.chdir(mmsource_src_dir)
		build_ambuild2(base_args)
		package.copy_folder(os.path.join(mmsource_src_dir,"build/package"),game)
	elif ext == "sendproxy":
		sendproxy_src_dir = os.path.join(sources,"sendproxy")
		os.chdir(os.path.join(sendproxy_src_dir,"extension"))
		build_ambuild2(base_args_ext)
		package.copy_folder(os.path.join(sendproxy_src_dir,"addons/sourcemod/gamedata"),os.path.join(game,"addons/sourcemod/gamedata"))
		package.copy_folder(os.path.join(sendproxy_src_dir,"extension/build/package"),game)
	elif ext == "sm-ripext":
		sm_ripext_src_dir = os.path.join(sources,"sm-ripext")
		os.chdir(sm_ripext_src_dir)
		build_ambuild2(base_args_ext)
		package.copy_folder(os.path.join(sm_ripext_src_dir,"build/package"),game)
	elif ext == "TF2Items":
		tf2items_src_dir = os.path.join(sources,"TF2Items")
		os.chdir(tf2items_src_dir)
		build_ambuild1(optimize_flag)
		package.copy_folder(os.path.join(tf2items_src_dir,"build/package"),game)
	elif ext == "SteamWorks":
		steamworks_src_dir = os.path.join(sources,"SteamWorks")
		os.chdir(steamworks_src_dir)
		build_ambuild2(base_args_ext.replace("--sdks=tf2","--sdks=sdk2013"))
		package.copy_folder(os.path.join(steamworks_src_dir,"build/package"),game)
	elif ext == "dhooks2-dynhooks":
		dhooks_src_dir = os.path.join(sources,"dhooks2-dynhooks")
		os.chdir(dhooks_src_dir)
		build_ambuild2(base_args_ext_nogame)
		package.copy_folder(os.path.join(dhooks_src_dir,"build/package"),game)

def handle_exts(exts):
	clone_repo(("https://github.com/alliedmodders/ambuild.git",))
	clone_repo(("https://github.com/alliedmodders/hl2sdk.git","sdk2013","hl2sdk-sdk2013"))
	clone_repo(("https://github.com/alliedmodders/hl2sdk.git","tf2","hl2sdk-tf2"))
	
	os.chdir(os.path.join(sources,"ambuild"))
	#subprocess.run("sudo python setup.py install",shell=True,cwd=os.getcwd(),env=os.environ)
	
	if not exts:
		exts = [
			"sourcemod",
			"metamod-source",
			"sendproxy",
			"sm-ripext",
			"TF2Items",
			"SteamWorks",
			"dhooks2-dynhooks",
		]
	
	for ext in exts:
		handle_ext(ext)

def handle_plugins(plugins):
	sourcemod_dir = os.path.join(game,"addons/sourcemod")
	
	plugins_str=""
	for plugin in plugins:
		plugins_str+= plugin + ' '
	
	defines = []
	if debug:
		defines += ["DEBUG"]
	
	defines_str = ""
	for define in defines:
		defines_str += define + ' '
	
	os.chdir(cwd)
	exec = "python \"scripts/package.py\" -s \"" + sourcemod_dir + "\" -f \"" + game + "\" -p " + plugins_str + " -d " + defines_str
	subprocess.run(exec,shell=True,cwd=os.getcwd())

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", action="store",default=os.path.join(cwd,"server"),required=False, dest="fldr")
	parser.add_argument("-e", action="store",nargs="*",required=False, dest="ext")
	parser.add_argument("-p", action="store",nargs="*",required=False, dest="plu")
	parser.add_argument("-d", action="store_true",required=False, dest="deb")
	parser.add_argument("-f", action="store_true",required=False, dest="fst")
	parser.add_argument("-i", action="store_true",required=False, dest="ins")
	args = parser.parse_args()
	
	all_exts = False
	if args.ext:
		all_exts = args.ext[0] == "all"
	
	all_plugins = False
	if args.plu:
		all_plugins = args.plu[0] == "all"
	
	if all_exts:
		args.ext = []
	
	if all_plugins:
		args.plu = []
	
	serv = args.fldr
	serv = os.path.abspath(serv)
	os.makedirs(serv,exist_ok=True)
	
	sources=os.path.join(serv,"sources")
	
	if args.ins:
		steamcmd_dir = os.path.join(serv,"steamcmd")
		os.makedirs(steamcmd_dir,exist_ok=True)
		
		steamcmd_sh = os.path.join(steamcmd_dir,"steamcmd.sh")
		if not os.path.exists(steamcmd_sh):
			url="https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
			clone.handle_wget(url, steamcmd_dir)
			zip=os.path.join(steamcmd_dir,os.path.basename(url))
			os.chdir(steamcmd_dir)
			subprocess.run("tar zxvf \""+zip+"\"",shell=True,cwd=os.getcwd())
			os.remove(zip)
	
	install_dir=os.path.join(serv,"serverfiles")
	game = os.path.join(install_dir,"tf")
	
	debug = args.deb
	
	if args.ext is not None:
		handle_exts(args.ext)
	if args.plu is not None:
		handle_plugins(args.plu)

	if args.fst:
		fastdl = os.path.join(serv,"fastdl")
		game = pathlib.Path(game)
		folders = [
			"models",
			"maps",
			"materials",
			"sound",
			"scripts",
		]
		for folder in folders:
			path = os.path.join(folder, "**/*")
			for file in game.glob(path):
				if not file.is_file():
					continue
				exec = "bzip2 \"" + str(file) + "\" -k --best -f -z"
				subprocess.run(exec,shell=True,cwd=os.getcwd())
				oldpath = str(file)
				oldpath += ".bz2"
				newpath = str(file).replace(str(game),"")
				newpath = newpath[1:]
				print(newpath)
				newpath = os.path.join(fastdl, newpath)
				newpath += ".bz2"
				os.makedirs(pathlib.Path(newpath).parent,exist_ok=True)
				os.rename(oldpath,newpath)

	if args.ins:
		subprocess.run(steamcmd_sh + " +login anonymous +force_install_dir \"" + install_dir + "\" +app_update 232250 +quit",shell=True,cwd=os.getcwd())
