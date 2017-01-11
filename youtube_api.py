import urllib.request
import requests
import json
from datetime import datetime, timedelta

import httplib2
import os
import sys

from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow


class YoutubeAPIURL:
    def __init__(self, api_key):
        self.youtubeApiUrl = "https://www.googleapis.com/youtube/v3"
        self.youtubeChannelsApiUrl = self.youtubeApiUrl + "/channels?key={0}&".format(api_key)
        self.youtubeSearchApiUrl = self.youtubeApiUrl + "/search?key={0}&".format(api_key)
        self.youtubeVideoApi = self.youtubeApiUrl + "/videos?key={0}&".format(api_key)

        self.requestParametersChannelId = self.youtubeChannelsApiUrl + 'forUsername={0}&part=id'
        self.requestChannelVideosInfo = self.youtubeSearchApiUrl + 'channelId={0}&' \
                                                                    'part=id&' \
                                                                    'order=date&' \
                                                                    'type=video&' \
                                                                    'publishedBefore={1}&' \
                                                                    'publishedAfter={2}&' \
                                                                    'pageToken={3}&' \
                                                                    'maxResults=50'
        self.requestVideoInfo = self.youtubeVideoApi + "part=snippet&id={0}"


class YoutubeClientAPI:
    def __init__(self, client_secrets_file):
        # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
        # the OAuth 2.0 information for this application, including its client_id and
        # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
        # the Google Cloud Console at
        # https://cloud.google.com/console.
        # Please ensure that you have enabled the YouTube Data API for your project.
        # For more information about using OAuth2 to access the YouTube Data API, see:
        #   https://developers.google.com/youtube/v3/guides/authentication
        # For more information about the client_secrets.json file format, see:
        #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

        self.CLIENT_SECRETS_FILE = client_secrets_file

        # This variable defines a message to display if the CLIENT_SECRETS_FILE is
        # missing.
        self.MISSING_CLIENT_SECRETS_MESSAGE = """
           WARNING: Please configure OAuth 2.0

           To make this sample run you will need to populate the client_secrets.json file
           found at:

           %s

           with information from the Cloud Console
           https://cloud.google.com/console

           For more information about the client_secrets.json file format, please visit:
           https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
           """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              client_secrets_file))

        # This OAuth 2.0 access scope allows for full read/write access to the
        # authenticated user's account.
        self.YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
        self.YOUTUBE_API_SERVICE_NAME = "youtube"
        self.YOUTUBE_API_VERSION = "v3"

        if getattr(sys, 'frozen', False):
            # The application is frozen
            self.data_dir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            self.data_dir = os.path.dirname(__file__)

        self.flow = flow_from_clientsecrets(self.CLIENT_SECRETS_FILE,
                                            scope=self.YOUTUBE_SCOPE,
                                            message=self.MISSING_CLIENT_SECRETS_MESSAGE)

        self.storage = Storage(os.path.join(self.data_dir, "{}-oauth2.json".format(sys.argv[0])))
        self.credentials = None
        try:
            self.credentials = self.storage.get()
        except AttributeError:
            pass

        if self.credentials is None or self.credentials.invalid:
            if getattr(sys, 'frozen', False):
                # The application is frozen
                self.credentials = run_flow(self.flow, self.storage,
                                            http=httplib2.Http(ca_certs=os.path.join(self.data_dir, 'cacert.pem')))
            else:
                self.credentials = run_flow(self.flow, self.storage)

    def get_authenticated_service(self):
        if getattr(sys, 'frozen', False):
            # The application is frozen
            self.data_dir = os.path.dirname(sys.executable)
            return build(self.YOUTUBE_API_SERVICE_NAME,
                         self.YOUTUBE_API_VERSION,
                         http=self.credentials.authorize(
                             httplib2.Http(ca_certs=os.path.join(self.data_dir, 'cacert.pem'))))

        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            return build(self.YOUTUBE_API_SERVICE_NAME,
                         self.YOUTUBE_API_VERSION,
                         http=self.credentials.authorize(
                             httplib2.Http()))


class Channel:
    def __init__(self, api_key, channel_name, channel_alias=None, channel_id=None):
        self.youtubeAPIURL = YoutubeAPIURL(api_key)
        self.channelName = channel_name
        self.channelAlias = channel_alias
        self.channelId = channel_id

    def __str__(self):
        return "Channel name:  {}\nChannel Alias:  {}\nChannelId:  {}".format(self.channelName,
                                                                              self.channelAlias,
                                                                              self.channelId)

    def __repr__(self):
        return "Channel name:  {}\nChannel Alias:  {}\nChannelId:  {}".format(self.channelName,
                                                                              self.channelAlias,
                                                                              self.channelId)

    def _get_videos_between(self, from_date, to_date):
        """
        dates= datetime.datetime objects

        :param from_date: Earliest date
        :param to_date: Latest date
        :return:
        """
        # format dates
        from_date = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        to_date = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        next_page_token = ""
        found_all = False

        ret_val = []

        while not found_all:
            try:
                url = self.youtubeAPIURL.requestChannelVideosInfo.format(self.channelId,
                                                                         to_date,
                                                                         from_date,
                                                                         next_page_token)
                resp = urllib.request.urlopen(url).read().decode("utf8")

                json_resp = json.loads(resp)
                returned_videos = json_resp["items"]

                for video in returned_videos:
                    ret_val.append(video["id"]["videoId"])

                try:
                    next_page_token = json_resp["nextPageToken"]

                except KeyError:  # no nextPageToken
                    found_all = True

            except IndexError:  # error; no videos found. don't print anything
                found_all = True

        return ret_val

    def get_videos_since(self, since_date):
        """
        sinceDate = datetime.datetime object
        """

        current_date = datetime.now()
        return self._get_videos_between(since_date, current_date)

    def get_all_videos(self):
        first_youtube_video = datetime(year=2005, month=4, day=22)  # first youtube video -1
        current_date = datetime.now()

        return self._get_videos_between(first_youtube_video, current_date)


class Video:
    def __init__(self, api_key, video_id):
        self.youtubeAPIURL = YoutubeAPIURL(api_key)
        self.videoId = video_id

    def get_data(self):
        """
        :return: dictionary in format
            {
                'date' : Published Date (datetime object),
                'description' : Video Description,
                'title' : Video Title,
                'url' : Video ID
            }
        """
        try:
            results = {}
            url = self.youtubeAPIURL.requestVideoInfo.format(self.videoId)
            resp = urllib.request.urlopen(url).read().decode("utf8")

            json_resp = json.loads(resp)
            snippet = json_resp["items"][0]["snippet"]
            results["description"] = snippet["description"]
            results["title"] = snippet["title"]
            results["video id"] = self.videoId
            results["date"] = datetime.strptime(snippet["publishedAt"], '%Y-%m-%dT%H:%M:%S.000Z')

            # we don't need else here since un-parsed date is already in results dict
            return results

        except IndexError:
            print("ERROR: Finding video data for video {}".format(self.videoId))
            return None
