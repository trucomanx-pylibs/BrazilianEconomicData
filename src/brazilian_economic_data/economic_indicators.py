
#!/usr/bin/env python3

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd


# =====================================================
# CONFIGURATION
# =====================================================

BCB_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

FOCUS = (
    "https://olinda.bcb.gov.br/olinda/servico/"
    "Expectativas/versao/v1/odata/"
)

CURRENT_YEAR = datetime.now().year


# =====================================================
# INTERNAL FUNCTIONS
# =====================================================

def _request_json(url):

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Python Economic Indicators/1.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_date(date):

    if not date:
        return None

    try:
        return datetime.strptime(
            date, "%d/%m/%Y"
        ).strftime("%Y-%m-%d")

    except ValueError:
        pass

    try:
        return datetime.strptime(
            date, "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

    except ValueError:
        raise ValueError(f"Invalid date format: {date}")


def _get_sgs_series(series_code):

    url = (
        f"{BCB_SGS}.{series_code}"
        "/dados/ultimos/1?formato=json"
    )

    data = _request_json(url)

    if not data:
        raise ValueError(
            f"BCB returned no data for series {series_code}"
        )

    return data[-1]


def _get_ipca_expectation(year):

    endpoint = FOCUS + "ExpectativasMercadoAnuais"

    initial_date = (
        datetime.now() - timedelta(days=30)
    ).strftime("%Y-%m-%d")

    parameters = {
        "$filter": (
            "Indicador eq 'IPCA' "
            f"and Data ge '{initial_date}'"
        ),
        "$top": "1000",
        "$format": "json"
    }

    url = endpoint + "?" + urllib.parse.urlencode(
        parameters,
        quote_via=urllib.parse.quote
    )

    data = _request_json(url)

    records = [
        record for record in data.get("value", [])
        if record.get("baseCalculo") == 0
        and str(record.get("DataReferencia")) == str(year)
    ]

    if not records:
        return None

    records.sort(
        key=lambda record: record["Data"],
        reverse=True
    )

    return records[0]


# =====================================================
# PUBLIC FUNCTION 1
# GET INDICATORS
# =====================================================

def get_indicators():

    result = {
        "consultation": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "cdi": None,
        "selic": None,
        "ipca_12m": None,
        "focus": [],
        "errors": []
    }

    # CDI
    try:
        cdi = _get_sgs_series(4389)

        result["cdi"] = {
            "value": float(cdi["valor"]),
            "date": _normalize_date(cdi["data"])
        }

    except Exception as error:
        result["errors"].append(f"CDI: {error}")

    # Selic Meta
    try:
        selic = _get_sgs_series(432)

        result["selic"] = {
            "value": float(selic["valor"]),
            "date": _normalize_date(selic["data"])
        }

    except Exception as error:
        result["errors"].append(f"Selic: {error}")

    # IPCA accumulated over 12 months
    try:
        ipca = _get_sgs_series(13522)

        result["ipca_12m"] = {
            "value": float(ipca["valor"]),
            "date": _normalize_date(ipca["data"])
        }

    except Exception as error:
        result["errors"].append(f"IPCA: {error}")

    # Focus expectations
    for year in [CURRENT_YEAR, CURRENT_YEAR + 1]:

        try:
            expectation = _get_ipca_expectation(year)

            if expectation:
                result["focus"].append({
                    "year": year,
                    "value": float(expectation["Mediana"]),
                    "date": _normalize_date(
                        expectation["Data"]
                    )
                })

        except Exception as error:
            result["errors"].append(
                f"Focus {year}: {error}"
            )

    return result


# =====================================================
# PUBLIC FUNCTION 2
# PRINT INDICATORS
# =====================================================

def indicators_to_string(
    data,
    show_cdi=True,
    show_selic=True,
    show_ipca_12m=True,
    show_focus=True,
    show_errors=True,
    show_consultation=True
):

    rows = []

    if show_cdi and data.get("cdi"):
        rows.append({
            "Indicator": "CDI",
            "Reference": "Annualized",
            "Value": data["cdi"]["value"],
            "Date": data["cdi"]["date"]
        })

    if show_selic and data.get("selic"):
        rows.append({
            "Indicator": "Selic",
            "Reference": "Target rate",
            "Value": data["selic"]["value"],
            "Date": data["selic"]["date"]
        })

    if show_ipca_12m and data.get("ipca_12m"):
        rows.append({
            "Indicator": "IPCA",
            "Reference": "12 months",
            "Value": data["ipca_12m"]["value"],
            "Date": data["ipca_12m"]["date"]
        })

    if show_focus:
        for item in data.get("focus", []):
            rows.append({
                "Indicator": "Focus IPCA",
                "Reference": str(item["year"]),
                "Value": item["value"],
                "Date": item["date"]
            })

    df = pd.DataFrame(rows)

    output = []

    if not df.empty:

        df["Value"] = df["Value"].map(
            lambda value: f"{value:.2f}%".replace(".", ",")
        )

        df["Date"] = pd.to_datetime(
            df["Date"],
            format="%Y-%m-%d",
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

        table = df.to_string(index=False, header=True)

        header, body = table.split("\n", 1)

        separator = "-" * len(header)

        output.append(
            header + "\n" +
            separator + "\n" +
            body
        )


    else:
        output.append("No indicators available.")

    if show_errors and data.get("errors"):
        output.append("\nCOLLECTION ERRORS:")

        for error in data["errors"]:
            output.append(f"- {error}")

    if show_consultation:
        output.append(
            f"\nConsultation: {data['consultation']}"
        )

    return "\n".join(output)
    
def print_indicators(data, **kwargs):
    print(indicators_to_string(data, **kwargs))


# =====================================================
# TEST
# =====================================================

def main():
    indicators = get_indicators()

    #with open("indicators.json", "w", encoding="utf-8") as file:
    #    json.dump(indicators, file, ensure_ascii=False, indent=4 )

    #print("ECONOMIC INDICATORS")
    #print("=" * 40)
    
    print_indicators(indicators)

    #print("JSON updated: indicators.json")


if __name__ == "__main__":
    main()
