import re
import csv
from collections import UserDict
from datetime import datetime


class Field:
    def __init__(self, value):
        if not self.is_valid(value):
            raise ValueError("Invalid value")
        self.__value = value

    def __str__(self):
        return str(self.__value)

    def is_valid(self, value):
        return True

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if not self.is_valid(value):
            raise ValueError("Invalid value")
        self.__value = value


class Name(Field):

    def is_valid(self, value):
        for i in value:
            if not (i.isalpha() or i.isspace()):
                return False
        return True


class Phone(Field):

    def is_valid(self, value):
        if not value.isdigit() or len(value) < 10:
            raise ValueError('Invalid phone number format')
        return True


class Birthday(Field):

    def is_valid(self, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError as e:
            raise ValueError(f"Wrong date format: {e}")


class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.birthday = Birthday(birthday) if birthday else None
        self.phones = []

    def add_phone(self, phone):
        new_number = Phone(phone)
        self.phones.append(new_number)

    def remove_phone(self, phone):
        phones_to_remove = filter(lambda p: p.value == phone, self.phones)
        self.phones.remove(list(phones_to_remove)[0])

    def edit_phone(self, old_number, new_number):
        found = False
        if not new_number.isdigit() or len(new_number) < 10:
            raise ValueError('Invalid phone number format')
        for phone in self.phones:
            if phone.value == old_number:
                phone.value = new_number
                found = True
                break

        if not found:
            raise ValueError(
                f"Phone number '{old_number}' not found in the record."
                )

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        return (
            f"Contact name: {self.name.value}, "
            f"phones: {'; '.join(p.value for p in self.phones)}"
        )

    def days_to_birthday(self):
        if self.birthday:
            current_date = datetime.now()
            birthday_this_year = datetime(
                current_date.year,
                self.birthday.value.month,
                self.birthday.value.day
            )
            difference = birthday_this_year - current_date
            if current_date > birthday_this_year:
                birthday_next_year = datetime(
                    current_date.year + 1,
                    self.birthday.value.month,
                    self.birthday.value.day
                )
                difference = birthday_next_year - current_date
            return difference.days
        else:
            return None


class AddressBook(UserDict):

    def add_record(self, record):
        if record.name.value not in self.data:
            self.data[record.name.value] = record
        else:
            raise ValueError('The contact with this name already exists')

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def iterator(self, record_number):
        counter = 0
        while counter < len(self.data):
            records_slice = list(
                self.data.values()
            )[counter:counter + record_number]
            yield records_slice
            counter += record_number

    def address_book_writer(self, filename='address_book.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            field_names = ['contact name', 'phone', 'birthday']
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            for record in self.data.values():
                writer.writerow({
                    'contact name': record.name.value,
                    'phone': '; '.join(phone.value for phone in record.phones),
                    'birthday': (
                        str(record.birthday.value) if record.birthday else ''
                    )
                })

    def address_book_reader(self, filename='address_book.csv'):
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['contact name']
                phone = row['phone']
                birthday = row['birthday']
                record = Record(name, birthday)
                record.add_phone(phone)
                self.add_record(record)


def input_error(func):
    def inner(*args):
        try:
            return func(*args)
        except KeyError:
            return 'Enter user name'
        except ValueError:
            return 'The contact with this name already exists'
        except IndexError:
            return 'Contact not found'
    return inner


@input_error
def hello_handler():
    return 'How can I help you?'

@input_error
def add_handler(address_book, command):
    pattern = r'^add [a-zA-Zа-яА-Я]{2,} \d{10,}$'
    if re.fullmatch(pattern, command):
        splitted_command = command.split()
        name = splitted_command[1]
        phone = splitted_command[2]
        if name not in address_book.data and \
           phone not in [record.phones for record in address_book.data.values()]:
            record = Record(name)
            record.add_phone(phone)
            address_book.add_record(record)
        return (
            f'Contact {name} with phone {phone} '
            f'has been added to the contacts'
        )
    else:
        return ('Invalid command. Please follow the format: '
                'add name(at least 2 characters) phone(at least 10 digits)')


@input_error
def change_handler(address_book, command):
    pattern = r'^change [a-zA-Zа-яА-Я]{2,} \d{10,}$'
    if re.fullmatch(pattern, command):
        splitted_command = command.split()
        name = splitted_command[1]
        new_phone = splitted_command[2]
        record = address_book.find(name)
        if record:
            record.edit_phone(record.phones[0].value, new_phone)
            return f'Phone has been changed for {name} to {new_phone}'
        else:
            raise IndexError
    else:
        return ('Invalid command. Please follow the format: '
                'change name(at least 2 characters) phone(at least 10 digits)')


@input_error
def phone_handler(address_book, command):
    pattern = r'^phone [a-zA-Zа-яА-Я]{2,}$'
    if re.fullmatch(pattern, command):
        splitted_command = command.split()
        name = splitted_command[1]
        record = address_book.find(name)
        if record:
            return f'The phone number for {name} is {record.phones[0].value}'
        else:
            raise IndexError
    else:
        return (
            'Invalid command. Please follow the format: '
            'phone name(at least 2 characters)'
        )

@input_error
def show_all_handler(address_book):
    if not address_book.data:
        return 'No contacts found'
    else:
        result = ''
        for record in address_book.data.values():
            phones_info = "; ".join(str(phone.value) for phone in record.phones)
            result += f'Contact name: {record.name.value}, phones: {phones_info}\n'
        return result


@input_error
def search_handler(address_book, command):
    splitted_command = command.split()
    if len(splitted_command) != 2 or not splitted_command[1].isalnum():
        return ('Invalid command. Please follow the format: '
                'search letter or digit')
    search_data = splitted_command[1]
    user_list = []
    for record in address_book.data.values():
        if search_data.isalpha():
            pattern = re.compile(f'{search_data}', re.IGNORECASE)
            if re.search(pattern, str(record.name.value)):
                user_list.append(str(record.name.value))
        elif search_data.isdigit():
            for phone in record.phones:
                if search_data in phone.value:
                    user_list.append(str(record.name.value))
    return user_list


@input_error
def exit_handler():
    return 'Good bye!'


@input_error
def main(address_book):
    address_book.address_book_reader()
    handlers_with_command = {
        'add': add_handler,
        'change': change_handler,
        'phone': phone_handler,
        'search': search_handler
    }

    handlers_without_command = {
        'hello': hello_handler,
        'show all': show_all_handler,
        'good bye': exit_handler,
        'close': exit_handler,
        'exit': exit_handler
    }

    while True:
        command = input('Please enter command: ').lower()

        for prefix, handler in handlers_with_command.items():
            if command.startswith(prefix):
                print(handler(address_book, command))
                break
        for prefix, handler in handlers_without_command.items():
            if command.startswith(prefix):
                if prefix == 'show all':
                    print(handler(address_book))
                    break
                print(handler())
                break

        if command in [',', 'good bye', 'close', 'exit']:
            address_book.address_book_writer()
            break


if __name__ == "__main__":
    address_book = AddressBook()
    main(address_book)
