# Faker Tool

Generate fake identity information based on country codes using the randomuser.me API.

## Features

- Generate realistic fake user data including:
  - Full name (title, first name, last name)
  - Email address
  - Phone numbers (phone & cell)
  - Complete address (street, city, state, postal code)
  - Country with flag emoji
  - Age and date of birth
  - Username and password
  - Profile picture URL

## Usage

### Command
```
/fake <country_code>
```

### Examples
```
/fake us    - Generate fake US identity
/fake gb    - Generate fake UK identity
/fake ca    - Generate fake Canadian identity
```

The bot accepts any country code. If the API supports it, it will return fake data for that country.

## API

This tool uses the [randomuser.me API](https://randomuser.me) to generate realistic fake user data.

## Files

- `fake.py` - Main module with API integration and formatting functions
- `__init__.py` - Package initialization
- `README.md` - This documentation file
