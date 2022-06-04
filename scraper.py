import re
import requests
from bs4 import BeautifulSoup
from anytree import Node, RenderTree
from colorama import init, deinit, Fore, Style
from constants import ROLES, MYTHIC_ITEMS, COLORS

# TODO: fix adaptive shards


class OpggScraper:
    def __init__(self, role: str, champion: str, mode: str) -> None:
        self.role = role
        self.champion = champion
        self.mode = mode
        self._cook_soup()

    def _get_item_name_from_id(self, id: str) -> str:
        return self.item_ids[id]["name"]

    def _cook_soup(self) -> None:
        if self.mode == "champion":
            if self.role:
                url = f"https://www.op.gg/{self.mode}s/{self.champion}/{ROLES[self.role]}/build?region=global&tier=gold_plus"
            else:
                url = f"https://www.op.gg/{self.mode}/{self.champion}/build?region=global&tier=gold_plus"
        else:
            url = f"https://www.op.gg/modes/{self.mode}/{self.champion}/build?region=global"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
        }

        r = requests.get(url, headers=headers)
        self.soup = BeautifulSoup(r.content, "html.parser")

        latest_patch = requests.get(
            "https://ddragon.leagueoflegends.com/api/versions.json"
        ).json()[0]
        self.item_ids = requests.get(
            f"https://ddragon.leagueoflegends.com/cdn/{latest_patch}/data/en_US/item.json"
        ).json()["data"]
        return

    def get_patch(self):
        return re.search(r"\(.*(Season .*)\)", self.soup.title.text).group(1)

    def get_role(self):
        return re.search(r"\((.*)\,.*\)", self.soup.title.text).group(1)

    def get_summoners(self) -> list[str]:
        summoners: list = []
        css_class = (
            "css-1oyezvu e1cidvo94"
            if self.mode == "champion"
            else "css-18fgzez e1cidvo90"
        )
        for i, summoners_row in enumerate(self.soup.find_all("div", class_=css_class)):
            summoners.append(
                " + ".join([img.get("alt") for img in summoners_row.select("img")])
            )
            pickrates = summoners_row.find("div", class_="pick_rate").strong.text
            winrates = summoners_row.find("div", class_="win_rate").text
            summoners[i] += f" {Style.BRIGHT+Fore.BLACK}({pickrates} PR){Style.RESET_ALL}"
            summoners[i] += f" {Style.BRIGHT+Fore.YELLOW}({winrates} WR){Style.RESET_ALL}"

        return summoners

    def get_skill_order(self) -> str:
        return self.soup.find("div", class_="css-hkh81z e1dv0fw31").text

    def _generate_item_strings(self, table, check_for_mythics: bool = False, verbose: bool = False) -> list[str]:
        results: list = []
        for i, row in enumerate(table.tbody.find_all("tr")):
            item_ids = [
                re.search(r"item\/(\d*)\.", str(i)).group(1)
                for i in [img.get("src") for img in row.find_all("img")]
            ]
            if check_for_mythics:
                item_names = [self._get_item_name_from_id(id) for id in item_ids]
                results.append(
                    " + ".join(
                        [
                            f"{Style.BRIGHT + Fore.MAGENTA}{x}{Style.RESET_ALL}"
                            if x in MYTHIC_ITEMS
                            else x
                            for x in item_names
                        ]
                    )
                )
            else:
                results.append(
                    " + ".join([self._get_item_name_from_id(id) for id in item_ids])
                )
            if verbose:
                pickrates, winrates = row.find_all("strong")
                results[i] += f" {Style.BRIGHT+Fore.BLACK}({pickrates.text} PR){Style.RESET_ALL}"
                results[i] += f" {Style.BRIGHT+Fore.YELLOW}({winrates.text} WR){Style.RESET_ALL}"

        return results

    def get_items(self):
        if self.mode == "champion":
            starters_table, boots_table, items_table = self.soup.find_all(
                "table", class_="css-xcse24 exo2f213"
            )
        else:
            _, starters_table, boots_table, items_table = self.soup.find_all(
                "table", class_="css-xcse24 exo2f213"
            )

        starters = self._generate_item_strings(starters_table, verbose=True)
        boots = self._generate_item_strings(boots_table, verbose=True)
        items = self._generate_item_strings(items_table, verbose=False, check_for_mythics=True)

        return starters, boots, items

    def get_runes(self):
        keystone = self.soup.find("div", class_="css-r2m0dx e1o8f101").img.get("alt")
        runes = [
            rune.img.get("alt")
            for rune in self.soup.find_all("div", class_="css-1rjzcri e1o8f101")
        ]
        shards = [
            shard.get("alt")
            for shard in self.soup.find_all("img", class_="css-anaetp e1gtrici1")
        ]
        trees = [
            tree.string
            for tree in self.soup.find_all("h5", class_="css-nx19kd e1o8f100")
        ]
        primary_color, secondary_color = [COLORS[tree] for tree in trees]

        return keystone, runes, shards, primary_color, secondary_color

    def _create_node(self, text: str, parent: Node, color: str, bright: bool = False) -> Node:
        return Node(
            f"{Style.BRIGHT if bright else Style.NORMAL}{color}{text}{Style.RESET_ALL}",
            parent=parent,
        )

    def _create_title_node(self, text: str, parent: Node) -> Node:
        return self._create_node(text, parent, Fore.BLUE, bright=True)

    def _create_subtitle_node(self, text: str, parent: Node) -> Node:
        return self._create_node(text, parent, Fore.RED, bright=True)

    def build_tree(self) -> None:
        summoners = self.get_summoners()
        skills = self.get_skill_order()
        starters, boots, items = self.get_items()
        keystone, runes, shards, primary_color, secondary_color = self.get_runes()

        patch = self.get_patch()

        root_title = f"{self.champion.title()} {self.get_role() if self.mode == 'champion' else self.mode.upper()} Builds for {patch}"

        root = self._create_node(root_title, parent=None, color=Fore.MAGENTA, bright=True)

        # Summoners
        summoners_node = self._create_title_node("Summoner Spells", root)
        for summoners_group in summoners:
            Node(summoners_group, parent=summoners_node)

        # Skill Order
        skills_node = self._create_title_node("Skill Order", parent=root)
        Node(skills, parent=skills_node)

        # Item Builds
        items_node = self._create_title_node("Item Builds", root)
        starters_node = self._create_subtitle_node("Starter Items", items_node)
        for starter in starters:
            Node(starter, parent=starters_node)
        builds = self._create_subtitle_node("Recommended Builds", items_node)
        for item in items:
            Node(item, parent=builds)
        boots_node = self._create_subtitle_node("Boots", items_node)
        for boot in boots:
            Node(boot, parent=boots_node)

        # Runes
        runes_node = self._create_title_node("Runes", root)
        keystone_node = self._create_node(keystone, runes_node, primary_color)

        for i, rune in enumerate(runes):
            if i < 3: 
                self._create_node(rune, keystone_node, primary_color)
            else:
                self._create_node(rune, keystone_node, secondary_color)

        # for shard in shards:
        #     self._create_node(shard.title(), keystone_node, Fore.MAGENTA)

        init()
        for pre, _, node in RenderTree(root):
            print(f"{pre}{node.name}")
        deinit()
