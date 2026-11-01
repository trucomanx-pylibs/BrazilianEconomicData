
#!/usr/bin/python3

#pip install brazilian_economic_data
#or
import sys
sys.path.append("../src")


import json
import brazilian_economic_data.economic_indicators as ecin
import brazilian_economic_data.treasure_bonds as trbo

data=ecin.get_indicators()
#ecin.print_indicators(data)
print(json.dumps(data, indent=4, ensure_ascii=False))
print(ecin.indicators_to_string(data, 
                                show_cdi=True, 
                                show_selic=True, 
                                show_ipca_12m=True, 
                                show_focus=True,
                                show_errors=True,
                                show_consultation=True
                            ))


print("")


data=trbo.get_treasury_bonds(4, 8)
#trbo.print_treasury_bonds(data)
print(json.dumps(data, indent=4, ensure_ascii=False))
print(trbo.treasury_bonds_to_string(data,
                                    show_maturity=True,
                                    show_reference_date=False,
                                    show_buy_rate=True,
                                    show_sell_rate=False,
                                    show_buy_price=True,
                                    show_sell_price=False,
                                    show_base_price=False,
                                    show_consultation=False,
                                    show_quotation_period=False,
                                    show_source=False ))
