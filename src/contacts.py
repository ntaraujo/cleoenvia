from csv import DictReader
from re import sub
from unicodedata import normalize


def encode(word):
    ascii_name = (
        normalize("NFKD", word).encode("ascii", errors="ignore").decode("ascii")
    )
    return ascii_name.upper()


def get_positive_filters(file):
    with open(file, encoding="utf-8") as f:
        return [
            encode(lstrip).split() for line in f.readlines() if (lstrip := line.strip())
        ]


def filter_names(
    person, positive_filters=None
):  # sourcery skip: remove-unreachable-code
    encoded_names = encode(person).split()

    # return encoded_names[0], True  # for debug

    return encoded_names[0], (
        any(
            all(single_filter in encoded_names for single_filter in filter_list)
            for filter_list in positive_filters
        )
        if positive_filters
        else True
    )


def valid_contacts(contacts_file, positive_filters=None):
    contacts = []

    with open(contacts_file, encoding="utf-8") as csv_file:
        csv_reader = DictReader(csv_file)
        phone_keys = [
            key
            for key in csv_reader.fieldnames
            if "phone" in (key_lower := key.lower()) and "value" in key_lower
        ]

        for row in csv_reader:
            name = row["Given Name"]
            if row["Additional Name"]:
                name += " " + row["Additional Name"]
            if row["Family Name"]:
                name += " " + row["Family Name"]

            phones = list(
                {
                    sub("[^0-9]", "", num)
                    for key in phone_keys
                    if (phone_string := row[key])
                    for num in phone_string.split(" ::: ")
                }
            )

            if name and phones:
                first_name, allow = filter_names(name, positive_filters)
                if allow:
                    contacts.append(
                        {
                            "name": name,
                            "phones": phones,
                            "first_name": first_name.capitalize(),
                        }
                    )
    return contacts


def filtered_contacts(contacts_file, positive_filters_file):
    return valid_contacts(
        contacts_file, positive_filters=get_positive_filters(positive_filters_file)
    )


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv, find_dotenv
    import time

    _ = load_dotenv(find_dotenv())

    _contacts_file = os.environ["CLEO_ENVIA_CONTACTS_FILE"]
    _positive_filters_file = os.environ["CLEO_ENVIA_POSITIVE_FILTERS_FILE"]
    
    _result = filtered_contacts(_contacts_file, _positive_filters_file)
    
    for _contact in _result:
        print(_contact)
