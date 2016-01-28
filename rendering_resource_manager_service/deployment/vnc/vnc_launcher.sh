#!/bin/sh
#[ -r /etc/sysconfig/i18n ] && . /etc/sysconfig/i18n

# Copyright (c) 2014-2016, Human Brain Project
#                          Cyrille Favreau <cyrille.favreau@epfl.ch>
#
# This file is part of RenderingResourceManager
# <https://github.com/BlueBrain/RenderingResourceManager>
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3.0 as published
# by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# All rights reserved. Do not distribute without further notice.

# Remove desktop icons
gconftool-2 --type boolean --set /apps/nautilus/desktop/computer_icon_visible false
gconftool-2 --type boolean --set /apps/nautilus/desktop/trash_icon_visible false
gconftool-2 --type boolean --set /apps/nautilus/desktop/home_icon_visible false

# Start VNC Server
export LANG
export SYSFONT
vncconfig -iconic &
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
OS=`uname -s`
rm -f *.log *.pid
module purge
module load BBP/viz/latest
export PARAMS=
while (( $# > 0 ))
do
  export PARAMS="$PARAMS $1"
  shift
done
vnc_response="$(vncserver -geometry 640x480 2>&1)"
export vnc_display=`echo "${vnc_response}" | sed '/New.*desktop.*is/!d' | awk -F" desktop is " '{print $2}' | awk -F":" '{print $2}'`
echo "VNC Display:${vnc_display}"

# Start IPython notebook
echo $PARAMS>params.log
EQ_WINDOW_IATTR_HINT_FULLSCREEN=1 DISPLAY=:${vnc_display} vglrun ipython $PARAMS 1>&2

# Stop VNC Server
vncserver -kill :${vnc_display} 1>&2

