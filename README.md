python clone.py -u USERNAME -t PERSONAL_TOKEN  
python package.py -s SOURCEMOD_FOLDER  
python upload.py -u USERNAME -p PASSWORD -s SERVER -f FOLDER  

todos scripts tem que ser executados na pasta onde fica os repositorios  

se o plugin depende de outros plugins o package.py n vai funcionar ai tem q criar um arquivo .sp_pak_info na pasta do git  
exemplo  

eventinho/.sp_pak_info  
```
{
	"depends": [
		"teammanager",
		"https://www.doctormckay.com/download/scripting/include/morecolors.inc"
	]
	"name_append": "svb/eventinho/"
}
```  

"name_append" adiciona a string ao nome do plugin qndo compilado  
