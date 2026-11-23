#  Write programs using for/while loops to generate ranges, multiplication tables, even/odd sequences, and running totals. Add
# user-controlled start/end values rather than hard-coding 1–100.

def ranges(a,b):
    li=[]
    for i in range(a,b-1):
        # print(i+1, end = " ")
        li.append(i+1)

    return li


def multiplication(a,b):
    #a--> multiple
    #b--> range end 
    li=[]
    for i in range(b):
        # print(i)
        li.append(f"{a} * {i+1} = {a * (i+1)}")
    return li

def oddEven(a):
    for i in range(a):
        if (i+1)%2 == 0:
            print(i+1)
        else:
            print(i+1)

def fib(n):
    num=0
    for i in range(n+1):
        num+=i
        print(num, end=" ")

#range, multiply,oddeven, fib
# print(" 1. Nature of number \n 2. Odd or Even \n 3. Divisibility check \n 4. Range of numbers \n 5. Check Leap year \n 6. Voting Eligibility ")

n= int(input(" 1. Range of numbers \n 2. Multiply \n 3. Odd Evens \n 4. Running Totals: "))

match n:
    case 1:
        a=int(input("Enter the starting range: "))
        b=int(input("Enter the ending range: "))
        range=ranges(a,b)
        for i in range:
            print(i,end=" ")

    case 2:
        a=int(input("Enter the number to be multiplied: "))
        b=int(input("Enter the ending range: "))
        li = multiplication(a,b)
        for i in li:
            print(i)

    case 3:
        a=int(input("Enter the range: "))
        oddEven(a)          

    case 4:
        a=int(input("Enter the range: "))
        fib(a)

        



