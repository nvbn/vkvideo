#!/usr/bin/python
from gi.repository import GLib, GObject, Gio, Unity, GConf, Gdk
from functools import wraps, partial
import collections
import vkontakte
import keyring
import urllib
import re
import subprocess
import gettext
import os
import threading
import time


path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locale')
if not os.path.isdir(path):
    path = '/usr/share/locale/'
gettext.bindtextdomain('vklens', path)
gettext.textdomain('vklens')
_ = gettext.gettext


def update_on_finish(fnc):
    @wraps(fnc)
    def wrapper(self, *args, **kwargs):
        try:
            return fnc(self, *args, **kwargs)
        except AttributeError:
            return None
        finally:
            self.update_results_model()
    return wrapper


class VideoPage(object):
    def __init__(self, uri, max_quality=720):
        data = urllib.urlopen(uri).read()
        vars = re.search('flashvars=(.*)><', data).group(1)
        vars = dict(map(lambda part: part.split('='), vars.split('&amp;')))
        url = vars['host'] + 'u' + vars['uid'] + '/' + 'video' + '/' + vars['vtag'] + '.%s.mp4'
        qualitys = ['720', '480', '360', '240']

        urls = map(lambda quality: (quality, url % quality),
            qualitys[qualitys.index(max_quality):])
        for quality, url in urls:
            if urllib.urlopen(url).code == 200:
                break
            else:
                urls.remove((quality, url))
        self.thumb = vars['thumb']
        self.urls = urls
        self.title = urllib.unquote_plus(vars['md_title'])

    def open(self, player, quality=0):
        subprocess.Popen(player.split(' ') + [
            self.urls[quality][1],
        ])


class ActionIdle(object):
    def __init__(self):
        self.open_queue = collections.deque()
        GObject.timeout_add(1000, self.run)

    def open(self, uri, max_quality, player):
        self.open_queue.append((
            uri, max_quality, player,
        ))

    def run(self):
        try:
            uri, max_quality, player = self.open_queue.popleft()
            page = VideoPage(uri, max_quality)
            page.open(player)
        except IndexError:
            pass
        GObject.timeout_add(1000, self.run)


class Daemon(object):
    """Lens daemon"""
    def __init__(self, session_bus_connection):
        """Init lens and create scope"""
        self.session_bus_connection = session_bus_connection
        self.lens = Unity.Lens.new("/net/launchpad/unity/lens/vkvideo", "vkvideo")
        self.lens.props.search_hint = _("Start writting video name")
        self.lens.props.visible = True
        self.lens.props.search_in_global = False
        category_icon = Gio.ThemedIcon.new("vkvideo")
        icon = Gio.ThemedIcon.new("/usr/share/icons/unity-icon-theme/places/svg/group-recent.svg")
        self.lens.props.categories = [
            Unity.Category.new(_("Videos"), category_icon,
                Unity.CategoryRenderer.HORIZONTAL_TILE,
            ), Unity.Category.new(_("Settings"), category_icon,
                Unity.CategoryRenderer.VERTICAL_TILE,
            ),
        ]
        quality = Unity.RadioOptionFilter.new('quality', _('quality'), icon, True)
        quality.add_option('with_low', _('with low'), icon)
        sort = Unity.RadioOptionFilter.new('sorting', _('sorting'), icon, True)
        sort.add_option('0', _('by date'), icon)
        sort.add_option('1', _('by length'), icon)
        sort.add_option('2', _('by rel'), icon)
        count = Unity.RadioOptionFilter.new('count', _('count'), icon, True)
        count.add_option('20', '20', icon)
        count.add_option('50', '50', icon)
        count.add_option('100', '100', icon)
        count.add_option('200', '200', icon)
        self.lens.props.filters = [quality, sort, count]
        self.scope = VKScope()
        self.lens.add_local_scope(self.scope.scope)
        self.lens.export()


