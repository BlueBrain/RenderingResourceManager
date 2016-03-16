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

#!/bin/sh
#[ -r /etc/sysconfig/i18n ] && . /etc/sysconfig/i18n

# Disable desktop
gconftool-2 --type boolean --set /apps/nautilus/desktop/computer_icon_visible false
gconftool-2 --type boolean --set /apps/nautilus/desktop/trash_icon_visible false
gconftool-2 --type boolean --set /apps/nautilus/desktop/home_icon_visible false
gconftool-2 --type boolean --set /apps/nautilus/lockdown/disable_context_menus 1
gconftool-2 --type boolean --set /apps/nautilus/preferences/show_desktop false
gconftool-2 -s -t list --list-type string /desktop/gnome/session/required_components_list [filemanager,windowmanager]
gconftool-2 -s -t string /desktop/gnome/session/required_components/panel ''

# Start VNC server
export LANG
export SYSFONT
vncconfig -iconic &
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
OS=`uname -s`
module purge
module load BBP/viz/latest
export PARAMS=
while (( $# > 0 ))
do
  export PARAMS="$PARAMS $1"
  shift
done
vnc_response="$(vncserver -geometry 1920x1080 2>&1)"
export vnc_display=`echo "${vnc_response}" | sed '/New.*desktop.*is/!d' | awk -F" desktop is " '{print $2}' | awk -F":" '{print $2}'`
echo "VNC Display:${vnc_display}"

# Start Livre
DISPLAY=:${vnc_display} vglrun livre $PARAMS 1>&2
    
# Kill VNC server
vncserver -kill :${vnc_display} 1>&2

