def some_list_gen(stop=False):
    if not stop:
        return [1,2,3,4]


count = 0
stop = False
while a_list := some_list_gen(stop):
    print("iteration: " + str(count))
    print(a_list)
    count += 1
    if count >= 3:
        stop = True
