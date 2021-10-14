import json, csv, datetime, pytz, math
import pandas as pd, numpy as np
from pprint import pprint


# initialize collateralized positions every day at open
def create_position(inputs, date, btcusd, ethusd):
	eth_required = btcusd * inputs["init c-ratio"] / ethusd
	position = {
		"timestamp": [date],
		"eth posted": [eth_required],
		"underlying value": [btcusd], # 1 btc positions
		"collateral value": [eth_required * ethusd],
		"c-ratio": [inputs["init c-ratio"]]
	}
	return position

# update position with new items in array and recalculate c-ratio
def update_position(position, date, btcusd, ethusd):
	eth_required = position["eth posted"][0]
	position["timestamp"].append(date)
	position["eth posted"].append(eth_required) # no change
	position["underlying value"].append(btcusd)
	position["collateral value"].append(eth_required * ethusd)
	position["c-ratio"].append(eth_required * ethusd / btcusd)
	return position

# iterate through date range, each day (1) create a new position, (2) update existing positions
def run_test(inputs, ohlc):
	test = {}
	benchmarks = {"init c-ratio":[],"courtesy call":[],"liquidation":[]}
	for t in inputs["date_rng"]:
		for key in benchmarks.keys():
			benchmarks[key].append(inputs[key])
		btcusd = ohlc["btcusd"]["open"].at[t]
		ethusd = ohlc["ethusd"]["open"].at[t]
		# i want to use this, but haven't figured out how yet
		ethbtc = ohlc["ethbtc"]["open"].at[t]
		# update all positions
		for key in test.keys():
			test[key] = update_position(test[key], str(t)[:10], btcusd, ethusd)
		# create a new position (stringize to dump datetime to a json, 10 to truncate time)
		test[str(t)[:10]] = create_position(inputs, str(t)[:10], btcusd, ethusd)
	with open("data/test.json", "w") as jf:
		json.dump(test, jf)
	return benchmarks

# function for reading/loading test data
def load_test():
	with open("data/test.json", "r") as jf:
		test = json.load(jf)
	return test

# iterate through the testing dictionary to count % liquidated, and % courtesy calls
def summary(inputs, test):
	summary = {"Date Position Opened":[],"Total Days":[],"Days Below Courtesy Call":[],"Liquidated?":[]}
	for t in test.keys():
		# init conditions
		tot_days = 0
		days_below_cc = 0
		liq_bool = False
		# test conditions
		for x in test[t]["c-ratio"]:
			tot_days += 1
			if x < inputs["courtesy call"]:
				days_below_cc += 1
				if x < inputs["liquidation"]:
					liq_bool = True
		# add data to list
		summary["Date Position Opened"].append(t)
		summary["Total Days"].append(tot_days)
		summary["Days Below Courtesy Call"].append(days_below_cc)
		summary["Liquidated?"].append(liq_bool)
	return summary



if __name__ == "__main__":
	# import csv price data
	ohlc = {
		"btcusd": pd.read_csv(r"data/BTCUSD.csv"),
		"ethusd": pd.read_csv(r"data/ETHUSD.csv"),
		"ethbtc": pd.read_csv(r"data/ETHBTC.csv")
	}

	# reformat datetime and set as index
	for key in ohlc.keys():
		ohlc[key]["timestamp"] = ohlc[key]["timestamp"].astype("datetime64[ns, UTC]")
		ohlc[key].set_index("timestamp", inplace = True)

	# init parameters for analysis
	inputs = {
		"init c-ratio": 1.5,
		"courtesy call": 1.25,
		"liquidation": 1.1,
		"start date": datetime.datetime(2021,1,1).replace(tzinfo=pytz.utc),
		"end date": ohlc["btcusd"].index.max()
	}

	inputs["date_rng"] = pd.date_range(inputs["start date"], inputs["end date"])
	run_test(inputs, ohlc)