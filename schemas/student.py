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

# f = Faker(locale='tr_TR')
f = Faker()

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%dT00:00:00Z"


def get_date_range(term=10):
    end = f.random_element([1, 1, 1, 1, 1, 6]) # some students did not  paid their tuition fees yet
    return [f.date_time_between('-%sd' % (30 * m),
                                '-%sd' % (30 * m)).strftime(DATE_FORMAT)
            for m in range(term * 6, end, -6)]



def data():
    first_name = f.first_name()
    last_name = f.last_name()
    name = "%s %s" % (first_name, last_name)
    active_term = f.random_int(1, 12)
    paid_tuition_fees = get_date_range(active_term)
    has_unpaid = active_term - len(paid_tuition_fees)
    unpaid_tuition_fees = [f.date_time_between('-180d', '-180d').strftime(DATE_FORMAT)] if has_unpaid else []
    return {
        "student_number_s": f.ean(),
        "name_s": name,
        "join_date_dt": f.date_time_between('-4y').strftime(DATE_FORMAT),
        "identity_information": {
            "tc_no_l": str(f.random_int(10000000000, 19999999999)),
            "id_card_serial": "%s%s%s" % (f.random_letter(), f.random_digit(), f.random_digit()),
            "id_card_no": str(f.random_int(10000, 99999)),
            "first_name_s": first_name,
            "last_name_s": last_name,
            "name_of_father_s": f.first_name(),
            "name_of_mother_s": f.first_name_female(),
            "place_of_birth_s": f.city(),
            "date_of_birth_dt": f.date_time_between('-40y', '-16y').strftime(DATE_FORMAT),
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
                    "name_ss": f.name(),
                    "street_ss": f.street_name(),
                    "postal_code_ss": f.postcode(),
                    "city_ss": f.city(),
                    "town_ss": f.city_prefix(),
                    "neighborhood_ss": f.city()
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
            "last_login_dt": f.date_time_this_year().strftime(DATE_TIME_FORMAT),
            "last_login_ip": f.ipv4(),
            "password_reset": {
                "token": f.sha256(),
                "request_ip": f.ipv4(),
                "date": f.date_time_this_year().strftime(DATE_TIME_FORMAT),
                "client": f.user_agent()
            },
            "password_last_changed_date": f.date_time_this_year().strftime(DATE_TIME_FORMAT),
        },
        "payment_information": {
            "iban": "%s%s%s" % (f.country_code(), f.ean(), f.ean()),
            "tuition_fees": {
                "paid_ss": paid_tuition_fees,
                "unpaid_ss": unpaid_tuition_fees,
                "charge_back_ss": [],
            }
        },
        "scholarship": {
            "active_term": active_term,
        },
        "lectures": [
            {
                "code_ss": f.color_name()[:3].upper(),
                "name_ss": f.sentence(5),
                "credit": f.random_int(1, 8),
                "ects_credit": f.random_int(1, 8),
                "note": f.random_int(1, 100),
                "exams": [
                    {
                        "type": f.random_element(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']),
                        "date": f.date_time_between('-4y').strftime(DATE_FORMAT),
                        "points": f.random_int(1, 100)
                    } for i in range(randint(1, 10))
                ]
            } for i in range(randint(5, 40))
        ]
    }
