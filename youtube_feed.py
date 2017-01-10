import youtube_api as ya

import datetime as dt

from xml.etree import ElementTree
from googleapiclient.errors import HttpError
from urllib.parse import urlparse
from PyQt4 import QtCore


class YoutubeFeed(QtCore.QObject):
    progress_update = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, subscription_feed=None):
        """

        :param subscription_feed: file name of the subscription feed within the working folder
        """
        super(YoutubeFeed, self).__init__(parent)

        self.channels = {}
        if subscription_feed:
            self.process_file(subscription_feed)

        self.videos = {}

    def get_channels(self):
        return self.channels

    def get_videos(self):
        return self.videos

    def process_file(self, subscription_feed):
        """
        Given a Youtube Subscription Manager RSS XML file, return a dictionary of the channel names and IDs
        :param subscription_feed: file name of the subscription feed within the working folder
        :return: { Channel Name : Channel ID }
        """
        self.channels = {}
        with open(subscription_feed, mode='r', encoding="utf8") as readfile:
            root = ElementTree.parse(readfile).getroot()
            for child in root[0][0]:
                self.channels[child.attrib['title']] = urlparse(child.attrib['xmlUrl']).query[11:]

    def process_feed_from(self, api_key, date, channels=None):
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

        if channels is None:
            channels = self.channels

        count = 0
        date = dt.datetime.strptime(date, '%Y-%m-%d')
        for channel_name, chId in sorted(channels.items()):  # alphabetical order
            # create Channel objects for every channel, assign an ID unless explicitly specified in file
            chan = ya.Channel(api_key, channel_name, channel_id=chId)

            videos = chan.get_videos_since(date)
            for videoId in videos:
                vid = ya.Video(api_key, videoId)
                data = vid.get_data()

                date = str(data['date'].date())
                time = str(data['date'].time())
                if date not in self.videos:
                    self.videos[date] = {channel_name: {time: {'Video Title': data["title"], 'Video ID': data["video id"]}}}
                else:
                    if channel_name not in self.videos[date]:
                        self.videos[date][channel_name] = {time:
                                                          {'Video Title': data["title"], 'Video ID': data["video id"]}}
                    else:
                        self.videos[date][channel_name][time] = {}
                        self.videos[date][channel_name][time]['Video Title'] = data["title"]
                        self.videos[date][channel_name][time]['Video ID'] = data["video id"]

            count += 1
            self.progress_update.emit(count)

    def add_to_playlist(self, client_secret_file, playlist_id, video_id, count):
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

        count += 1
        self.progress_update.emit(count)
        return count
