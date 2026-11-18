
# Read SSH authentication logs
with open("sample_auth.log", "r") as file:
    for line in file:
        if "Failed password" in line:
            print(line.strip())
