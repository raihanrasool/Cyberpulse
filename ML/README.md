# Network Traffic Classification
# Supervised Learning
## Project: Finding Donors for CharityML

### Install

This project requires **Python 3.6** and the following Python libraries installed:

- [NumPy](http://www.numpy.org/)
- [Pandas](http://pandas.pydata.org)
- [matplotlib](http://matplotlib.org/)
- [scikit-learn](http://scikit-learn.org/stable/)

You will also need to have software installed to run and execute an [iPython Notebook](http://ipython.org/notebook.html)

I recommend to install [Anaconda](https://www.continuum.io/downloads), a pre-packaged Python distribution that contains all of the necessary libraries and software for this project. 


### Run

You can run the source code using either a terminal or Jupyter Notebook. 

Option 1 - Terminal: Navigate to the directory of the .ipynb file and type the following command.

```bash
jupyter notebook finding_donors.ipynb
```
This will open the iPython Notebook software and project file in your browser.

Option 2 - Jupyter Notebook from Anaconda Distribution. Open Jupyter Notebook and press the upload button in the top right corner. Navigate to the directory that the file is located and upload it. Finally, hit right click on the file.

Both options include running each bolck of code individually after the file is opened. You can run every file by clicking each block of code and press run button from the menu. That way you can observe each step of the process.



### Data

The Burst Header Packet (BHP) flooding attack on Optical Burst Switching (OBS) Network Data Set dataset consists of approximately 1075 data points, with each datapoint having 22 features. 

**Features**
1. Node (numeric)
2. utilized bandwidth (numeric)
3.  packet drop rate (numeric)
3. full bandwidth (numeric)
4. percentage of packet lost rate (numeric)
5. percentage of lost byte rate (numeric)
6. packets received rate (numeric)
7. used bandwidth (numeric)
8. lost bandwidth (numeric)
9. packet size (numeric)
10.packets received (numeric)
11. packets lost (numeric)
12. transmitted byte (numeric)
13. flooding status (numeric)

 
 
**Target Variable**
Class ' {Flooding, Legitimate}: The final classification of nodes (Categorical ). 


### Reults
After training is finished. There will be 10 pickle and 10 JSON files that hold the best performing model. In case you want to use that model, call the 'load_model' function with the path string as a paramater.

### Results explanation

#### The results the following structure:

f_beta score: Score based on recall, precision rates
accuracy_score: Accuracy score

After transforming the problem into binary, during class distrbution plot I observed that the classes are imbalanced. More specificaly, alsmost 88% is consisted of legitimate trafic observations. Thus, accuracy_score would be inaccurate metric to evaluate the performance of the classifiers.

That's why I trained the models based on f_beta score which is used in these cases. The most appropriate model's are these with the highest f_beta score and then accuracy score using the test set.

As far as plots are concerned, the first plot shows the training performance in terms of f_beta score and the second the performance using the test dataset.

Example:

LR
==============================
Results on training set:
fbeta_score 0.9790819291109819
accuracy_score 0.976063829787234
Results on test set:
fbeta_score 0.9538357094365241
accuracy_score 0.9473684210526315

plot_1 
plot_2

