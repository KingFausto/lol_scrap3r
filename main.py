import argparse
from scraper import OpggScraper


def main():
    parser = argparse.ArgumentParser(description="champion builds scraped off of OP.GG")
    parser.add_argument("champion")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-a", "--aram", help="search for champion builds in ARAM", action="store_true"
    )
    group.add_argument(
        "-u", "--urf", help="search for champion builds in URF", action="store_true"
    )
    group.add_argument(
        "-q",
        "--soloq",
        help="search for champion builds in SOLOQ",
        choices=["top", "jgl", "mid", "bot", "sup"],
        dest="role",
    )

    args = parser.parse_args()

    role: str = args.role
    champion: str = args.champion
    mode: str = ""

    if args.aram:
        mode = "aram"
    elif args.urf:
        mode = "urf"
    else:
        mode = "champion"

    scraper = OpggScraper(role=role, champion=champion, mode=mode)
    scraper.build_tree()


if __name__ == "__main__":
    main()
