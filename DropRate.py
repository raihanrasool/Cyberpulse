import matplotlib.pyplot as plt
import matplotlib.animation as anim
import csv
import matplotlib.dates as mdates
import datetime
xlabel="Time"
ylabel="Packet Drop Rate"
title='{} vs {}'.format(xlabel,ylabel)
infile="graph_data.csv"
xcol="Time"
ycol="Packet_Drop_Rate"
fig, ax1 = plt.subplots()
plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.title(title)
def animate(i):
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
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
ani = anim.FuncAnimation(fig, animate, interval=5000)
plt.show()
