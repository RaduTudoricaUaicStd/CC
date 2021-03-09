from json import loads
from pymongo import MongoClient

DB = MongoClient().cc_tema2

attributes = {
	"series":[
		"name",
		"creator",
		"available_on",
		"imdb_rating",
		"imdb_id"
	],
	"episodes":[
		"name",
		"season",
		"runtime",
		"imdb_rating",
		"imdb_id"
	]
}

def get_collection_series(request):
	series = []
	for s in list(DB.series.find({})):
		del s["_id"]
		series.append(s)
	return {
		"code": 200,
		"data": {
			"status": True,
			"series": series
		}
	}


def get_series(request):
	name = request.path.replace("/series/", "")
	series = DB.series.find_one({"name":name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"series": "no series with the name \""+name+"\" was found"
			}
		}
	else:
		del series["_id"]
		return {
			"code": 200,
			"data": {
				"status": True,
				"series": series
			}
		}

def get_collection_episodes(request):
	_, _, series_name, _ = request.path.split("/")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"error": "no series named \"" + name + "\" was found in the database"
			}
		}
	return {
		"code": 200,
		"data": {
			"status": True,
			"episodes": series["episodes"]
		}
	}

def get_episode(request):
	_, _, series_name, _, episode_name = request.path.split("/")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"error": "no series named \"" + series_name + "\" was found in the database"
			}
		}
	for episode in series["episodes"]:
		if episode["name"] == episode_name:
			return {
				"code": 200,
				"data": {
					"status": True,
					"episode": episode
				}
			}
	return {
		"code": 404,
		"data": {
			"status": False,
			"error": "no episode named \""+episode_name+"\" in the series named \""+series_name+"\""
		}
	}

def post_collection_series(request):
	posted_series = request.rfile.read(int(request.headers["Content-Length"])).decode('utf-8')
	try:
		posted_series = loads(posted_series)
	except:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "invalid json format sent"
			}
		}
	if not "Location" in request.headers:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "location header not sent"
			}
		}
	series_name = request.headers["Location"].replace("/series/", "")
	if not DB.series.find_one({"name":series_name}) is None:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "series already exists"
			}
		}
	series = {
		"episodes":[]
	}
	for attribute in attributes["series"]:
		if not attribute in posted_series:
			return {
			"code": 400,
			"data": {
				"status": False,
				"error": "field \"" + attribute + "\" not found in the posted json"
			}
		}
		series[attribute] = posted_series[attribute]
	DB.series.insert_one(series)
	return {
		"code": 200,
		"data": {
			"status": True,
			"message": "series \"" + series["name"] + "\" was added to the database"
		}
	}



def post_series(request):
	name = request.path.replace("/series/", "")
	series = DB.series.find_one({"name":name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"series": "no series with the name \""+name+"\" was found"
			}
		}
	else:
		return {
			"code": 409,
			"data": {
				"status": True,
				"error": "series already exists"
			}
		}

def post_collection_episodes(request):
	posted_episodes = request.rfile.read(int(request.headers["Content-Length"])).decode('utf-8')
	try:
		posted_episodes = loads(posted_episodes)
	except:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "invalid json format sent"
			}
		}
	if not "Location" in request.headers:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "location header not sent"
			}
		}
	_, _, series_name, _, episode_name = request.headers["Location"].split("/")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "the series doesn't exist"
			}
		}

	if len([ episode for episode in series["episodes"] if episode["name"] == episode_name ]) != 0:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "episode already exists"
			}
		}

	episode = {}
	for attribute in attributes["episodes"]:
		if not attribute in posted_episodes:
			return {
			"code": 400,
			"data": {
				"status": False,
				"error": "field \"" + attribute + "\" not found in the posted json"
			}
		}
		episode[attribute] = posted_episodes[attribute]
	series["episodes"].append(episode)
	DB.series.update_one({"name":series_name}, {"$set":{"episodes":series["episodes"]}})
	return {
		"code": 200,
		"data": {
			"status": True,
			"message": "the episode \"" + episode["name"] + "\" was added to the database"
		}
	}

