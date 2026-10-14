def digit_count(num):
    count = 0
    while num > 0:
        num = num // 10
        count += 1
    # print(count)
    return count


# digit_count(12345)
def SumProduct(num):
    sum = 0
    prod = 1
    dict = {}
    while num > 0:
        curr = num % 10
        sum += curr
        prod *= curr
        num = num // 10
    dict["Total"] = sum
    dict["Product"] = prod
    return dict


# SumProduct(123456)


def reverse(num):
    rev = ""

    while num > 0:
        curr = num % 10
        # curr=str(curr)
        rev += str(curr)
        num = num // 10
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
# test commit
def gcd(a, b):

    a_list = []
    b_list = []
    common = []
    for i in range(1, a + 1):
        if a % i == 0:
            a_list.append(i)

    for j in range(1, b + 1):
        if b % j == 0:
            b_list.append(j)

    for i in range(len(a_list)):
        for j in range(len(b_list)):
            if a_list[i] == b_list[j]:
                common.append(a_list[i])

    print(max(common))


def calculate_lcm(a, b):  # 5,6
    candidate = max(a, b)  # 6
    print("picking max num", candidate)

    while True:
        if candidate % a == 0 and candidate % b == 0:  # 6%5
            print("match found", candidate)
            return candidate
        print("incrementing candidate", candidate)
        candidate += max(a, b)
        print("after increment", candidate)


# calculate_lcm(10,8)


def prime_num(num):
    if num < 2:
        return False
    # by default every number is divisible by 1
    for i in range(2, num):
        if num % i == 0:

            return f"It is not a prime, {num}"

    return f"It is a prime number, {num}"


# print(prime_num(8))


def armstrong_num(num):
    local_num = num
    num_length = digit_count(num)
    sum = 0
    for i in range(num_length):
        curr_num = num % 10
        sum += curr_num**num_length
        num = num // 10

    print("sum", sum)
    if sum == local_num:
        print("armstrong number")
    else:
        print("not an armstrong")


# armstrong_num(1634)


def perfect_num(num):
    num_list = []
    sum = 0
    for i in range(1, num):
        if num % i == 0:
            num_list.append(i)
    for j in num_list:
        sum += j
    print("num_list", num_list)
    print("sum", sum)
    print("num", num)
    if sum == num:
        return f"{num}, is a perfect number"
    else:
        return f"{num}, is a not perfect number"


# print(perfect_num(6))



def factorial(num):
    fact=1
    for i in range(fact, num+1):
        fact*=i
    return fact

def strong_num(num):
    local_num=num
    final_factorial_sum=0
    num_length=digit_count(num)

    for i in range(num_length):
        curr_num=num%10
        curr_fact=factorial(curr_num)
        final_factorial_sum+=curr_fact
        num=num//10
        
    if(final_factorial_sum==local_num):
        return f"{local_num} is a strong number"
    else:
        return f"{local_num} is a not a strong number"

    
print(strong_num(40585))