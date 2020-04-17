import os, sys, argparse, pathlib, ftplib

parser = argparse.ArgumentParser()
parser.add_argument("-u", action="store", required=True, dest="usr")
parser.add_argument("-p", action="store", required=True, dest="pwd")
parser.add_argument("-s", action="store", required=True, dest="sv")
parser.add_argument("-f", action="store", required=True, dest="fldr")
args = parser.parse_args()

folder = pathlib.Path(args.fldr)

def upload(ftp, src, dst):
	src = pathlib.Path(src)
	if dst in [name for name, data in list(ftp.mlsd())]:
		ftp.mkd(dst)
	ftp.cwd(dst)
	if os.path.isfile(src):
		with open(src, "rb") as file:
			ftp.storbinary(f'STOR {src.name}', file)

with ftplib.FTP(args.sv, args.usr, args.pwd) as ftp:
	for file in folder.glob("**/*"):
		if not file.is_file():
			continue
		basepath = str(file.parent).replace(str(folder),"")
		dst = "tf" + basepath
		upload(ftp, file, dst)
