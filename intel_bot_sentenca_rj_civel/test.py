with open('./logs/test.log', 'r') as f1:
    data = f1.readlines()

formatted = [x.replace('.pdf', '') for x in data]

with open('./logs/test2.log', 'r') as f1:
    f1.writelines(formatted)

