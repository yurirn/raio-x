from app.services import unused_password_numbers


def test_unused_passwords_finds_daily_gaps():
    assert unused_password_numbers([1, 2, 4, 5, 7, 10]) == [3, 6, 8, 9]


def test_unused_passwords_empty_when_sequence_is_complete():
    assert unused_password_numbers([1, 2, 3]) == []
    assert unused_password_numbers([]) == []


def test_unused_passwords_ignore_numbers_after_the_highest_used():
    assert unused_password_numbers([3, 6, 12]) == [1, 2, 4, 5, 7, 8, 9, 10, 11]
