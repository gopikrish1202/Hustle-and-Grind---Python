def digit_count(num):
    count=0
    while(num>0):
        num=num//10
        count+=1
    # print(count)
    return count
# digit_count(12345)
def SumProduct(num):
    sum=0
    prod=1
    dict={}
    while(num>0):
        curr=num%10 
        sum+=curr
        prod*=curr
        num=num//10
    dict["Total"]=sum
    dict["Product"]=prod
    return dict 
# SumProduct(123456)

def reverse(num):
    rev=''

    while(num>0):
        curr=num%10
        # curr=str(curr)
        rev+=str(curr)
        num=num//10
    # print(rev)
    return rev

def palindrome(num):
    palin = reverse(num)
    if num == int(palin):
        # print("Works fine, palindrome")
        return True
    else:
        # print("Not a palindrome")
        return False
# palindrome(121)

def gcd(a,b):
    a_list=[]
    b_list=[]
    common = []
    for i in range(1,a+1):
        if a%i == 0:
            a_list.append(i)

    for j in range(1,b+1):
            if b%j == 0:
                b_list.append(j)

    for i in range(len(a_list)):  
        for j in range(len(b_list)):
            if a_list[i] == b_list[j]:
                common.append(a_list[i])

    print(max(common))
# gcd(20,28)














