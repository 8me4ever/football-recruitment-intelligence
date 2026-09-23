def month_diff(date1,date2):
    year1 = int(date1[:4])
    year2 = int(date2[:4])
    mon1 = int(date1[4:])
    mon2 = int(date2[4:])
    if year1 >= year2:
        if mon1 >= mon2:
            return (year1 - year2) * 12 + mon2 - mon1
        if mon1 < mon2:
            return (year1 - year2) * 12 + mon1 - mon2
    if year1 < year2:
        return (year1 - year2) * 12 - mon2 + mon1

print(month_diff('202001','201804'))
print(month_diff('202001','202003'))