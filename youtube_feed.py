import youtube_api as ya

import datetime as dt

from xml.etree import ElementTree
from googleapiclient.errors import HttpError
from urllib.parse import urlparse


def process_file(subscription_feed):
    """
    Given a Youtube Subscription Manager RSS XML file, return a dictionary of the channel names and IDs
    :param subscription_feed: file name of the subscription feed within the working folder
    :return: { Channel Name : Channel ID }
    """
    channels = {}
    with open(subscription_feed, mode='r', encoding="utf8") as readfile:
        root = ElementTree.parse(readfile).getroot()
        for child in root[0][0]:
            channels[child.attrib['title']] = urlparse(child.attrib['xmlUrl']).query[11:]

    return channels


def process_feed_from(api_key, date, channels):
    """
    Gets all the videos from the channels given
    :param api_key: String with the Youtube API key
    :param date: datetime object with the starting date in the past
    :param channels: Dictionary in format - { channel name : channel id }
    :return: dictionary of format
        {
            Publish Date : {
                Channel Name: {
                    Video Title : Video URL
                }
            }
        }
    """

    date = dt.datetime.strptime(date, '%Y-%m-%d')
    video_list = {}
    for channel_name, chId in sorted(channels.items()):  # alphabetical order
        # create Channel objects for every channel, assign an ID unless explicitly specified in file
        chan = ya.Channel(api_key, channel_name, channel_id=chId)

        videos = chan.get_videos_since(date)
        for videoId in videos:
            vid = ya.Video(api_key, videoId)
            data = vid.get_data()

            data['date'] = str(data['date'].date())
            if data['date'] not in video_list:
                video_list[data['date']] = {channel_name: {data["title"]: data["video id"]}}
            else:
                if channel_name not in video_list[data['date']]:
                    video_list[data['date']][channel_name] = {data["title"]: data["video id"]}
                else:
                    video_list[data['date']][channel_name][data["title"]] = data["video id"]

    return video_list


def add_to_playlist(client_secret_file, playlist_id, video_id):
    youtube_service = ya.YoutubeClientAPI(client_secret_file).get_authenticated_service()
    try:
        add_video_request = youtube_service.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                    # 'position': 0
                }
            }
        ).execute()
    except HttpError:
        pass

