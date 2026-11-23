
# 1. Take input and set up foundations
try:
    units_consumed = float(input("Enter units consumed: "))

except ValueError:
    print("Invalid input! Please enter numbers only.")
    exit()

#Gowtham's code
remaining_units = units_consumed
final_amt = 0
units_consumed=int(units_consumed)
if units_consumed>0:
    if remaining_units > 0: #first 200
        slab1_units = min(remaining_units, 200) #401, 200 - compare
        print("slab units slab1", slab1_units)
        final_amt += slab1_units * 0.00
        print("final_amt_slab1",final_amt)
        remaining_units -= slab1_units  # 401-200=201
        print("remaining_units slab1",remaining_units)

    # 3. Process Slab 2: Next 200 units, i.e., 201 to 400 (Rate = ₹4.71)
    if remaining_units > 0: #second 200 (or) 200-400
        # Take either all remaining units OR max 200 units for this slab
        slab2_units = min(remaining_units, 200)  #201, 200
        print("slab units slab2", slab2_units)
        final_amt += slab2_units * 4.71
        print("final_amt_slab2",final_amt)
        remaining_units -= slab2_units  # 200-200=0
        print("remaining_units slab2",remaining_units)
        #break

    # 4. Process Slab 3: Anything left above 400 units (Rate = ₹6.30)
    if remaining_units > 0: #1>0 false
        final_amt += remaining_units * 6.30
        print("final_amt_slab3",final_amt)
    
    final_amt += 30 #base price
    print("Progressive EB Bill Amount: ₹", final_amt)

else:
    print("please enter valid postive units")



