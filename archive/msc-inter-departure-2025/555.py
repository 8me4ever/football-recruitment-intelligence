def seperate(s):
    result={}
    items=s.split(",")
    for item in items:
        key,value=item.split(":")
        result[key]=int(value)
    return result

s = "A1:1,b2:13,x5:651,D61:47"
ans=seperate(s)
print(ans)
