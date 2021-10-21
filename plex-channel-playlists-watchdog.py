# import yaml package
try:
    from ruamel.yaml import YAML
except:
    print("No python module named 'ruamel' found.")
# import plexapi package
try:
    from plexapi.server import PlexServer
except ImportError:
    print("No python module named 'plexapi' found.")

# main
print("-------------------------------\nPlex Channel-Playlists Watchdog\n-------------------------------")

# load yaml config
yaml = YAML(typ="safe")
yaml.default_flow_style = False
with open("config.yaml", "r") as config_file:
    config_yaml = yaml.load(config_file)
playlist_title = config_yaml["settings"]["playlist_title"]
plex_url = config_yaml["plex"]["plex_url"]
plex_libraryname = config_yaml["plex"]["plex_libraryname"]
plex_user_token = config_yaml["plex"]["plex_user_token"]

# connect to plex server
user_plex = PlexServer(plex_url, plex_user_token)

# remove first playlist item if it is currently playing (in progress)
series_library = user_plex.library.section(plex_libraryname)
my_playlist = series_library.playlist(playlist_title)
first_item = my_playlist.items()[0]
search_results = series_library.search(filters={"inProgress": "True"}, libtype="episode")
for episode in search_results:
    if episode.ratingKey == first_item.ratingKey:
        my_playlist.removeItems([first_item])
        print("Removed episode: " + str(first_item.grandparentTitle) + " - S" + str(first_item.parentIndex).zfill(2) + "E" + str(first_item.index).zfill(2) + " - " + str(first_item.title))

print("Done!")