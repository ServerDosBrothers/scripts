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

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", action="store",default=os.path.join(cwd,"server"),required=False, dest="fldr")
	args = parser.parse_args()
	
	serv = args.fldr
	serv = os.path.abspath(serv)
	os.makedirs(serv,exist_ok=True)
	
	steamcmd_dir = os.path.join(serv,"steamcmd")
	os.makedirs(steamcmd_dir,exist_ok=True)
	
	sources=os.path.join(serv,"sources")
	
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
	#subprocess.run(steamcmd_sh + " +login anonymous +force_install_dir \"" + install_dir + "\" +app_update 232250 +quit",shell=True,cwd=os.getcwd())
	
	steamworks_dir = os.path.join(sources,"steamworks_sdk")
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
	
	repos = [
		("https://github.com/alliedmodders/ambuild.git",),
		("https://github.com/alliedmodders/hl2sdk.git","sdk2013","hl2sdk-sdk2013"),
		("https://github.com/alliedmodders/hl2sdk.git","tf2","hl2sdk-tf2"),
		("https://github.com/alliedmodders/metamod-source.git",),
		("https://github.com/alliedmodders/sourcemod.git",),
		("https://github.com/TheByKotik/sendproxy.git",),
		("https://github.com/ErikMinekus/sm-ripext.git",),
		("https://github.com/asherkin/TF2Items.git",),
		("https://github.com/KyleSanderson/SteamWorks.git",),
		("https://github.com/PerfectLaugh/dhooks2-dynhooks.git",),
	]
	
	for repo in repos:
		url = repo[0]
		name = os.path.splitext(os.path.basename(url))[0]
		branch = "master"
		if len(repo) >= 3:
			name = repo[2]
		if len(repo) >= 2:
			branch = repo[1]
		path = os.path.join(sources,name)
		clone.clone(url,path,branch)
		
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
	
	debug = False
	optimize_flag = "--enable-debug" if debug else "--enable-optimize"
	
	base_args = optimize_flag + " --sdks=tf2 --hl2sdk-root=\"" + sources + "\" "
	base_args_ext = base_args + "--mms-path=\"" + mmsource_src_dir + "\" --sm-path=\"" + sourcemod_src_dir + "\" "
	base_args_ext_nogame = optimize_flag + " --mms-path=\"" + mmsource_src_dir + "\" --sm-path=\"" + sourcemod_src_dir + "\" "
	
	os.chdir(mmsource_src_dir)
	build_ambuild2(base_args)
	
	os.chdir(sourcemod_src_dir)
	build_ambuild2(base_args + "--mms-path=\"" + mmsource_src_dir + "\" --no-mysql --disable-auto-versioning")
	
	sendproxy_src_dir = os.path.join(sources,"sendproxy")
	os.chdir(os.path.join(sendproxy_src_dir,"extension"))
	build_ambuild2(base_args_ext)
	
	sm_ripext_src_dir = os.path.join(sources,"sm-ripext")
	os.chdir(sm_ripext_src_dir)
	build_ambuild2(base_args_ext)
	
	tf2items_src_dir = os.path.join(sources,"TF2Items")
	os.chdir(tf2items_src_dir)
	build_ambuild1(optimize_flag)
	
	steamworks_src_dir = os.path.join(sources,"SteamWorks")
	os.chdir(steamworks_src_dir)
	build_ambuild2(base_args_ext.replace("--sdks=tf2","--sdks=sdk2013"))
	
	dhooks_src_dir = os.path.join(sources,"dhooks2-dynhooks")
	os.chdir(dhooks_src_dir)
	build_ambuild2(base_args_ext_nogame)
	
	package.copy_folder(os.path.join(mmsource_src_dir,"build/package"),game)
	package.copy_folder(os.path.join(sourcemod_src_dir,"build/package"),game)
	package.copy_folder(os.path.join(sourcemod_src_dir,"addons"),os.path.join(game,"addons"))
	package.copy_folder(os.path.join(sendproxy_src_dir,"extension/build/package"),game)
	package.copy_folder(os.path.join(sm_ripext_src_dir,"build/package"),game)
	package.copy_folder(os.path.join(tf2items_src_dir,"build/package"),game)
	package.copy_folder(os.path.join(steamworks_src_dir,"build/package"),game)
	package.copy_folder(os.path.join(dhooks_src_dir,"build/package"),game)
	
	os.chdir(cwd)
	#os.system()
	
	
	
	
	
	
	
	
	
	
	
	
	
	
