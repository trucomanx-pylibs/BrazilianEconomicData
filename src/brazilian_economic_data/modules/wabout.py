import brazilian_economic_data.about as about


def show_about():
    print("\n" + "=" * 50)
    print(f"{about.__program_name__}")
    print("=" * 50)
    print(f"Version      : {about.__version__}")
    print(f"Package      : {about.__package__}")
    print(f"Author       : {about.__author__}")
    print(f"Email        : {about.__email__}")
    print(f"Description  : {about.__description__}")
    print(f"Source       : {about.__url_source__}")
    print(f"Documentation: {about.__url_doc__}")
    print(f"Funding      : {about.__url_funding__}")
    print(f"Bugs         : {about.__url_bugs__}")
    print("=" * 50 + "\n")
