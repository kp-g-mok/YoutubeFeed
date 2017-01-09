from settings_api import Settings
import youtube_feed as yf

import sys
import os
import datetime as dt

from PyQt4 import QtCore, QtGui, uic

__author__ = 'KPGM'

form_main = uic.loadUiType('main.ui')[0]


class MainWindow(QtGui.QMainWindow, form_main):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.settings = Settings(find_data_file('settings.json'))
        self.videos = {}

        self.trv_Video_Feed_Model = QtGui.QStandardItemModel(self.trv_Video_Feed_View)
        self.reset_treeview_model()

        self.refresh_date()
        self.setup_treeview()
        self.connect_components()

    def reset_treeview_model(self):
        self.trv_Video_Feed_Model.clear()
        self.trv_Video_Feed_Model.setHorizontalHeaderLabels(['', ''])
        self.trv_Video_Feed_View.setColumnWidth(0, 700)
        self.trv_Video_Feed_View.setColumnWidth(1, 300)

    def setup_treeview(self):
        self.trv_Video_Feed_View.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.trv_Video_Feed_View.setModel(self.trv_Video_Feed_Model)
        self.trv_Video_Feed_View.setUniformRowHeights(True)

    def connect_components(self):
        """
        Connects QT actionables with functions
        """
        self.btn_Check_Feed.clicked.connect(self.act_check_feed_triggered)
        self.btn_Update_Date.clicked.connect(self.act_update_date_triggered)
        self.btn_Watch_Later.clicked.connect(self.act_watch_later_triggered)

    def refresh_date(self):
        """
        Refreshes the Lasted Checked Date display
        """
        y, m, d = (int(date_part) for date_part in self.settings.get_last_checked().split("-"))
        self.last_checked_date.setDate(QtCore.QDate(y, m, d))

    def act_check_feed_triggered(self):
        api_key = self.settings.get_api_key()
        if not api_key or api_key.isspace():
            error_message("Youtube API key missing.\nCheck settings.json file.")
        last_checked_date = self.settings.get_last_checked()
        if not last_checked_date or last_checked_date.isspace():
            error_message("No Last Checked Date.\nCheck settings.json file.")

        self.reset_treeview_model()
        self.videos = yf.process_feed_from(api_key, last_checked_date, yf.process_file(find_data_file('subscription_manager.xml')))

        for publish_date in sorted(self.videos):
            date = QtGui.QStandardItem(dt.datetime.strptime(publish_date, '%Y-%m-%d').strftime('%m/%d/%y'))
            for channel_name in sorted(self.videos[publish_date]):
                channel = QtGui.QStandardItem(channel_name)
                for video_title in sorted(self.videos[publish_date][channel_name]):
                    video = QtGui.QStandardItem(video_title)
                    video_url = QtGui.QStandardItem(
                        "https://www.youtube.com/watch?v={}".format(
                            self.videos[publish_date][channel_name][video_title]))
                    channel.appendRow([video, video_url])
                date.appendRow(channel)
            self.trv_Video_Feed_Model.appendRow(date)

        self.trv_Video_Feed_View.expandAll()

    def act_update_date_triggered(self):
        """
        Updates the last checked date to today
        """
        self.settings.update_last_run(str(dt.date.today()))
        self.refresh_date()

    def act_watch_later_triggered(self):
        self.pb_adding_videos.setValue(0)  # Reset value

        video_count = 0
        for publish_date in self.videos:
            for channel_name in self.videos[publish_date]:
                video_count += len(self.videos[publish_date][channel_name])
        self.pb_adding_videos.setMaximum(video_count)

        count = 0
        client_secrets_file = find_data_file(self.settings.get_client_secrets_file())
        for publish_date in sorted(self.videos):
            for channel_name in sorted(self.videos[publish_date]):
                for video_title in sorted(self.videos[publish_date][channel_name]):
                    yf.add_to_playlist(client_secrets_file,
                                       'WL',
                                       self.videos[publish_date][channel_name][video_title])
                    count += 1
                    self.pb_adding_videos.setValue(count)

        self.act_update_date_triggered()


def error_message(err_msg):
    msg = QtGui.QMessageBox()
    msg.setIcon(QtGui.QMessageBox.Critical)
    msg.setText("Error when running utility.")
    msg.setInformativeText(str(err_msg))
    msg.setWindowTitle("Error Message")
    msg.setStandardButtons(QtGui.QMessageBox.Ok)

    msg.exec_()


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        data_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        data_dir = os.path.dirname(__file__)

    return os.path.join(data_dir, filename)


def main():
    app = QtGui.QApplication(sys.argv)
    my_window = MainWindow(None)
    my_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
