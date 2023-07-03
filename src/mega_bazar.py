from csv import DictReader
from re import sub
from unicodedata import normalize


def encode(word):
    ascii_name = (
        normalize("NFKD", word).encode("ascii", errors="ignore").decode("ascii")
    )
    return ascii_name.upper()


def filter_names(person):  # sourcery skip: remove-unreachable-code
    encoded_names = encode(person).split()

    # return encoded_names[0], True  # for debug

    return encoded_names[0], ("MANANCIAL" in encoded_names) or (
        "PR" in encoded_names and "TONINHO" in encoded_names
    ) or ("ANA" in encoded_names and "CHIQUETTI" in encoded_names)


def valid_contacts(contacts_file):
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

            # TODO remove duplicates from phones
            phones = [
                sub("[^0-9]", "", num)
                for key in phone_keys
                if (phone_string := row[key])
                for num in phone_string.split(" ::: ")
            ]

            if name and phones:
                first_name, allow = filter_names(name)
                if allow:
                    contacts.append(
                        {
                            "name": name,
                            "phones": phones,
                            "first_name": first_name.capitalize(),
                        }
                    )
    return contacts
