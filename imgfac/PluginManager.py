# encoding: utf-8

#   Copyright 2012 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import sys
import os
import json
from .Singleton import Singleton
from .ImageFactoryException import ImageFactoryException

PLUGIN_TYPES = ('OS', 'CLOUD')
INFO_FILE_EXTENSION = '.info'
PKG_STR = 'imagefactory_plugins'


class PluginManager(Singleton):
    """ Registers and manages ImageFactory plugins. """

    @property
    def plugins(self):
        """
        The property plugins
        """
        return self._plugins

    def _singleton_init(self, plugin_path):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        sys.path.append(plugin_path)

        if os.path.exists(plugin_path):
            self.path = plugin_path
        else:
            msg = 'Plugin path (%s) does not exist! No plugins loaded.' % plugin_path
            self.log.exception(msg)
            raise Exception(msg)

        self._plugins = dict()
        self._targets = dict()
        self._types = dict().fromkeys(PLUGIN_TYPES, list())

    def load(self):
        """
        Enumerates through installed plugins and registers each according to
        the features provided. Only one plugin may be registered per feature.
        When more than one plugin is found, the first will be registered and
        all others listed as inactive.
        """
        info_files = list()
        directory_listing = os.listdir(self.path)
        for _file in directory_listing:
            if _file.endswith(INFO_FILE_EXTENSION):
                info_files.append(_file)

        for filename in info_files:
            plugin_name = filename[:-len(INFO_FILE_EXTENSION)]
            md = self.metadata_for_plugin(plugin_name)
            try:
                if md['type'].upper() in PLUGIN_TYPES:
                    for target in md['targets']:
                        target = target if isinstance(target, str) else tuple(target)
                        if not target in self._targets:
                            self._targets[target] = plugin_name
                        else:
                            msg = 'Did not register %s for %s. Plugin %s already registered.' % (plugin_name,
                                                                                                 target,
                                                                                                 self._targets[target])
                            self._register_plugin_with_error(plugin_name, msg)
                            self.log.warn(msg)
                    self._plugins[plugin_name] = md
                    self._types[md['type'].upper()].append(plugin_name)
                    self.log.info('Plugin (%s) loaded...' % plugin_name)
            except KeyError as e:
                msg = 'Invalid metadata for plugin (%s). Missing entry for %s.' % (plugin_name, e)
                self._register_plugin_with_error(plugin_name, msg)
                self.log.exception(msg)
            except Exception as e:
                msg = 'Loading plugin (%s) failed with exception: %s' % (plugin_name, e)
                self._register_plugin_with_error(plugin_name, msg)
                self.log.exception(msg)

    def _register_plugin_with_error(self, plugin_name, error_msg):
        self._plugins[plugin_name] = dict(ERROR=error_msg)

    def metadata_for_plugin(self, plugin):
        """
        Returns the metadata dictionary for the plugin.

        @param plugin name of the plugin or the plugin's info file

        @return dictionary containing the plugin's metadata
        """
        if plugin in self._plugins:
            return self._plugins[plugin]
        else:
            fp = None
            metadata = None
            info_file = plugin + INFO_FILE_EXTENSION
            try:
                fp = open(os.path.join(self.path, info_file), 'r')
                metadata = json.load(fp)
            except Exception as e:
                self.log.exception('Exception caught while loading plugin metadata: %s' % e)
                raise e
            finally:
                if fp:
                    fp.close()
                return metadata

    def plugin_for_target(self, target):
        """
        Looks up the plugin for a given target and returns an instance of the 
        delegate class or None if no plugin is registered for the given target.
        Matches are done from left to right, ie. ('Fedora', '16', 'x86_64') will
        match a plugin with a target of ('Fedora', None, None) but not
        ('Fedora', None, 'x86_64')
        
        @param target A list or string matching the target field of the
        plugin's .info file.
    
        @return An instance of the delegate class of the plugin or None.
        """
        try:
            if isinstance(target, str):
                self.log.debug("Attempting to match string target (%s)" % target)
                plugin_name = self._targets.get(tuple([target]))
                if not plugin_name:
                    raise ImageFactoryException("No plugin .info file loaded for target: %s" % (target))
                plugin = __import__('%s.%s' % (PKG_STR, plugin_name), fromlist=['delegate_class'])
                return plugin.delegate_class()
            elif isinstance(target, tuple):
                _target = list(target)
                self.log.debug("Attempting to match list target (%s)" % (str(_target)))
                
                # Add s390x-specific logging for clarity
                if 's390x' in _target:
                    self.log.info("Target involves s390x architecture. Checking plugin compatibility...")
                    
                for index in range(1, len(target) + 1):
                    plugin_name = self._targets.get(tuple(_target))
                    if not plugin_name:
                        _target[-index] = None
                    else:
                        plugin = __import__('%s.%s' % (PKG_STR, plugin_name), fromlist=['delegate_class'])
                        return plugin.delegate_class()
        except ImportError as e:
            self.log.exception(e)
            raise ImageFactoryException("Unable to import plugin for target: %s" % str(target))

