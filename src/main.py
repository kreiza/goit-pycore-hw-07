from collections import UserDict
from datetime import datetime, date, timedelta
from typing import List
import sys


# Decorator for input error handling
def input_error(func):
    """
    Decorator to catch KeyError, ValueError, and IndexError in command handlers.

    :return: The function result or an error message.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as ve:
            return str(ve)
        except IndexError:
            return "Insufficient arguments provided."

    return wrapper


def parse_input(user_input: str) -> (str, List[str]):
    """
    Parse user input into a command and its arguments.

    :param user_input: The raw input string from the user.
    :return: A tuple with the command and a list of arguments.
    """
    parts = user_input.split()
    if not parts:
        return "", []
    command = parts[0].strip().lower()
    args = parts[1:]
    return command, args


# Basic field class
class Field:
    """
    Base class for record fields.

    :param value: The field value.
    """

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


# Name field (required)
class Name(Field):
    """
    Class for storing a contact's name.

    :param value: The contact's name.
    """

    def __init__(self, value: str) -> None:
        if not value:
            raise ValueError("Name cannot be empty.")
        super().__init__(value)


# Phone field with validation (10 digits)
class Phone(Field):
    """
    Class for storing a phone number with validation.

    :param value: The phone number as a string (must be exactly 10 digits).
    """

    def __init__(self, value: str) -> None:
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must consist of exactly 10 digits.")
        super().__init__(value)


# Birthday field (optional) with date validation (format DD.MM.YYYY)
class Birthday(Field):
    """
    Class for storing a birthday.

    :param value: The birthday as a string in DD.MM.YYYY format.
    :raises ValueError: If the date is not in the correct format.
    """

    def __init__(self, value: str) -> None:
        try:
            # Convert string to a datetime.date object
            birthday_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        self.value = birthday_date

    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")


# Record stores a contact's name, phones, and optional birthday.
class Record:
    """
    Class for storing information about a contact.

    :param name: The contact's name.
    """

    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.birthday = None

    def add_phone(self, phone: str) -> None:
        """
        Add a phone number to the record.

        :param phone: A phone number as a string.
        """
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        """
        Remove a phone number from the record.

        :param phone: The phone number to remove.
        """
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                break

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """
        Edit an existing phone number.

        :param old_phone: The existing phone number.
        :param new_phone: The new phone number.
        """
        for idx, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[idx] = Phone(new_phone)
                break

    def find_phone(self, phone: str) -> str:
        """
        Find a phone number in the record.

        :param phone: The phone number to search for.
        :return: The phone number if found, or an empty string.
        """
        for p in self.phones:
            if p.value == phone:
                return p.value
        return ""

    def add_birthday(self, birthday_str: str) -> None:
        """
        Add or update the birthday for the contact.

        :param birthday_str: The birthday as a string in DD.MM.YYYY format.
        """
        self.birthday = Birthday(birthday_str)

    def __str__(self) -> str:
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = str(self.birthday) if self.birthday else "Not set"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {birthday_str}"


# AddressBook for managing multiple records.
class AddressBook(UserDict):
    """
    Class for storing and managing contact records.
    """

    def add_record(self, record: Record) -> None:
        """
        Add a record to the address book.

        :param record: The Record to add.
        """
        self.data[record.name.value] = record

    def find(self, name: str) -> Record:
        """
        Find a record by contact name.

        :param name: The contact name to search for.
        :return: The Record if found, otherwise None.
        """
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """
        Delete a record by contact name.

        :param name: The contact name of the record to delete.
        """
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> List[Record]:
        """
        Get a list of contacts with birthdays in the next 7 days.

        :return: A list of Record objects.
        """
        today = date.today()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                # Create birthday for current year
                bday = record.birthday.value.replace(year=today.year)
                if bday < today:
                    bday = bday.replace(year=today.year + 1)
                delta = (bday - today).days
                # Adjust if birthday falls on weekend
                if bday.weekday() == 5:
                    bday += timedelta(days=2)
                elif bday.weekday() == 6:
                    bday += timedelta(days=1)
                if 0 <= delta <= 7:
                    upcoming.append(record)
        return upcoming


# Command handlers decorated with input_error
@input_error
def add_contact(args: list, book: AddressBook) -> str:
    """
    Add a new contact or update an existing one with a phone number.

    :param args: A list where the first element is the name and second is a phone.
    :param book: The AddressBook instance.
    :return: A confirmation message.
    """
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: list, book: AddressBook) -> str:
    """
    Change an existing contact's phone number.

    :param args: A list with the name, old phone, and new phone.
    :param book: The AddressBook instance.
    :return: A confirmation message.
    """
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args: list, book: AddressBook) -> str:
    """
    Show phone numbers for a given contact.

    :param args: A list with the contact name.
    :param book: The AddressBook instance.
    :return: The contact's phone numbers.
    """
    name = args[0]
    record = book.find(name)
    if record is None:
        return "Contact not found."
    return "; ".join(p.value for p in record.phones) if record.phones else "No phone numbers found."


def show_all(book: AddressBook) -> str:
    """
    Return all contacts in the address book.

    :param book: The AddressBook instance.
    :return: A formatted string of all contacts.
    """
    if not book.data:
        return "No contacts available."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: list, book: AddressBook) -> str:
    """
    Add or update a birthday for a contact.

    :param args: A list with the contact name and birthday (DD.MM.YYYY).
    :param book: The AddressBook instance.
    :return: A confirmation message.
    """
    name, birthday_str = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.add_birthday(birthday_str)
    return "Birthday added."


@input_error
def show_birthday(args: list, book: AddressBook) -> str:
    """
    Show the birthday for a given contact.

    :param args: A list with the contact name.
    :param book: The AddressBook instance.
    :return: The birthday as a string or a message if not set.
    """
    name = args[0]
    record = book.find(name)
    if record is None:
        return "Contact not found."
    return str(record.birthday) if record.birthday else "Birthday not set."


def birthdays(args: list, book: AddressBook) -> str:
    """
    Show contacts with birthdays in the next 7 days.

    :param args: Unused.
    :param book: The AddressBook instance.
    :return: A formatted list of contacts with upcoming birthdays.
    """
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    result = []
    for record in upcoming:
        bday_str = str(record.birthday) if record.birthday else "Not set"
        result.append(f"{record.name.value}: {bday_str}")
    return "\n".join(result)


@input_error
def change_birthday(args: list, book: AddressBook) -> str:
    """
    Change the birthday for a given contact.

    :param args: A list with the contact name and new birthday (DD.MM.YYYY).
    :param book: The AddressBook instance.
    :return: A confirmation message.
    """
    name, birthday_str = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.add_birthday(birthday_str)
    return "Birthday updated."


def main() -> None:
    """
    Run the CLI assistant bot.

    Supported commands:
    - add [name] [phone]
    - change [name] [old_phone] [new_phone]
    - phone [name]
    - all
    - add-birthday [name] [DD.MM.YYYY]
    - show-birthday [name]
    - birthdays
    - hello
    - close / exit
    """
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)
        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == '__main__':
    main()
