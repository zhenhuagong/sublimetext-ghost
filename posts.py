import sublime
from ghost import GhostTextCommand

###
#   Handle the operations with Posts APIs
###
class GhostPostsPost(object):
    def run(self, edit=None):
        post_object = self.post_object_builder()
        self.run_command('Posts', 'POST', post_object, self.post_done)

    def post_done(self, result):
        return

class GhostPostsUpdate(object):
    def run(self, edit=None):
        self.run_command('Posts', 'PUT', self.update_done)

    def update_done(self, result):
        return