# -*- coding: utf-8 -*-
#
###################################################################
# Some of this code is ...
#
# Copyright (C) 2014 Junichi Shinohara
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################

from libqtile import utils
from libqtile.widget import base
import httplib2
import datetime
import re
import dateutil.parser
import threading
import gobject
import json

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow, argparser
import oauth2client.file
from yampy import Yammer


class YammerChecker(base.ThreadedPollText):

    defaults = [
        (
            'storage_file',
            None,
            'absolute path of secrets file - must be set'
        ),
        (
            'format',
            ('My Feed:%(unseen_message_count_following)s, '
             'Private:%(private_unseen_thread_count)s'),

            'text to display - leave this at the default for now...'
        ),
        (
            'reminder_color',
            'FF0000',
            'color entries'
        ),
        ('www_group', None, 'group to open browser into'),
        ('www_screen', 0, 'screen to open group on'),
        (
            'browser_cmd',
            '/usr/bin/firefox -url https://www.yammer.com',
            'command or script to execute on click'
        ),
    ]

    def __init__(self, **config):
        base.ThreadedPollText.__init__(self, **config)
        self.text = 'Yammer Checker not initialized.'
        self.latest_message_id = None
        self.cred_init()
        # confirm credentials every hour
        self.timeout_add(3600, self.cred_init)

    def _configure(self, qtile, bar):
        base.ThreadedPollText._configure(self, qtile, bar)
        self.add_defaults(YammerChecker.defaults)
        self.layout = self.drawer.textlayout(
            self.text,
            self.foreground,
            self.font,
            self.fontsize,
            self.fontshadow,
            markup=True
        )

    def cred_init(self):
        # this is the main method for obtaining credentials
        self.log.info('refreshing GC credentials')

        # Set up a Flow object to be used for authentication.
        FLOW = OAuth2WebServerFlow(
            client_id='QnuErqsmJel45bS7pHbn2A',
            client_secret='hJmR25kAnTnP7tocz2c4fMqVsDLWbrvUEuSfq8',
            scope='https://www.yammer.com/dialog/oauth',
            user_agent='Qtile Yammer Checker/Version 0.1',
            auth_uri='https://www.yammer.com/dialog/oauth',
            token_uri='https://www.yammer.com/oauth2/access_token.json')

        # storage is the location of our authentication credentials
        storage = oauth2client.file.Storage(self.storage_file)

        # get the credentials, and update if necessary
        # this method will write the new creds back to disk if they are updated
        self.credentials = storage.get()

        # if the credentials don't exist or are invalid, get new ones from FLOW
        # FLOW must be run in a different thread or it blocks qtile
        # when it tries to pop the authentication web page
        def get_from_flow(creds, storage):
            if creds is None or creds.invalid:
                http = httplib2.Http()
                http.disable_ssl_certificate_validation = True
                flags = argparser.parse_args()
                self.credentials = run_flow(FLOW, storage, flags, http)
        threading.Thread(
            target=get_from_flow,
            args=(self.credentials, storage)
        ).start()

        return True

    def cal_updater(self):
        self.log.info('adding GC widget timer')

        def cal_getter():  # get cal data in thread, write it in main loop
            data = self.fetch_calendar()
            gobject.idle_add(self.update, data)
        threading.Thread(target=cal_getter).start()
        return True

    def button_press(self, x, y, button):
        base.ThreadedPollText.button_press(self, x, y, button)
        if hasattr(self, 'credentials'):
            if self.www_group:
                self.qtile.addGroup(self.www_group)
                www_group = self.www_group
            else:
                www_group = self.qtile.groupMap.keys()[0]
            self.qtile.groupMap[www_group].cmd_toscreen(self.www_screen)
            self.qtile.cmd_spawn(self.browser_cmd)

    def poll(self):
        # if we don't have valid credentials, update them
        if not hasattr(self, 'credentials') or self.credentials.invalid:
            self.cred_init()
            return 'Credentials updating'

        access_token = self.credentials.access_token['token']
        yammer = Yammer(access_token=access_token)
        contents = yammer.messages.from_my_feed()
        p_contents = yammer.messages.private()

        content_keys = [
            "unseen_message_count_following",
            "unseen_thread_count_following",
            "unseen_message_count_received",
            "unseen_thread_count_received",
            "unseen_message_count_algo",
            "unseen_thread_count_algo",
            "unseen_message_count_my_all",
            "unseen_thread_count_my_all"]
        p_content_keys = [
            "unseen_thread_count"]
        data = {}
        for p_content_key in p_content_keys:
            data["private_" + p_content_key] = p_contents.meta[p_content_key]
        for content_key in content_keys:
            data[content_key] = contents.meta[content_key]

        for key in data.keys():
            if data[key] == 0:
              continue
            data[key] = '<span color="%s">%s</span>' % (
                utils.hex(self.reminder_color),
                data[key])
        return self.format % data
