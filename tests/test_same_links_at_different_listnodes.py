# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from tests.models import Student, Role


class TestCase():
    """
    Same links at different listnodes under same class shouldn't affect each other.
    They should be independent.

    Test example architecture:

    class Student(Model):

        class Lecturer(ListNode):
            role = Role()

        class Lectures(ListNode):
            role = Role()

    """

    # First role is taken.
    first_role = Role.objects.get('W6lg6WmtQMHStCxpxBJjUFasfA7')
    # Second role is taken.
    second_role = Role.objects.get('65XrcpfYKzOK4tesQLA0awArpGH')
    # First role's student set is cleared.
    first_role.student_set.clear()
    # Second role's student set is cleared.
    second_role.student_set.clear()
    # First and second roles are saved.
    first_role.save()
    second_role.save()

    # Student instance is created.
    student = Student()
    # First and second roles' student sets are controlled.
    assert len(first_role.student_set) == 0
    assert len(second_role.student_set) == 0
    # Student's Lecturer list node's role field is assigned to first_role.
    student.Lecturer(role=first_role)
    # Student instance is saved.
    student.save()
    # Student's Lecturer list increases one, it is controlled.
    assert len(student.Lecturer) == 1
    # Student's Lectures list remains same, it is controlled.
    assert len(student.Lectures) == 0
    # Student's Lecturer data's role info is controlled.
    assert student.Lecturer[0].role == first_role
    # First role's student set number should increase one.
    assert len(first_role.student_set) == 1
    # First role's student set's student object's data is controlled.
    # Role info is controlled whether it is true or not.
    assert first_role.student_set[0].student.clean_value()['lecturer'][0]['role_id'] == first_role.key
    assert first_role.student_set[0].student.clean_value()['lectures'] == []

    # Student's Lectures list node's role field is assigned to first_role.
    student.Lectures(role=first_role)
    # Student instance is saved.
    student.save()

    # Lecturer and Lectures listnodes' number should be 1.
    assert len(student.Lectures) == 1
    assert len(student.Lecturer) == 1
    # Both's role data should be first_role
    assert student.Lecturer[0].role == first_role
    assert student.Lectures[0].role == first_role
    # First role student set's number should remain same.
    assert len(first_role.student_set) == 1
    # First role's student set's student object's data is controlled.
    # Role info is controlled whether it is true or not.
    assert first_role.student_set[0].student.clean_value()['lecturer'][0]['role_id'] == first_role.key
    assert first_role.student_set[0].student.clean_value()['lectures'][0]['role_id'] == first_role.key

    # Student's Lecturer list node's role field is changed from first_role to second_role.
    student.Lecturer[0].role = second_role
    # Student instance is saved.
    student.save()

    # Student's Lecturer list number should be 1.
    assert len(student.Lecturer) == 1
    # Student's Lectures list number should be 1.
    assert len(student.Lectures) == 1
    # Changes are controlled.
    assert student.Lecturer[0].role == second_role
    assert student.Lectures[0].role == first_role
    # # Second role's student set number should increase one.
    # assert len(second_role.student_set) == 1
    # # Second role's student set's student object's data is controlled.
    # assert second_role.student_set[0].student.clean_value()['lecturer'][0]['role_id'] == second_role.key
