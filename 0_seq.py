import time 

start = time.time()
list = [['pomme',5],['banane',3],['orange',10],['kiwi',4],['fraise',1]]

for fruit in list:
    time.sleep(5)  

end = time.time()
print(f"Execution time: {end - start} seconds")