def post_episode(request):
	_, _, series_name, _, episode_name = request.path.split("/")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"error": "no series named \"" + series_name + "\" was found in the database"
			}
		}
	for episode in series["episodes"]:
		if episode["name"] == episode_name:
			return {
				"code": 409,
				"data": {
					"status": False,
					"episode": "episode already exists"
				}
			}
	return {
		"code": 404,
		"data": {
			"status": False,
			"error": "no episode named \""+episode_name+"\" in the series named \""+series_name+"\""
		}
	}

def put_collection_series(request):
	return {
		"code": 405,
		"data": {
			"status": False,
			"error": "method not allowed, cannot update or replace every series in the collection"
		}
	}

def put_series(request):
	posted_series = request.rfile.read(int(request.headers["Content-Length"])).decode('utf-8')
	try:
		posted_series = loads(posted_series)
	except:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "invalid json format sent"
			}
		}
	series_name = request.path.replace("/series/", "")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "series doesn't exist"
			}
		}
	for attribute in attributes["series"]:
		if attribute in posted_series:
			DB.series.update_one({"name": series_name}, {"$set":{attribute: posted_series[attribute]}})
	return {
		"code": 200,
		"data": {
			"status": True,
			"message": "series \"" + series["name"] + "\" was updated"
		}
	}

def put_collection_episodes(request):
	return {
		"code": 405,
		"data": {
			"status": False,
			"error": "method not allowed, cannot update or replace every episode in the series"
		}
	}

def put_episode(request):
	posted_episodes = request.rfile.read(int(request.headers["Content-Length"])).decode('utf-8')
	try:
		posted_episodes = loads(posted_episodes)
	except:
		return {
			"code": 400,
			"data": {
				"status": False,
				"error": "invalid json format sent"
			}
		}
	_, _, series_name, _, episode_name = request.path.split("/")
	series = DB.series.find_one({"name":series_name})
	if series is None:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "the series doesn't exist"
			}
		}

	if len([ episode for episode in series["episodes"] if episode["name"] == episode_name ]) != 1:
		return {
			"code": 405,
			"data": {
				"status": False,
				"error": "the episode doesn't exist"
			}
		}

	for i in range(len(series["episodes"])):
		if series["episodes"][i]["name"] != episode_name:
			continue
		for attribute in attributes["episodes"]:
			if attribute in posted_episodes:
				series["episodes"][i][attribute] = posted_episodes[attribute]
		break
	DB.series.update_one({"name":series_name}, {"$set":{"episodes":series["episodes"]}})
	return {
		"code": 200,
		"data": {
			"status": True,
			"message": "the episode was updated"
		}
	}

def delete_collection_series(request):
	return {
		"code": 405,
		"data": {
			"status": False,
			"error": "method not allowed, cannot delete every series in the collection"
		}
	}

def delete_series(request):
	name = request.path.replace("/series/", "")
	if DB.series.delete_one({"name": name}).deleted_count == 1:
		return {
			"code": 200,
			"data": {
				"status": True,
				"message": "series \""+name+"\" was deleted with success"
			}
		}
	else:
		return {
			"code": 404,
			"data": {
				"status": False,
				"error": "series \""+name+"\" was not found"
			}
		}

def delete_collection_episodes(request):
	return {
		"code": 405,
		"data": {
			"status": False,
			"error": "method not allowed, cannot delete every episode in the series"
		}
	}

def delete_episode(request):
	_, _, series_name, _, episode_name = request.path.split("/")
	series = DB.series.find_one({"name": series_name})
	if series is None:
		return {
			"code": 404,
			"data": {
				"status": False,
				"error": "no series named \""+series_name+"\" was found"
			}
		}
	for i in range(len(series["episodes"])):
		episode = series["episodes"][i]
		if episode["name"] == episode_name:
			del series["episodes"][i]
			if DB.series.update_one({"name": series_name}, {"$set":{"episodes":series["episodes"]}}).modified_count == 1:
				return {
					"code": 200,
					"data": {
						"status": True,
						"message": "deleted episode named \""+episode_name+"\" from the seares named \""+series_name+"\""
					}
				}
			else:
				return {
					"code": 500,
					"data":{
						"status": False,
						"error": "the database could not be modified"
					}
				}

