import time 

start = time.time()
fruits = [['pomme', 5], ['banane', 3], ['orange', 10], ['kiwi', 4], ['fraise', 1]]

for fruit in fruits:
    time.sleep(fruit[1])

end = time.time()
print(f"Execution time: {end - start} seconds")
