from src.frontend.api_client import (
    API_BASE_URL,
    APIClientError,
    get_health
)


def main():
    print("=" * 55)
    print("BANKING CREDIT RISK — API CONNECTION TEST")
    print("=" * 55)

    print(f"\nAPI URL: {API_BASE_URL}")

    try:
        response = get_health()

        print("\nConnection: PASS")
        print("HTTP Status: 200")
        print("API Response:")
        print(response)

    except APIClientError as error:
        print("\nConnection: FAIL")
        print(f"Reason: {error}")

        if error.status_code is not None:
            print(f"HTTP Status: {error.status_code}")

        raise SystemExit(1)


if __name__ == "__main__":
    main()