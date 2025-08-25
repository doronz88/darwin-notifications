import typer

from .api import notify


def main() -> None:
    typer.run(notify)


if __name__ == "__main__":
    main()
