
import json
from io import BytesIO
from datetime import date, datetime

import pandas as pd
import requests


CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/"
    "precotaxatesourodireto.csv"
)


def _add_years(reference_date, years):
    try:
        return reference_date.replace(year=reference_date.year + years)
    except ValueError:
        return reference_date.replace(
            year=reference_date.year + years,
            month=2,
            day=28
        )


def get_treasury_bonds(min_years, max_years):
    if not isinstance(min_years, int) or not isinstance(max_years, int):
        raise ValueError("Years must be integers.")

    if min_years < 0 or max_years < min_years:
        raise ValueError("Invalid maturity range.")

    today = date.today()
    min_date = _add_years(today, min_years)
    max_date = _add_years(today, max_years)

    response = requests.get(CSV_URL, timeout=60)
    response.raise_for_status()

    df = pd.read_csv(
        BytesIO(response.content),
        sep=";",
        decimal=",",
        encoding="latin1"
    )

    df.columns = df.columns.str.strip()

    required_columns = [
        "Tipo Titulo",
        "Data Vencimento",
        "Data Base",
        "Taxa Compra Manha",
        "Taxa Venda Manha",
        "PU Compra Manha",
        "PU Venda Manha",
        "PU Base Manha"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing CSV columns: {missing_columns}"
        )

    df["Data Base"] = pd.to_datetime(
        df["Data Base"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    df["Data Vencimento"] = pd.to_datetime(
        df["Data Vencimento"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    numeric_columns = [
        "Taxa Compra Manha",
        "Taxa Venda Manha",
        "PU Compra Manha",
        "PU Venda Manha",
        "PU Base Manha"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "Tipo Titulo",
            "Data Base",
            "Data Vencimento",
            "Taxa Compra Manha"
        ]
    )

    # Keep the latest quotation for each title and maturity.
    df = df.sort_values("Data Base")

    df = df.drop_duplicates(
        subset=["Tipo Titulo", "Data Vencimento"],
        keep="last"
    )

    # Filter titles by maturity range.
    df = df[
        (df["Data Vencimento"].dt.date >= min_date)
        & (df["Data Vencimento"].dt.date <= max_date)
    ].copy()

    # Keep the highest buy rate for each complete title type.
    best_indices = df.groupby(
        "Tipo Titulo"
    )["Taxa Compra Manha"].idxmax()

    best_bonds = df.loc[best_indices]

    bonds = []

    for _, bond in best_bonds.iterrows():
        bonds.append({
            "name": bond["Tipo Titulo"],
            "maturity": bond["Data Vencimento"].date().isoformat(),
            "reference_date": bond["Data Base"].date().isoformat(),
            "buy_rate": float(bond["Taxa Compra Manha"]),
            "sell_rate": (
                float(bond["Taxa Venda Manha"])
                if pd.notna(bond["Taxa Venda Manha"])
                else None
            ),
            "buy_price": (
                float(bond["PU Compra Manha"])
                if pd.notna(bond["PU Compra Manha"])
                else None
            ),
            "sell_price": (
                float(bond["PU Venda Manha"])
                if pd.notna(bond["PU Venda Manha"])
                else None
            ),
            "base_price": (
                float(bond["PU Base Manha"])
                if pd.notna(bond["PU Base Manha"])
                else None
            )
        })

    result = {
        "consultation": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "source": CSV_URL,
        "quotation_period": "Morning",
        "maturity_range": {
            "min_years": min_years,
            "max_years": max_years,
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat()
        },
        "bonds": sorted(
            bonds,
            key=lambda bond: bond["buy_rate"],
            reverse=True
        )
    }

    return result


def print_treasury_bonds(data):
    bonds = data.get("bonds", [])

    if not bonds:
        print("No Treasury bonds found for the selected maturity range.")
        return

    df = pd.DataFrame(bonds)

    df = df.rename(columns={
        "name": "Title",
        "maturity": "Maturity",
        "reference_date": "Reference Date",
        "buy_rate": "Buy Rate (%)",
        "sell_rate": "Sell Rate (%)",
        "buy_price": "Buy Price (R$)",
        "sell_price": "Sell Price (R$)",
        "base_price": "Base Price (R$)"
    })

    print("\nTREASURY BONDS")
    print("=" * 100)

    print(
        df.to_string(
            index=False,
            formatters={
                "Buy Rate (%)": lambda value: f"{value:.2f}%",
                "Sell Rate (%)": lambda value: (
                    f"{value:.2f}%" if pd.notna(value) else "-"
                ),
                "Buy Price (R$)": lambda value: (
                    f"R$ {value:,.2f}" if pd.notna(value) else "-"
                ),
                "Sell Price (R$)": lambda value: (
                    f"R$ {value:,.2f}" if pd.notna(value) else "-"
                ),
                "Base Price (R$)": lambda value: (
                    f"R$ {value:,.2f}" if pd.notna(value) else "-"
                )
            }
        )
    )

    print("\nConsultation:", data["consultation"])
    print("Quotation period:", data["quotation_period"])
    print("Source: Tesouro Transparente")


def main():
    bonds = get_treasury_bonds(4, 8)

    print_treasury_bonds(bonds)

    with open(
        "treasury_bonds.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            bonds,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nJSON updated: treasury_bonds.json")


if __name__ == "__main__":
    main()
