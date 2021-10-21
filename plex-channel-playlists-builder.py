import io, math
from objects.ShowObj import ShowObj
# import yaml package
try:
    from ruamel.yaml import YAML
except:
    print("No python module named 'ruamel' found.")
# import plexapi package
try:
    from plexapi.server import PlexServer
    from plexapi.playlist import Playlist
    from plexapi.exceptions import NotFound
except ImportError:
    print("No python module named 'plexapi' found.")

def ConnectPlexUser(plex_url: str, plex_token: str, plex_username: str):
    print("\nConnecting to Plex server with user profile.\n")
    try:
        main_plex = PlexServer(plex_url, plex_token)
        main_account = main_plex.myPlexAccount()
        user_account = main_account.user(plex_username)
        user_plex = PlexServer(plex_url, user_account.get_token(main_plex.machineIdentifier))
        print("Plex User Token is: " + user_account.get_token(main_plex.machineIdentifier))
        return user_plex, user_account.get_token(main_plex.machineIdentifier)
    except Exception:
        print("Can not connect to Plex server.")  
        raise

# main
print("------------------------------\nPlex Channel-Playlists Builder\n------------------------------")

# TODO: Argument Parser (Rebuild, Config File), Main User case, (Missing config settings)

rebuild = False
channel_playlist = []

# load yaml config
yaml = YAML(typ="safe")
yaml.default_flow_style = False
with open("config.yaml", "r") as config_file:
    config_yaml = yaml.load(config_file)
playlist_title = config_yaml["settings"]["playlist_title"]
plex_url = config_yaml["plex"]["plex_url"]
plex_token = config_yaml["plex"]["plex_token"]
plex_libraryname = config_yaml["plex"]["plex_libraryname"]
plex_username = config_yaml["plex"]["plex_username"]
if "plex_user_token" in config_yaml["plex"]: plex_user_token = config_yaml["plex"]["plex_user_token"]
else: plex_user_token = 0

# connect to plex server
if plex_user_token:
    user_plex = PlexServer(plex_url, plex_user_token)
else:
    user_plex, plex_user_token = ConnectPlexUser(plex_url, plex_token, plex_username)
    config_yaml["plex"]["plex_user_token"] = str(plex_user_token)
    with io.open("config.yaml", "w", encoding="utf8") as config_file:
        yaml.dump(config_yaml, config_file)

series_library = user_plex.library.section(plex_libraryname)

# Show Objects Example
# archer = ShowObj("Archer", 5, 1, 4, True)
# brooklyn = ShowObj("Brooklyn Nine-Nine", 2, 1, 2, True)
# castle = ShowObj("Castle Rock", 2, 1, 1, False)
# shows_list = [archer, brooklyn, castle]

shows_dict = {}
for item in config_yaml["shows"].items():
    print(item[1])
    shows_dict[item[1]["title"]] = ShowObj(item[1]["title"], item[1]["start_season"], item[1]["start_episode"], item[1]["sequence"], item[1]["loop"])
    print(shows_dict[item[1]["title"]].title)

if rebuild == True:
    print("Rebuild active. Get current episodes in playlist")
    my_playlist = series_library.playlist(playlist_title)
    playlist_items = my_playlist.items()
    for show in shows_dict.values():
        for item in playlist_items:
            if item.grandparentTitle == show.title:
                show.start_season = item.parentIndex
                show.start_episode = item.index
                print("New start episode: " + str(item.grandparentTitle) + " - S" + str(item.parentIndex).zfill(2) + "E" + str(item.index).zfill(2) + " - " + str(item.title))
                break

print("Build Show Episodes Lists")
for show in shows_dict.values():
    try:
        episodes = series_library.get(show.title).episodes()
    except NotFound:
        print("Show: " + str(show.title) + " not found.")
        break
    start_index = next(i for i, ep in enumerate(episodes) if ep.seasonNumber == show.start_season and ep.episodeNumber == show.start_episode)
    range_1 = range(start_index, len(episodes))
    order = []
    for i in range_1:
        order.append(i)
    if show.loop:
        range_2 = range(0, start_index)
        for i in range_2:
            order.append(i)
    print("Order for " + str(show.title) + " is: ")
    print(order)
    show.episodes_list = [episodes[i] for i in order]

# Fill Up was here

print("Get Remaining Episode Counter")
remaining_episodes = 0
for show in shows_dict.values():
    remaining_episodes += len(show.episodes_list)

print("Build the channel playlist")
while remaining_episodes > 0:
    for show in shows_dict.values():
        print("Add episodes of " + str(show.title + ". Remaining episodes: " + str(remaining_episodes)))
        for i in range(show.sequence):
            if len(show.episodes_list) > 0:
                channel_playlist.append(show.episodes_list.pop(0))
                remaining_episodes -= 1

if rebuild == True:
    print("Update the playlist on server")
    my_playlist.removeItems(playlist_items)
    my_playlist.addItems(channel_playlist)
else:
    print("Create the playlist on server")
    Playlist.create(user_plex, playlist_title, items=channel_playlist)

print("Done!")


# print("Fill Up Episodes")
# if fill_up:
#     episodes_count = []
#     for show in show_list:
#         episodes_count.append(len(show.list))
#     episodes_max = max(episodes_count)
#     for show in show_list:
#         if show.loop:
#             print("Fill up: " + str(show.title) + ". From " + str(len(show.list)) + " to " + str(episodes_max) + " episodes.")
#             i = 0
#             while len(show.list) < episodes_max:
#                 next_episode = show.list[i]
#                 show.list.append(next_episode)
#                 if i < (len(show.list)-1):
#                     i += 1
#                 else:
#                     i = 0

# print("Fill Up Episodes")
# # Unify the episode number of every show. This fill ups the episodes until the shows have the equal number of bunches. A bunch is, in this case, a series of episodes of each show before an episode of the first show comes again.
# if fill_up:
#     bunches_count = []
#     for show in show_list:
#         bunches_count.append(int(math.ceil(len(show.list)/show.sequence)))
#     bunch_max = max(bunches_count)
#     print("Number of max. bunches: " + str(bunch_max))
#     for show in show_list:
#         if show.loop:
#             new_episode_count = bunch_max*show.sequence
#             i = 0
#             print("Fill up: " + str(show.title) + ". From " + str(len(show.list)) + " to " + str(new_episode_count) + " episodes.")
#             while len(show.list) < new_episode_count:
#                 next_episode = show.list[i]
#                 show.list.append(next_episode)
#                 if i < (len(show.list)-1):
#                     i += 1
#                 else:
#                     i = 0