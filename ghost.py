import os
import sublime
import sublime_plugin
import threading
import urllib
import urllib2
import functools
import os.path

def view_contents(view):
    region = sublime.Region(0, view.size())
    return view.substr(region)

def _make_text_safeish(text, fallback_encoding, method='decode'):
    try:
        unitext = getattr(text, method)('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        unitext = getattr(text, method)(fallback_encoding)
    return unitext

class GhostApiCallThread(threading.Thread):
    def __init__(self, api, action, content, on_done, fallback_encoding=""):
        threading.Thread.__init__(self)
        self.api = api
        self.action = action
        self.content = _make_text_safeish(content, fallback_encoding)
        self.on_done = on_done
        self.result = None
        self.token = ''
        threading.Thread.__init__(self)

    def run(self):
        self.get_token();
        try:
            request = self.request_builder()
            http_response = urllib2.urlopen(request, timeout=self.timeout)
            self.result = http_response.read()
            return

        except (urllib2.HTTPError) as (e):
            err = '%s: HTTP error %s when call Ghost API' % (__name__, str(e.code))
        except (urllib2.URLError) as (e):
            err = '%s: URL error %s when call Ghost API' % (__name__, str(e.reason))

        sublime.error_message(err)
        self.result = False

    def get_token(self):
        settings = sublime.load_settings('Git.sublime-settings')
        username = settings.get('username')
        password = settings.get('password')

        # Call Auth API
        token = 'token'
        return token

    def get_endpoint(self):
        settings = sublime.load_settings('Git.sublime-settings')
        return settings.get(self.api)

    # Build http request of GET/POST/PUT/DELETE
    def request_builder(self):
        request = None
        endpoint = self.get_endpoint()
        token = self.get_token()
        if self.action == 'GET':
            request = urllib2.Request(endpoint, headers={"Authorization": "Bearer " + token})
        if self.action == 'POST' or self.action == 'PUT':
            request = urllib2.Request(endpoint, urllib.urlencode(self.content),
                headers={"Authorization": "Bearer " + token})

        return request

# EndPoint invoke for all ghost commands
class GhostCommand(object):

    def run_command(self, api, action, content, callback=None):
        if not callback:
            callback = self.generic_done


        thread = GhostApiCallThread(api, action, content, callback)
        thread.start()

        # Show some message on ST status bar
        message = kwargs.get('status_message', False) or self.token.join(command)
        sublime.status_message(message)

    def generic_done(self, result):
        if not result.strip():
            return
        sublime.status_message(result)

# A base for all ghost commands that work with the file in the active view
class GhostTextCommand(GhostCommand, sublime_plugin.TextCommand):
    def active_view(self):
        return self.view

    def get_file_name(self):
        return os.path.basename(self.view.file_name())

    # Build post object. Sample:
    #{
    #    posts: [
    #        {
    #            title: "Welcome to Ghost",
    #            markdown: "",
    #            slug: "welcome-to-ghost",
    #            status: "published",
    #            author: 1
    #        }
    #    ]
    #}
    def post_object_builder(self):
        return view_contents(self.active_view())
