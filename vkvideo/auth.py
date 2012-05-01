from gi.repository import Gtk, WebKit, Notify
import re
import keyring
import os
import gettext


path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locale')
if not os.path.isdir(path):
    path = '/usr/share/locale/'
gettext.bindtextdomain('vklensauth', path)
gettext.textdomain('vklensauth')
_ = gettext.gettext


class AuthDialog(Gtk.Window):
    """Authentication dialog"""
    def __init__(self, *args, **kwargs):
        """Open vk auth page"""
        super(AuthDialog, self).__init__(*args, **kwargs)
        self.webview = WebKit.WebView()
        self.add(self.webview)
        self.webview.open("""http://oauth.vk.com/authorize?
        client_id=2739195&
        scope=video,offline&
        redirect_uri=oauth.vk.com/blank.html&
        display=page&
        response_type=token""")
        self.webview.connect('load-finished', self.finished)

    def finished(self, widget, user_data):
        """Page load fifnshed"""
        uri = widget.get_uri()
        if 'access_token' in uri:
            token = re.match('.*access_token=(.*)&expires.*', uri).groups()[0]
            keyring.set_password(
                'vkvideo-lens', 'access_token', token,
            )
            Notify.init("vkvideo")
            Notify.Notification.new(
                'vkvideo',
                 _('authorisations success'),
            '').show()
            Gtk.main_quit()


def main():
    win = AuthDialog(title=_('Authorise'))
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
