#!/usr/libexec/system-python

# proxy-autodetect.py
# Override the default proxy server according to the output of a script
#
# Based in part on https://raw.githubusercontent.com/rpm-software-management/dnf-plugins-extras/master/plugins/torproxy.py
#
# Copyright (C) 2017 Nicholas Martin Booker
# Copyright (C) 2016 Michael Scherer
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

import dnf
import iniparse.compat as ini
import subprocess
import logging

class ProxyAutodetect(dnf.Plugin):
    name = 'proxy-autodetect'

    def __init__(self, base, cli):
        super(ProxyAutodetect, self).__init__(base, cli)
        self.base = base
        self.logger = logging.getLogger(self.name)

    def config(self):
        conf = self.read_config(self.base.conf, self.name)
        # # Following conditional cargo-culted from torproxy in dnf-plugins-extras
        # if not conf.has_section('main') or not conf.getboolean("main", "enabled"):
        #     return

        self._proxy_cmd = None

        # Look for our config
        if not conf.has_section(self.name):
            return
        try:
            self._proxy_cmd = conf.get(self.name, "program")
        except ini.Error:
            return

        if not self._proxy_cmd:
            # No override should happen
            return

        self.logger.debug("proxy-autodetect/program: {}".format(self._proxy_cmd))
        # Run the program and get the output
        try:
            proc = subprocess.Popen(self._proxy_cmd, stdout=subprocess.PIPE)
        except IOError as exc:
            self.logger.error("proxy-autodetect/program did not execute: {}".format(exc))
            return
        (stdout, _) = proc.communicate()
        self.logger.error("Script output: {}".format(stdout))
        detected_proxy = stdout.rstrip()

        if not detected_proxy:
            self.logger.error("{} returned empty stdout - no need to set proxy".format(self._proxy_cmd))
            return

        # Set the proxy
        self.logger.error("{} returned {}".format(self._proxy_cmd, detected_proxy))
        self.base.proxy = detected_proxy
        for repo in self.base.repos.values():
            repo.proxy = detected_proxy
