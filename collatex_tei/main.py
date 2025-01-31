import os
import re
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, ConfigDict, RootModel


class Token(BaseModel):
    t: str
    n: str | None = None

    class Config:
        extra = "allow"


Cell = List[Token]

Column = List[Cell]

Table = List[Column]

Witnesses = List[str]


class CollateXOutput(BaseModel):
    witnesses: Witnesses
    table: Table


class WitnessSoup(BaseModel):
    siglum: str
    soup: BeautifulSoup

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProcessedColumn(RootModel):
    root: Dict[str, List[str]]


def get_token_reading(token: Token) -> str:
    if "n" in token:
        return token["n"]
    elif "t" in token:
        return token["t"]
    return ""


def get_tokens_string(tokens: List[Token]) -> str:
    strings = [get_token_reading(token) for token in tokens]
    return " ".join(strings)


def add_table_cell_tokens(
    soup: BeautifulSoup,
    parent: Tag,
    table_cell: Cell,
) -> None:
    for token in table_cell:
        word = soup.new_tag("word", **token)
        word.string = get_token_reading(token)
        parent.append(word)
    return None


def init_soup():
    soup = BeautifulSoup()
    body = soup.new_tag("body")
    soup.append(body)
    return soup


def process_collatex(
    data: CollateXOutput,
) -> Tuple[
    Table,
    Witnesses,
    List[ProcessedColumn],
    BeautifulSoup,
    List[WitnessSoup],
]:
    table: Table = data["table"]
    witnesses: Witnesses = data["witnesses"]

    main_soup: BeautifulSoup = init_soup()

    witness_soups: List[WitnessSoup] = []
    for witness in witnesses:
        soup = init_soup()
        witness_soups.append(WitnessSoup(siglum=witness, soup=soup))

    columns: List[ProcessedColumn] = []
    for set in table:
        readings = {}
        for w_index, witness in enumerate(set):
            sig = witnesses[w_index]
            rdg = get_tokens_string(witness)
            if rdg in readings:
                readings[rdg].append(sig)
            else:
                readings[rdg] = [sig]
        columns.append(readings)

    return table, witnesses, columns, main_soup, witness_soups


def collatex_to_tei(
    data: CollateXOutput, path_to_witnesses: str = "./"
) -> Tuple[BeautifulSoup, BeautifulSoup]:
    (
        table,
        witnesses,
        columns,
        main_soup,
        witness_soups,
    ) = process_collatex(data)

    rdg_num = 0
    for col_index, column in enumerate(columns):
        readings_count = len(column)
        if readings_count == 1:
            text = list(column.keys())[0] + " "
            main_soup.body.append(text)
            for wit in witness_soups:
                row_index = witnesses.index(wit.siglum)
                table_cell = table[col_index][row_index]
                wit_soup = wit.soup
                add_table_cell_tokens(
                    soup=wit_soup, parent=wit_soup.body, table_cell=table_cell
                )
        else:
            app = main_soup.new_tag("app")
            for text, wit in column.items():
                rdg_num += 1
                rdg_grp = main_soup.new_tag("rdgGrp")
                for w in wit:
                    row_index = witnesses.index(w)
                    table_cell = table[col_index][row_index]
                    xml_id = f"v_{rdg_num}"
                    rdg = main_soup.new_tag("rdg", **{"wit": w})
                    witness = next(i for i in witness_soups if i.siglum == w)
                    wit_soup = witness.soup
                    seg = wit_soup.new_tag("seg", **{"xml:id": xml_id})
                    add_table_cell_tokens(
                        soup=wit_soup, parent=seg, table_cell=table_cell
                    )
                    wit_soup.body.append(seg)
                    target = os.path.join(
                        path_to_witnesses,
                        f"{w}/view#{xml_id}",
                    )
                    ptr = main_soup.new_tag("ptr", **{"target": target})
                    rdg.append(ptr)
                    rdg_grp.append(rdg)
                app.append(rdg_grp)
            main_soup.body.append(app)

    omissions = main_soup.find_all("rdg", string=re.compile(r""))
    for elem in omissions:
        elem.replace_with(
            BeautifulSoup(str(elem).replace("></rdg>", "  />"), "lxml").rdg
        )

    ptrs = main_soup.find_all("ptr")
    for elem in ptrs:
        elem.replace_with(
            BeautifulSoup(str(elem).replace("></ptr>", "  />"), "lxml").ptr
        )

    return main_soup, witness_soups
