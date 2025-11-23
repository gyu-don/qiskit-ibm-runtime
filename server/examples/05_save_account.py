"""
Example: Save account configuration for local server.

This example shows how to save the local server configuration
so you don't have to specify it every time.
"""

from qiskit_ibm_runtime import QiskitRuntimeService

def save_local_account():
    """Save local server account configuration."""
    print("Saving local server account configuration...")

    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform",
        token="test-token-local",
        url="http://localhost:8000",
        name="local_mock_server",  # Give it a name
        set_as_default=False,  # Don't set as default (to avoid conflicts)
        overwrite=True  # Overwrite if already exists
    )

    print("✓ Account saved with name: 'local_mock_server'")


def load_local_account():
    """Load the saved local server configuration."""
    print("\nLoading saved account configuration...")

    # Just specify the name - all other settings are loaded automatically
    service = QiskitRuntimeService(name="local_mock_server")

    print("✓ Account loaded successfully")
    print(f"  URL: {service._account.url}")
    print(f"  Channel: {service._account.channel}")

    return service


def list_saved_accounts():
    """List all saved accounts."""
    print("\nListing all saved accounts:")
    print("-" * 60)

    saved_accounts = QiskitRuntimeService.saved_accounts()

    if not saved_accounts:
        print("  No saved accounts found")
    else:
        for name, details in saved_accounts.items():
            print(f"\n  Name: {name}")
            print(f"    URL: {details.get('url', 'N/A')}")
            print(f"    Channel: {details.get('channel', 'N/A')}")
            print(f"    Default: {details.get('default', False)}")


def delete_local_account():
    """Delete the saved local server configuration."""
    print("\nDeleting local server account...")

    QiskitRuntimeService.delete_account(name="local_mock_server")

    print("✓ Account deleted")


def main():
    print("="*60)
    print("Managing Local Server Account Configuration")
    print("="*60)

    # 1. List existing accounts
    list_saved_accounts()

    # 2. Save local server account
    print("\n" + "="*60)
    save_local_account()

    # 3. List accounts again to verify
    list_saved_accounts()

    # 4. Load the saved account
    print("\n" + "="*60)
    service = load_local_account()

    # 5. Try to use it
    print("\nTesting the loaded service...")
    try:
        backends = service.backends()
        print(f"✓ Service works! Found {len(backends)} backends")
    except Exception as e:
        print(f"⚠ Server returned error (expected if not implemented): {type(e).__name__}")

    # 6. Optionally delete (uncomment to clean up)
    # print("\n" + "="*60)
    # delete_local_account()
    # list_saved_accounts()

    print("\n" + "="*60)
    print("Done! You can now use:")
    print("  service = QiskitRuntimeService(name='local_mock_server')")
    print("="*60)


if __name__ == "__main__":
    main()