class VKScope(object):
    """Scope with vk videos"""
    def __init__(self):
        """Init scope and connect signals"""
        self.search_string = ''
        self.only_hd = 1
        self.sorting = 0
        self.model = None
        self.count = 20
        self._vk = None
        self.settings = GConf.Client.get_default()
        self.scope = Unity.Scope.new("/net/launchpad/unity/scope/vkvideo")
        self.scope.connect("activate_uri", self.on_uri_activated)
        self.scope.connect("filters-changed", self.on_filter_changed)
        self.scope.connect("search-changed", self.on_search_changed)
        self.scope.export()
        self.scope.connect('preview-uri', self.on_preview_uri)
        self.action_idle = ActionIdle()

    @property
    def vk(self):
        """VK api property"""
        if not self._vk:
            token = keyring.get_password('vkvideo-lens', 'access_token')
            self._vk = vkontakte.API(token=token) if token else None
        return self._vk

    @update_on_finish
    def on_search_changed(self, scope, search, search_type, cancellable):
        """Search value changed event"""
        self.search_string = search.props.search_string.strip()
        self.model = search.props.results_model

    @update_on_finish
    def on_filter_changed(self, scope):
        """Filter value changed event"""
        self.only_hd = 1 - int(bool(scope.get_filter('quality').get_active_option()))
        sorting = scope.get_filter('sorting').get_active_option()
        if sorting:
            self.sorting = sorting.props.id
        else:
            self.sorting = 0
        count = scope.get_filter('count').get_active_option()
        if count:
            self.count = count.props.id
        else:
            count = 20

    def update_results_model(self):
        """Update results"""
        model = self.model
        if model is not None:
            model.clear()
            if self.vk:
                try:
                    for entry in self.vk.get(
                        'video.search', q=self.search_string,
                        hd=self.only_hd, sort=self.sorting,
                        count=self.count,
                    ):
                        model.append(entry['player'],
                            entry['thumb'], 0, "video/mp4",
                            entry['title'], "",
                        entry['player'])
                except Exception:  # Prevent apport errors
                    pass
            model.append('vkvideo',
                'vkvideo', 1, 'image/png',
                _('Authorisation'), "",
            "vkvideo")
            model.append('vksettings',
                'vkvideo', 1, 'image/png',
                _('Settings'), "",
            "vksettings")

    def on_uri_activated(self, scope, uri):
        """Uri activated event"""
        handled = Unity.ActivationResponse(handled=Unity.HandledType.HIDE_DASH, goto_uri=uri)
        if uri in ('vkvideo', 'vksettings'):
            subprocess.Popen([uri])
        elif self.vk:
            self.action_idle.open(uri,
                self.settings.get_string('/apps/unity-vkvideo-lens/quality') or '720',
                self.settings.get_string('/apps/unity-vkvideo-lens/player') or 'totem',
            )
        return handled

    def on_preview_uri(self, scope, uri):
        page = VideoPage(url)
        preview = Unity.GenericPreview.new(page.title, '', None)
        preview.props.image_source_uri = page.thumb
        for num, (quality, url) in enumerate(page.urls):
            action = Unity.PreviewAction.new(quality, quality + 'p', None)
            action.connect('activated', partial(page, 
                self.settings.get_string('/apps/unity-vkvideo-lens/player') or 'totem',
            num))
            preview.add_action(action)
        return preview


def main():
    session_bus_connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    session_bus = Gio.DBusProxy.new_sync(session_bus_connection, 0, None,
        'org.freedesktop.DBus',
        '/org/freedesktop/DBus',
        'org.freedesktop.DBus', None)
    result = session_bus.call_sync('RequestName',
        GLib.Variant("(su)", ('net.launchpad.Unity.Lens.VKvideo', 0x4)),
        0, -1, None)
    result = result.unpack()[0]
    if result != 1:
        raise SystemExit(1)
    daemon = Daemon(session_bus_connection)
    GObject.MainLoop().run()

if __name__ == "__main__":
    main()
