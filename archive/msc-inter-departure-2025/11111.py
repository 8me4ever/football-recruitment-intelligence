def num_Square(n):
    dp=[float('inf')]*100000
    dp[0]=0
    for i in range(1,n+1):
        j=1
        while j*j<=i:
            dp[i]=min(dp[i],dp[i-j*j]+1)
            j+=1
    return dp[n]

print(num_Square(13))