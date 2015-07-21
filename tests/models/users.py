# -*-  coding: utf-8 -*-
"""
data models for tests
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

from pyoko.model import Model, ListNode, field

"""

Sorgular
Bilgisayar mühendisliği 1. sınıfta Math101 dersinin 2. dönem 2. vizesinden 60 - 80 almış öğrencilerin listesi
Sosyal Bilimler Enstitüsünde 2010 - 2015 yılları arasında kademe cezası almış, kadın personellerin listesi. (kademe cezası önceki yıla göre kademe farklarına göre bulunabilir.)
Tıp fakültesinde, en az lise mezunu, kadro derecesi 7 den büyük, askerlik engeli bulunmayan personeller.
Bir öğrencinin seçmek istediği bir derse bağlı olan ön şartlı ders notu
Bir dersin genel sınavına (final) girmeye hak kazanmış öğrencilerin listesi
Belirli bir tarihe kadar sisteme not girmesi beklenen hocaların listesi. (sınavın yapıldığı tarihi takiben max 15 gün, sonraki sınav tarihinden min 7 gün önce gibi sabit birkaç kural söz konusu.)

Create ve Update islemleri

Yeni ogrenci yarat
Yeni personel yarat
Ogrenci ozluk bilgisi guncelle
Okul lokasyon bilgisi guncelle

Raporlar

Fakülte, bölüm ve program başına beklenen harç miktarları
Fakülte, bölüm ve program başına hocalara ödenecek beklenen ek ders ücretleri
Bir akademik personelin performansına dair son iki yılda danışmanlığını yaptığı öğrencilerin not ortalaması
Yıllara göre mezunların başarı ortalaması (her programın mezuniyet için öğrencilerin tutturması gereken asgari bir program mezuniyet ortalaması değeri vardır. öğrenciler bu değerin neresindedir?)
Azami öğretim süresine gelmiş ve mezun olmayacak öğrencilerin listesi


"""

class User(Model):
    name = field.String('Full Name', index=True)

# class Unit(Model):
#     parent = field.Link("Unit")
#     name = field.String()
#     type = field.String()

# class Location(Model):
#     unit = Unit()
#     name = field.String()


class Employee(Model):
    usr = User(one_to_one=True)
    role = field.String("Role", index=True)

    def __repr__(self):
        return "Employee with %s role" % self.role

class TimeTable(Model):
    lecture = field.String("Lecture", index=True)
    week_day = field.Integer("Week day", index=True)
    hours = field.Integer("Hours", index=True)

    def __unicode__(self):
        return self.lecture

class Scholar(Model):
    name = field.String("Name", index=True)


    def __unicode__(self):
        return self.name

    class TimeTables(ListNode):
        timetable = TimeTable()
        confirmed = field.Boolean("Is confirmed", index=True)

        def __str__(self):
            return self.timetable.__repr__()
