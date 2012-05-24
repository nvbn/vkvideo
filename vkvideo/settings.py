from gi.repository import Gtk, Notify, GConf
import os
import gettext


path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locale')
if not os.path.isdir(path):
    path = '/usr/share/locale/'
gettext.bindtextdomain('vksettings', path)
gettext.textdomain('vksettings')
_ = gettext.gettext


class SettingsDialog(Gtk.Dialog):
    """Settings dialog"""
    QUALITYS = ['240', '360', '480', '720']
    DEFAULT_QUALITY = '720'
    DEFAULT_PLAYER = 'totem'
    PLAYER_KEY = '/apps/unity-vkvideo-lens/player'
    QUALITY_KEY = '/apps/unity-vkvideo-lens/quality'

    def __init__(self, *args, **kwargs):
        """Open settings dialog"""
        super(SettingsDialog, self).__init__(*args, **kwargs)
        self.settings = GConf.Client.get_default()
        self.set_default_size(150, 100)
        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add(vbox)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.add(Gtk.Label(_('Prefered player:')))
        self.player = Gtk.Entry()
        current_player = self.settings.get_string(SettingsDialog.PLAYER_KEY) or SettingsDialog.DEFAULT_PLAYER
        self.player.set_text(current_player)
        hbox.add(self.player)
        vbox.add(hbox)
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox2.add(Gtk.Label(_('Prefered quality:')))
        self.quality = Gtk.ComboBoxText()
        for q in SettingsDialog.QUALITYS:
            self.quality.append_text(q)
        current_quality = self.settings.get_string(SettingsDialog.QUALITY_KEY) or SettingsDialog.DEFAULT_QUALITY
        self.quality.set_active(SettingsDialog.QUALITYS.index(current_quality))
        hbox2.add(self.quality)
        vbox.add(hbox2)
        self.connect('response', self.on_action)

    def on_action(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self.settings.set_string(
                SettingsDialog.QUALITY_KEY, 
                SettingsDialog.QUALITYS[self.quality.get_active()],
            )
            self.settings.set_string(
                SettingsDialog.PLAYER_KEY, 
                self.player.get_text(),
            )
            Notify.init("vkvideo")
            Notify.Notification.new(
                'vkvideo',
                 _('Settings saved success'),
            '').show()
        Gtk.main_quit()


def main():
    win = SettingsDialog(_('Settings'), None, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
