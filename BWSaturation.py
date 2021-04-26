import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib.dates as mdates
import csv
import datetime
xlabel="Time"
ylabel="Bandwidth Saturation"
title='{} vs {}'.format(xlabel,ylabel)
infile="graph_data.csv"
xcol="Time"
ycol="Bandwidth_Saturation"
fig, ax1 = plt.subplots()
plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.title(title)
def animate(i):
    try:
        with open(infile) as csvfile:
            reader = csv.DictReader(csvfile)
            xs=[]
            ys=[]
            for row in reader:
                x = datetime.datetime.strptime( row[xcol],"%Y-%m-%d %H:%M:%S")	   
                y = row[ycol]
                xs.append(x)
                ys.append(y)			
            ax1.clear()
            plt.gcf().autofmt_xdate()
            ax1.plot(xs, ys)
            xfmt = mdates.DateFormatter('%H:%M:%S')
            ax1.xaxis.set_major_formatter(xfmt)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=45)
            plt.title(title)
    except OSError as e:
            print(e.errno)
ani = anim.FuncAnimation(fig, animate, interval=5000)
plt.show()
