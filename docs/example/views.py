# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from .models import Person, Unit

user = Person(first_name='Bugs')
user.last_name = 'Bunny'
contact_info = user.ContactInfo(email="foo@foo.com", city="Izmir")
contact_info.phone = "902327055555"
user.work = Unit(name="Acme").save()
user.home = Unit(name="Emac").save()
user.save()
