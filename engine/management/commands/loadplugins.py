from django.core.management.base import BaseCommand, CommandError
from engine.util.configparser import Config
from engine.controller.sharedmanager import shared_plugin
from engine.controller.rts import load_plugins

from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.locale import LocaleMiddleware 
class Command(BaseCommand):
    ''' Load games plugin. store plugin class in memory '''
    plugin_methods = {}
    plugin_methods_map = {}

    def handle(self, *args, **options):
        try:
            PLUGINS_PATH = Config.getValue("PLUGINS", "path")
        except:
            raise CommandError("[path] value not defined in section [PLUGINS] . See web.cfg!")

        ''' load games plugins '''
        try:
            load_plugins(PLUGINS_PATH)
        except:
            raise CommandError("Unable to load plugins")
        self.stdout.write("Successfully loaded plugins")