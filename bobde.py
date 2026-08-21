# Currency Converter in Python

# Predefined exchange rates with USD as the base currency
exchange_rates = {
    "USD": 1.0,
    "INR": 83.50,
    "EUR": 0.92,
    "GBP": 0.78,
    "JPY": 154.50,
    "AUD": 1.52
}


# Function to convert currency
def convert_currency(amount, from_currency, to_currency):
    # Convert source currency to USD
    amount_in_usd = amount / exchange_rates[from_currency]

    # Convert USD to target currency
    converted_amount = amount_in_usd * exchange_rates[to_currency]

    return converted_amount


# Display available currencies
print("===== Currency Converter =====")
print("Available Currencies:")
print("USD - US Dollar")
print("INR - Indian Rupee")
print("EUR - Euro")
print("GBP - British Pound")
print("JPY - Japanese Yen")
print("AUD - Australian Dollar")

try:
    # Take input from user
    from_currency = input("\nEnter source currency: ").upper()
    to_currency = input("Enter target currency: ").upper()
    amount = float(input("Enter amount: "))

    # Check whether currencies are available
    if from_currency not in exchange_rates:
        print("Invalid source currency!")

    elif to_currency not in exchange_rates:
        print("Invalid target currency!")

    elif amount <= 0:
        print("Amount must be greater than zero!")

    else:
        # Perform conversion
        result = convert_currency(
            amount,
            from_currency,
            to_currency
        )

        print("\n===== Conversion Result =====")
        print(f"{amount:.2f} {from_currency} = "
              f"{result:.2f} {to_currency}")

except ValueError:
    print("Invalid amount! Please enter a number.")
except Exception as e:
    print("Something went wrong:", e)