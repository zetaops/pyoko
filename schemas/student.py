# -*-  coding: utf-8 -*-
"""
test data schema for student bucket
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from random import randint
from faker import Faker

f = Faker(locale='tr_TR')

data = lambda: {
    "student_number_s": f.ean(),
    "tname_s": f.name(),
    "join_date_dt": f.date(),
    "identity_information": {
        "tc_no_l": str(f.random_int(10000000000, 19999999999)),
        "id_card_serial": "%s%s%s" % (f.random_letter(), f.random_digit(), f.random_digit()),
        "id_card_no": str(f.random_int(10000, 99999)),
        "first_name_s": f.first_name(),
        "last_name_s": f.last_name(),
        "name_of_father_s": f.first_name(),
        "name_of_mother_s": f.first_name_female(),
        "place_of_birth_s": f.city(),
        "date_of_birth_dt": f.date_time_between('-40y', '-16y').date().isoformat(),
        "city_s": f.city(),
        "town_s": f.city(),
        "neighborhood": f.city_prefix(),
        "logbook": str(f.random_int(100, 999)),
        "family_order": str(f.random_int(1, 3000)),
        "order": str(f.random_int(100, 9999))
    },
    "contact_information": {
        "addresses": [
            {
                "name_s": f.name(),
                "street_s": f.street_name(),
                "postal_code_i": f.postcode(),
                "city_s": f.city(),
                "town_s": f.city_prefix(),
                "neighborhood_s": f.city()
            } for i in range(randint(1, 3))
        ],
        "phones": {
            "gsm": f.phone_number(),
            "phone": f.phone_number()
        }
    },
    "auth_information": {
        "username_s": f.simple_profile()['username'],
        "password": f.sha256(),
        "email_s": f.email(),
        "last_login_dt": f.date_time_this_year().isoformat(),
        "last_login_ip": f.ipv4(),
        "password_reset": {
            "token": f.sha256(),
            "request_ip": f.ipv4(),
            "date": f.date_time_this_year().isoformat(),
            "client": f.user_agent()
        },
        "password_last_changed_date": f.date_time_this_year().isoformat(),
    },
    "payment_information": {
        "iban": "%s%s%s" % (f.country_code(), f.ean(), f.ean()),
        "fees": {
            "paids": {
                "date": f.date_time_this_year().isoformat()
            },
            "unpaids": {
                "last_pay_date": f.date_time_this_year().isoformat()
            },
            "charge_backs": {
                "date": f.date_time_this_year().isoformat()
            }
        }
    },
    "scholarship": {
        "active_term": f.random_int(1, 12)
    },
    "lectures": [
        {
            "code": f.color_name()[:3].upper(),
            "name": f.sentence(5),
            "credit": f.random_int(1, 8),
            "ects_credit": f.random_int(1, 8),
            "note": f.random_int(1, 100),
            "exams": [
                {
                    "type": f.random_element(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']),
                    "date": f.date_time_between('-4y').date().isoformat(),
                    "points": f.random_int(1, 100)
                } for i in range(randint(1, 10))
            ]
        } for i in range(randint(1, 40))
    ]
}