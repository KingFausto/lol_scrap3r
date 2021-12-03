import requests
import re
import os
from bs4 import BeautifulSoup
from anytree import Node, RenderTree
from colorama import init, deinit, Fore, Back, Style

ROLES = {
    "-t": "Top",
    "-j": "Jungle",
    "-m": "Mid",
    "-b": "Bottom",
    "-s": "Support",
}

COLORS = {
    "Precision": Fore.YELLOW,
    "Domination": Fore.RED,
    "Sorcery": Fore.BLUE,
    "Resolve": Fore.GREEN,
    "Inspiration": Fore.CYAN,
}

MYTHIC_ITEMS = [
    "Divine Sunderer",
    "Duskblade of Draktharr",
    "Eclipse",
    "Everfrost",
    "Frostfire Gauntlet",
    "Galeforce",
    "Goredrinker",
    "Hextech Rocketbelt",
    "Immortal Shieldbow",
    "Imperial Mandate",
    "Kraken Slayer",
    "Liandry's Anguish",
    "Locket of the Iron Solari",
    "Luden's Tempest",
    "Moonstone Renewer",
    "Night Harvester",
    "Prowler's Claw",
    "Riftmaker",
    "Shurelya's Battlesong",
    "Stridebreaker",
    "Sunfire Aegis",
    "Trinity Force",
    "Turbo Chemtank",
    "Evenshroud",
    "Crown of the Shattered Queen",
]

# helper function to clean up information from certain queries
def parse_results(results, regex=r"&gt;(.*?)&"):
    return [re.search(regex, str(i)).group(1) for i in results]


# get input on champion, role, and gamemode
cmd = input(">> ").split()

role = None
mode = "champion"

if len(cmd) == 1:
    champion = cmd[0]
elif "-" in cmd[1]:
    champion, role = cmd
else:
    champion, mode = cmd

# set the url and add a role if applicable
url = f"https://www.op.gg/{mode}/{champion}/statistics/"
if role:
    role = ROLES[role]
    url += role

# get the main table with all the information
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
main_table = soup.find_all("td", class_="champion-overview__data")

# get the current patch and real role
current_patch = soup.find("div", class_="champion-stats-header-version").text.split()[
    -1
]

if not role:
    role = soup.find("h1", class_="champion-stats-header-info__name").text.split()[-1]
    if role == "Middle":
        role = "Mid"


# --------------------- GET SUMMONERS -----------------------------------------
summoner_pick_rates = soup.find_all(
    "td", class_="champion-overview__stats champion-overview__stats--pick"
)

summoners = []

for i in range(0, 2):
    summoners.append(
        parse_results(main_table[i].find_all("li", class_="champion-stats__list__item"))
        + summoner_pick_rates[i].text.strip().split("\n")[:-1]
    )
    summoners[
        i
    ] = f"{' + '.join(summoners[i][:2])} {Style.BRIGHT + Fore.BLACK}({summoners[i][2]} PR){Style.RESET_ALL}"

# --------------------- GET SKILL ORDER ---------------------------------------
skill_order = main_table[2].find("table", class_="champion-skill-build__table").text

skills = skill_order.replace("\t", "").replace("\n", "")[-15:]

# --------------------- GET ITEMS ---------------------------------------------
pick_rate = soup.find_all(
    "td",
    class_="champion-overview__stats champion-overview__stats--pick champion-overview__border",
)

items = []
for i in range(3, 13):
    items.append(
        parse_results(
            main_table[i].find_all("li", class_="champion-stats__list__item tip")
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

# --------------------- GET RUNES ---------------------------------------------
keystone = parse_results(
    main_table[13].find_all(
        "div",
        class_="perk-page__item perk-page__item--keystone perk-page__item--active",
    )
)[0]

runes = parse_results(
    main_table[13].find_all("div", class_="perk-page__item perk-page__item--active")
)

shards = parse_results(
    main_table[13].find_all("img", class_="active tip"), r"span&gt;(.*?)&"
)

rune_trees = soup.find("div", class_="champion-stats-summary-rune__name").text.split(
    " + "
)

primary_color = COLORS[rune_trees[0]]
secondary_color = COLORS[rune_trees[1]]

# --------------------- BUILD THE TREE ----------------------------------------
root_title = f"{champion.title()} {role if mode == 'champion' else mode.title()} Builds for Patch {current_patch}"
root = Node(Style.BRIGHT + Fore.GREEN + root_title + Style.RESET_ALL)

summoners_node = Node(
    Style.BRIGHT + Fore.BLUE + "Summoner Spells" + Style.RESET_ALL, parent=root
)
for i in range(0, 2):
    Node(summoners[i], parent=summoners_node)

skills_node = Node(
    Style.BRIGHT + Fore.BLUE + "Skill Order" + Style.RESET_ALL, parent=root
)
Node(skills, parent=skills_node)

items_node = Node(
    Style.BRIGHT + Fore.BLUE + "Item Builds" + Style.RESET_ALL, parent=root
)

starters = Node(
    Style.BRIGHT + Fore.RED + "Starter Items" + Style.RESET_ALL, parent=items_node
)
for i in range(0, 2):
    Node(items[i], parent=starters)

builds = Node(
    Style.BRIGHT + Fore.RED + "Recommended Builds" + Style.RESET_ALL, parent=items_node
)
for i in range(2, 7):
    Node(items[i], parent=builds)

boots = Node(Style.BRIGHT + Fore.RED + "Boots" + Style.RESET_ALL, parent=items_node)
for i in range(7, 10):
    Node(items[i], parent=boots)

runes_node = Node(Style.BRIGHT + Fore.BLUE + "Runes" + Style.RESET_ALL, parent=root)

keystone_node = Node(primary_color + keystone + Fore.RESET, parent=runes_node)

for i in range(len(runes)):
    if i < 3:
        Node(primary_color + runes[i] + Fore.RESET, parent=keystone_node)
    else:
        Node(secondary_color + runes[i] + Fore.RESET, parent=keystone_node)

for i in range(len(shards)):
    Node(Style.BRIGHT + Fore.YELLOW + shards[i] + Style.RESET_ALL, parent=keystone_node)

# display the tree
init()
for pre, fill, node in RenderTree(root):
    print(f"{pre} {node.name}")
deinit()
