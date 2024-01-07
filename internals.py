#!/usr/bin/python3.9

from os import environ
from pathlib import Path
from sys import argv as sys_argv
from sys import platform as sys_platform

from yaml import dump as yaml_dump
from yaml import load as yaml_load
from yaml import Loader as yaml_Loader

_cached_gameslist=[]
_cached_config={}
_cached_game={}
_cached_state={}

def cached_config_update(data,clear_first=False):
	if clear_first:
		_cached_config.clear()
	_cached_config.update(data)

def cached_config_get(target):
	return _cached_config.get(target)

def get_sys_argv()->list:
	return sys_argv

def get_path_program()->Path:
	return Path(sys_argv[0]).resolve()

def get_sys_platform()->str:
	return sys_platform

def get_list_of_places()->list:

	os_platform=get_sys_platform()
	path_program_dir=get_path_program().parent

	places=[Path(".").absolute()]

	if os_platform=="linux":
		try:
			user_home=Path(environ.get("HOME"))
			if user_home not in places:
				places.append(user_home)
		except:
			pass

	if os_platform=="win32":
		try:
			user_home=Path(
				environ.get("HOMEDRIVE"),
				environ.get("HOMEPATH")
			)
			if user_home not in places:
				places.append(user_home)
		except:
			pass

		for letter in "abcdefghijglmnopqrstuvwxyz":
			point=Path(f"{letter.upper()}:/").absolute()
			if not point.exists():
				continue

			if point in places:
				continue

			places.append(point)

	if path_program_dir not in places:
		places.append(path_program_dir)

	return places

def get_path_real(path_offset:Path,fse:Path)->Path:

	if fse.is_absolute():
		return fse.resolve()

	return path_offset.joinpath(fse).resolve()

def util_yaml_read(filepath=None,text=None)->dict:

	has_file=(not (not filepath))
	has_text=(not (not text))

	content=None
	if (not has_file) and has_text:
		content=text
	if has_file and (not has_text):
		content=filepath.read_text()

	if not content:
		return {}

	data={}

	try:
		data.update(
			yaml_load(
				content,
				Loader=yaml_Loader
			)
		)
	except Exception as e:
		print("YAML read error:",str(e))
		return {}

	return data

def util_yaml_write(filepath,data)->bool:
	try:
		filepath.write_text(
			yaml_dump(
				data,
				sort_keys=False
			)
		)
	except Exception as e:
		print("YAML write error:",str(e))
		return False

	return True

def game_data_to_yaml(filepath,data)->bool:
	pass

def game_yaml_to_data(fse)->dict:
	data=util_yaml_read(filepath=fse)
	game_name=data.get("name")
	if not isinstance(game_name,str):
		return {}
	game_iwad=data.get("iwad")
	if not isinstance(game_iwad,str):
		return {}

	return data

def cached_game_save(filepath)->bool:
	return util_yaml_write(filepath,_cached_game)

def cached_game_update(data,clear_first=False):
	if clear_first:
		_cached_game.clear()

	_cached_game.update(data)

	return (len(_cached_game)>0)

def create_gameslist()->list:

	path_program=get_path_program()

	games=[]
	path_games=path_program.parent.joinpath(f"{path_program.stem}.games")
	if not path_games.is_dir():
		return []

	games=[]
	for fse in path_games.iterdir():
		if not fse.is_file():
			continue
		if fse.suffix.lower() not in (".yaml",".yml"):
			continue
		if fse.stat().st_size>1024*32:
			continue
		if not game_yaml_to_data(fse):
			continue
		games.append(fse)

	if len(games)>1:
		games.sort()

	return games

def update_gameslist(force:bool=False)->int:

	if len(_cached_gameslist)>0 and force:
		_cached_gameslist.clear()

	if len(_cached_gameslist)==0:
		_cached_gameslist.extend(create_gameslist())

	return len(_cached_gameslist)

def get_game_by_index(index:int)->Path:
	if len(_cached_gameslist)==0:
		update_gameslist()
	if not index<len(_cached_gameslist):
		return None
	return _cached_gameslist[index]

def program_config_read():

	path_program=get_path_program()
	path_config=path_program.parent.joinpath(f"{path_program.stem}.yaml")
	if not path_config.is_file():
		path_config=path_program.parent.joinpath(f"{path_program.stem}.yml")
	if not path_config.is_file():
		return

	_cached_config.update(
		util_yaml_read(filepath=path_config)
	)

	print(f"\nProgram config:\n\t{_cached_config}")

def program_config_write():

	print(f"Updating program configuration:\n{_cached_config}")

	path_program=get_path_program()
	util_yaml_write(
		path_program.parent.joinpath(
			f"{path_program.stem}.yaml"
		),
		_cached_config
	)

def get_path_srcport()->Path:

	path_srcport_str=_cached_config.get("path-srcport")
	if isinstance(path_srcport_str,str):
		path_program_dir=get_path_program().parent
		path_srcport=get_path_real(
			path_program_dir,
			Path(path_srcport_str)
		)
		if not path_srcport.is_file():
			return None

		return path_srcport

	return None

