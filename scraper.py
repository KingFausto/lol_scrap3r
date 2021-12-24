import re
import requests
from bs4 import BeautifulSoup
from constants import ROLES, MYTHIC_ITEMS, COLORS
from anytree import Node, RenderTree
from colorama import init, deinit, Fore, Style


class OpggScraper:
    def __init__(self, role: str, champion: str, mode: str = "champion"):
        self.role: str = role
        self.champion: str = champion
        self.mode: str = mode
        self.soup: BeautifulSoup = None
        self.main_table: list = []

    # helper function to clean up information from certain queries
    def parse_results(self, results, regex=r"&gt;(.*?)&"):
        return [re.search(regex, str(i)).group(1) for i in results]

    def cook_soup(self):
        url = f"https://www.op.gg/{self.mode}/{self.champion}/statistics/"
        if self.role:
            self.role = ROLES["jgl"] if self.role == "jgl" else ROLES[self.role]
            url += self.role
        # get the main table with all the information
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers)
        self.soup = BeautifulSoup(r.text, "html.parser")
        self.main_table = self.soup.find_all("td", class_="champion-overview__data")
        if not self.role:
            self.role = self.soup.find(
                "h1", class_="champion-stats-header-info__name"
            ).text.split()[-1]

    def get_patch(self):
        return self.soup.find(
            "div", class_="champion-stats-header-version"
        ).text.split()[-1]

    def get_summoners(self):
        summoner_pick_rates = self.soup.find_all(
            "td", class_="champion-overview__stats champion-overview__stats--pick"
        )
        summoners: list = []

        for i in range(0, 2):
            summoners.append(
                self.parse_results(
                    self.main_table[i].find_all(
                        "li", class_="champion-stats__list__item"
                    )
                )
                + summoner_pick_rates[i].text.strip().split("\n")[:-1]
            )
            summoners[
                i
            ] = f"{' + '.join(summoners[i][:2])} {Style.BRIGHT + Fore.BLACK}({summoners[i][2]} PR){Style.RESET_ALL}"

        return summoners

    def get_skill_order(self):
        skill_order = (
            self.main_table[2].find("table", class_="champion-skill-build__table").text
        )
        return skill_order.replace("\t", "").replace("\n", "")[-15:]

    def get_items(self):
        pick_rate = self.soup.find_all(
            "td",
            class_="champion-overview__stats champion-overview__stats--pick champion-overview__border",
        )

        items: list = []
        for i in range(3, 13):
            items.append(
                self.parse_results(
                    self.main_table[i].find_all(
                        "li", class_="champion-stats__list__item tip"
                    )
                )
                + pick_rate[i - 3].text.strip().split("\n")
            )

            for j in range(len(items[i - 3][:-2])):
                if items[i - 3][j] in MYTHIC_ITEMS:
                    items[i - 3][j] = (
                        Style.BRIGHT + Fore.MAGENTA + items[i - 3][j] + Style.RESET_ALL
                    )
            if i < 10:
                items[
                    i - 3
                ] = f"{' + '.join(items[i - 3][:-2])} {Style.BRIGHT + Fore.BLACK}({items[i - 3][-2]} PR){Style.RESET_ALL}"
            else:
                items[
                    i - 3
                ] = f"{items[i - 3][0]} {Style.BRIGHT + Fore.BLACK}({items[i - 3][1]} PR){Style.RESET_ALL}"

        return items

    def get_runes(self):
        keystone = self.parse_results(
            self.main_table[13].find_all(
                "div",
                class_="perk-page__item perk-page__item--keystone perk-page__item--active",
            )
        )[0]

        runes = self.parse_results(
            self.main_table[13].find_all(
                "div", class_="perk-page__item perk-page__item--active"
            )
        )

        shards = self.parse_results(
            self.main_table[13].find_all("img", class_="active tip"), r"span&gt;(.*?)&"
        )

        rune_trees = self.soup.find(
            "div", class_="champion-stats-summary-rune__name"
        ).text.split(" + ")
        primary_color = COLORS[rune_trees[0]]
        secondary_color = COLORS[rune_trees[1]]

        return keystone, runes, shards, primary_color, secondary_color

    def build_tree(self):
        self.cook_soup()
        current_patch = self.get_patch()
        root_title = f"{self.champion.title()} {self.role if self.mode == 'champion' else self.mode.title()} Builds for Patch {current_patch}"
        root = Node(Style.BRIGHT + Fore.GREEN + root_title + Style.RESET_ALL)

        # summoners
        summoners = self.get_summoners()
        summoners_node = Node(
            Style.BRIGHT + Fore.BLUE + "Summoner Spells" + Style.RESET_ALL, parent=root
        )
        for i in range(0, 2):
            Node(summoners[i], parent=summoners_node)

        # skills
        skills = self.get_skill_order()
        skills_node = Node(
            Style.BRIGHT + Fore.BLUE + "Skill Order" + Style.RESET_ALL, parent=root
        )
        Node(skills, parent=skills_node)

        # items
        items = self.get_items()
        items_node = Node(
            Style.BRIGHT + Fore.BLUE + "Item Builds" + Style.RESET_ALL, parent=root
        )
        starters = Node(
            Style.BRIGHT + Fore.RED + "Starter Items" + Style.RESET_ALL,
            parent=items_node,
        )
        for i in range(0, 2):
            Node(items[i], parent=starters)

        builds = Node(
            Style.BRIGHT + Fore.RED + "Recommended Builds" + Style.RESET_ALL,
            parent=items_node,
        )
        for i in range(2, 7):
            Node(items[i], parent=builds)

        boots = Node(
            Style.BRIGHT + Fore.RED + "Boots" + Style.RESET_ALL, parent=items_node
        )
        for i in range(7, 10):
            Node(items[i], parent=boots)

        # runes
        keystone, runes, shards, primary_color, secondary_color = self.get_runes()
        runes_node = Node(
            Style.BRIGHT + Fore.BLUE + "Runes" + Style.RESET_ALL, parent=root
        )
        keystone_node = Node(primary_color + keystone + Fore.RESET, parent=runes_node)

        for i in range(len(runes)):
            if i < 3:
                Node(primary_color + runes[i] + Fore.RESET, parent=keystone_node)
            else:
                Node(secondary_color + runes[i] + Fore.RESET, parent=keystone_node)

        for i in range(len(shards)):
            Node(
                Style.BRIGHT + Fore.YELLOW + shards[i] + Style.RESET_ALL,
                parent=keystone_node,
            )

        # display the tree
        init()
        for pre, _, node in RenderTree(root):
            print(f"{pre} {node.name}")
        deinit()
