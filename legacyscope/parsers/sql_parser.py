from __future__ import annotations

import re
from pathlib import Path

from ..models import ColumnInfo, TableInfo


def split_top_level(value: str, separator: str = ",") -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    for char in value:
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
            current.append(char)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == separator and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [part for part in parts if part]


def clean_identifier(name: str) -> str:
    return name.strip().strip("`\"[]")


def parse_sql_text(text: str, source: str) -> list[TableInfo]:
    tables: list[TableInfo] = []
    table_re = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"\[\]\w.]+)\s*\(",
        flags=re.IGNORECASE,
    )
    for match in table_re.finditer(text):
        table_name = clean_identifier(match.group(1)).split(".")[-1]
        start = match.end()
        depth = 1
        quote = ""
        end = start
        for index in range(start, len(text)):
            char = text[index]
            if quote:
                if char == quote:
                    quote = ""
                continue
            if char in {"'", '"', "`"}:
                quote = char
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        body = text[start:end]
        columns: list[ColumnInfo] = []
        primary_keys: list[str] = []
        foreign_keys: list[str] = []
        for item in split_top_level(body):
            normalized = re.sub(r"\s+", " ", item.strip())
            upper = normalized.upper()
            if not normalized:
                continue
            if upper.startswith(("PRIMARY KEY", "UNIQUE", "KEY ", "INDEX ", "CONSTRAINT", "FOREIGN KEY", "CHECK ")):
                pk_match = re.search(r"PRIMARY\s+KEY\s*\(([^)]+)\)", normalized, flags=re.IGNORECASE)
                if pk_match:
                    primary_keys.extend(clean_identifier(x) for x in pk_match.group(1).split(","))
                fk_match = re.search(
                    r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([`\"\[\]\w.]+)\s*\(([^)]+)\)",
                    normalized,
                    flags=re.IGNORECASE,
                )
                if fk_match:
                    child = clean_identifier(fk_match.group(1).split(",")[0])
                    parent_table = clean_identifier(fk_match.group(2)).split(".")[-1]
                    parent_column = clean_identifier(fk_match.group(3).split(",")[0])
                    foreign_keys.append(f"{child}->{parent_table}.{parent_column}")
                    for column in columns:
                        if column.name == child:
                            column.is_foreign = True
                            column.references = f"{parent_table}.{parent_column}"
                continue
            column_match = re.match(r"([`\"\[\]\w]+)\s+([A-Za-z]+(?:\s*\([^)]*\))?)", normalized)
            if not column_match:
                continue
            name = clean_identifier(column_match.group(1))
            col_type = column_match.group(2).strip()
            is_pk = "PRIMARY KEY" in upper
            is_fk = "REFERENCES" in upper
            references = ""
            if is_fk:
                ref_match = re.search(r"REFERENCES\s+([`\"\[\]\w.]+)\s*\(([^)]+)\)", normalized, flags=re.IGNORECASE)
                if ref_match:
                    references = f"{clean_identifier(ref_match.group(1)).split('.')[-1]}.{clean_identifier(ref_match.group(2).split(',')[0])}"
            nullable = "NOT NULL" not in upper and "PRIMARY KEY" not in upper
            columns.append(ColumnInfo(
                name=name,
                type=col_type,
                is_primary=is_pk,
                is_foreign=is_fk,
                nullable=nullable,
                references=references,
            ))
            if is_pk:
                primary_keys.append(name)
        for column in columns:
            if column.name in primary_keys:
                column.is_primary = True
        for column in columns:
            if column.references:
                foreign_keys.append(f"{column.name}->{column.references}")
        tables.append(TableInfo(
            name=table_name,
            columns=columns,
            source=source,
            primary_key=", ".join(dict.fromkeys(primary_keys)),
            foreign_keys=list(dict.fromkeys(foreign_keys)),
        ))
    return tables


def parse_sql_file(path: Path, rel_path: str) -> list[TableInfo]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return parse_sql_text(text, rel_path)


def find_sql_tables(text: str) -> list[str]:
    patterns = [
        r"\bFROM\s+([`\"\[\]\w.]+)",
        r"\bJOIN\s+([`\"\[\]\w.]+)",
        r"\bINSERT\s+INTO\s+([`\"\[\]\w.]+)",
        r"\bUPDATE\s+([`\"\[\]\w.]+)",
        r"\bDELETE\s+FROM\s+([`\"\[\]\w.]+)",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            name = clean_identifier(match.group(1)).split(".")[-1]
            if name.upper() not in {"SELECT", "WHERE", "SET", "VALUES"} and name not in found:
                found.append(name)
    return found
