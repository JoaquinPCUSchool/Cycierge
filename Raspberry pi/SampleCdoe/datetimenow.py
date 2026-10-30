from datetime import datetime

# Get current local date and time
now = datetime.now()

# Print the default format (YYYY-MM-DD HH:MM:SS.microseconds)
print(now)

# Or format it specifically using strftime
print(now.strftime("%Y-%m-%d %H:%M:%S"))



# Get current local date and time
now = datetime.now()

# Print formatted time (HH:MM:SS)
print("Current Time =", now.strftime("%H:%M"))
timenowvar = str(now.strftime("%H:%M"))
print(timenowvar)
timenowvar = str(now.strftime("%Y-%M-%d"))
print(timenowvar)


# Print full datetime
print("Current DateTime =", now)
