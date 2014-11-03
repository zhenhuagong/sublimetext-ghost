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

class GhostApiCallThread(threading.Thread):
    def __init__(self, api, action, endpoint, token, content, on_done):
        threading.Thread.__init__(self)
        self.api = api
        self.action = action
        self.endpoint = endpoint
        self.token = token
        self.content = content
        self.on_done = on_done
        self.result = None
        self.token = ''
        self.timeout = 1    # 1 second for http request timeout
        threading.Thread.__init__(self)

    def run(self):
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

    # Build http request of GET/POST/PUT/DELETE
    def request_builder(self):
        request = None
        headers = {"Authorization": "Bearer " + self.token}
        if self.action == 'GET':
            request = urllib2.Request(self.endpoint, headers={"Authorization": "Bearer " + token})
        if self.action == 'POST' or self.action == 'PUT':
            request = urllib2.Request(self.endpoint, self.content, headers)
        return request

# EndPoint invoke for all ghost commands
class GhostCommand(object):

    def run_command(self, api, action, content, callback=None, **kwargs):
        if not callback:
            callback = self.generic_done

        # Loading settings
        token = self.get_token()
        endpoint = self.get_endpoint(api)

        thread = GhostApiCallThread(api, action, endpoint, token, content, callback)
        thread.start()

        # Show some message on ST status bar
        message = api.join(action)
        sublime.status_message(message)

    def generic_done(self, result):
        if not result.strip():
            return
        #sublime.status_message(result)

    def get_token(self):
        settings = sublime.load_settings('Ghost.sublime-settings')
        username = settings.get('username')
        password = settings.get('password')
        client_id = settings.get('client_id')

        token_endpoint = self.get_endpoint("Auth")

        # Call Auth API
        post_content = "grant_type=password&username=" + username + "&password=" + password + "&client_id=" + client_id
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            http_request = urllib2.Request(token_endpoint, post_content, headers)
            http_response = urllib2.urlopen(http_request, timeout=1)
            result = http_response.read()

            if not result.strip():
                return result.access_token
            return

        except (urllib2.HTTPError) as (e):
            err = '%s: HTTP error %s when call Ghost API' % (__name__, str(e.code))
        except (urllib2.URLError) as (e):
            err = '%s: URL error %s when call Ghost API' % (__name__, str(e.reason))
        sublime.error_message(err)

    def get_endpoint(self, api):
        settings = sublime.load_settings('Ghost.sublime-settings')
        return settings.get("host") + settings.get(api)


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
