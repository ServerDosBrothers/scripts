python clone.py -u USERNAME -t PERSONAL_TOKEN
python package.py -s SOURCEMOD_FOLDER

todos 2 tem que ser executado na pasta onde fica os repositorios

se o plugin depende de outros plugins o package.py n vai funcionar tem q criar um arquivo .sp_pak_info na pasta do git
exemplo

```
eventinho/.sp_pak_info
{
	"depends": [
		"teammanager"
	]
	"append_path": "svb/eventinho/"
}
```
