
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


data=trbo.get_treasury_bonds(4, 8)
#trbo.print_treasury_bonds(data)
print(json.dumps(data, indent=4, ensure_ascii=False))
