import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib.dates as mdates
import csv
import datetime

xlabel="Time"
title='Time vs Throughput and input load'
infile="traffic_data.csv"
xcol="Time"
y1col="Input_load"
y2col="Throughput"
fig, ax1 = plt.subplots()
plt.xlabel(xlabel)
plt.title(title)
def animate(i):
    try:
        with open(infile) as csvfile:
            reader = csv.DictReader(csvfile)
            xs=[]
            y1s=[]
            y2s=[]
            for row in reader:
                x = datetime.datetime.strptime( row[xcol],"%Y-%m-%d %H:%M:%S")	   
                y1 = row[y1col]
                y2 = row[y2col]
                xs.append(x)
                y1s.append(y1)			
                y2s.append(y2)			
            ax1.clear()
            plt.gcf().autofmt_xdate()
            xfmt = mdates.DateFormatter('%H:%M:%S')
            ax1.xaxis.set_major_formatter(xfmt)
            plt.xlabel(xlabel)
            plt.plot(xs,y1s,label=y1col)
            plt.plot(xs,y2s,label=y2col)
            plt.xticks(rotation=45)
            plt.title(title)
            plt.legend( loc='upper center', shadow=True)

    except OSError as e:
            print(e.errno)
ani = anim.FuncAnimation(fig, animate, interval=5000)
plt.show()
